"""Server adapter — plain browser, live bidirectional sync (MVP terminator).

A dependency-free stdlib ``ThreadingHTTPServer`` bound to localhost: SSE
(``GET /events``) carries Python→browser pushes, ``POST /change`` carries
browser→Python edits. The session (server object, daemon thread, connected SSE
streams) is transient infrastructure, not model state. Concurrency is guarded by
the single ``synccore.LOCK``; the echo loop is handled by reusing
``synccore.is_echo`` rather than inventing server-specific logic (SKELETON_V2 §04,
ITER_V2_03).
"""

from __future__ import annotations

import json
import queue
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from figureflow import synccore
from figureflow.transport.base import ChangeHandler, Transport
from figureflow.transport.static_export import _STATIC, render_host_page

if TYPE_CHECKING:
    from figureflow import Flow

# Top-level await is valid in a module script: fetch the initial snapshot so the
# server adapter can answer getState() synchronously when the renderer mounts.
_SERVER_BOOTSTRAP = """
const initial = await (await fetch("/state")).json();
const transport = globalThis.figureflow.createServerTransport(initial);
globalThis.figureflow.mount(
  document.getElementById("figureflow-root"),
  transport,
  { height: initial.height }
);
""".strip()


class ServerAdapter(Transport):
    """Serves a ``Flow`` over a localhost stdlib SSE+POST HTTP server."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 0,
        *,
        open_browser: bool = True,
        block: bool = False,
    ) -> None:
        self._host = host
        self._port = port
        self._open_browser = open_browser
        self._block = block
        self._flow: Optional["Flow"] = None
        self._handler: Optional[ChangeHandler] = None
        # Connected SSE streams as message queues, guarded by their own lock.
        self._streams: set[queue.Queue[Optional[str]]] = set()
        self._streams_lock = threading.Lock()
        self._last_from_client: Optional[synccore.State] = None
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._url = ""
        self._observers: List[tuple[Callable[[Any], None], List[str]]] = []

    # ── Transport contract ──────────────────────────────────────────────────

    def bind(self, flow: "Flow") -> None:
        """Attach to the canonical ``Flow`` the server reads/mutates."""
        self._flow = flow

    def send_state(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        meta: Dict[str, Any],
    ) -> None:
        """Push canonical state down by broadcasting an SSE ``state`` message."""
        self._broadcast({"kind": "state", "nodes": nodes, "edges": edges})

    def on_change(self, handler: ChangeHandler) -> None:
        """Register an optional listener for committed edits.

        The HTTP ``POST /change`` path is the commit funnel (it writes the traits
        under the lock); this handler, if set, additionally observes each commit.
        """
        self._handler = handler

    def emit(self, event: str, payload: Any) -> None:
        """Send a custom message down by broadcasting an SSE ``event`` message."""
        self._broadcast({"kind": "event", "name": event, "payload": payload})

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def start(self) -> None:
        """Bind the server and run ``serve_forever`` on a daemon thread.

        ``ThreadingHTTPServer`` (not ``HTTPServer``) so the never-ending SSE
        stream lives on its own thread while ``/change`` POSTs land on others. A
        ``port`` of ``0`` lets the OS pick a free port, surfaced on :attr:`url`.
        """
        flow = self._require_flow()
        httpd = ThreadingHTTPServer((self._host, self._port), _Handler)
        httpd.daemon_threads = True
        # Hand the adapter to request handlers via the server instance.
        httpd.adapter = self  # type: ignore[attr-defined]
        self._httpd = httpd
        self._url = f"http://{self._host}:{httpd.server_address[1]}"

        def _on_state(_change: Any) -> None:
            # Reentrancy: this observer fires synchronously inside handle_change
            # while synccore.LOCK is held, so it must NOT re-acquire it. is_echo
            # drops the origin client's own edit; Python-side edits broadcast.
            current: synccore.State = {
                "nodes": list(flow.nodes),
                "edges": list(flow.edges),
            }
            if synccore.is_echo(current, self._last_from_client):
                return
            self.send_state(current["nodes"], current["edges"], {})

        def _on_layout(_change: Any) -> None:
            req = flow._layout_request
            if req and req.get("nonce"):
                self._broadcast({"kind": "event", "name": "layout", "payload": req})

        flow.observe(_on_state, names=["nodes", "edges"])
        flow.observe(_on_layout, names=["_layout_request"])
        self._observers = [
            (_on_state, ["nodes", "edges"]),
            (_on_layout, ["_layout_request"]),
        ]

        self._thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        self._thread.start()
        print(f"figureflow serving at {self._url}")
        if self._open_browser:
            webbrowser.open(self._url)
        if self._block:
            try:
                self._thread.join()
            except KeyboardInterrupt:
                self.stop()

    def stop(self) -> None:
        """Shut the server down, detach observers, and close open SSE streams."""
        if self._httpd is None:
            return
        for fn, names in self._observers:
            try:
                self._require_flow().unobserve(fn, names=names)
            except ValueError:
                pass
        self._observers = []
        # Unblock every SSE handler thread waiting on its queue.
        with self._streams_lock:
            streams = list(self._streams)
            self._streams.clear()
        for q in streams:
            q.put(None)
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._httpd = None
        self._thread = None

    @property
    def url(self) -> str:
        """The served URL (valid after :meth:`start`)."""
        return self._url

    # ── HTTP-facing helpers (called from the request handler) ───────────────

    def host_page(self) -> str:
        """The ``GET /`` page: the shared host template, linked at the live endpoints."""
        return render_host_page(
            title="figureflow",
            head='<link rel="stylesheet" href="/widget.css" />',
            island="",
            bundle='<script type="module" src="/widget.js"></script>',
            bootstrap=f'<script type="module">{_SERVER_BOOTSTRAP}</script>',
        )

    def state_json(self) -> str:
        """The ``GET /state`` body: the initial ``to_json`` snapshot."""
        from figureflow.serialize import to_json

        with synccore.LOCK:
            return to_json(self._require_flow())

    def handle_change(self, patch: Dict[str, Any]) -> None:
        """Apply a ``POST /change`` body to the canonical ``Flow``.

        A ``{"op": "event", ...}`` body is a custom-component event routed to the
        v1 ``on()`` handlers. Otherwise the patch carries full ``nodes``/``edges``
        arrays: they are written under the lock as a single batched notification,
        and the resulting push is dropped as an echo so it is not re-sent to the
        origin client.
        """
        if patch.get("op") == "event":
            self._dispatch_event(patch.get("name"), patch.get("payload"))
            return
        flow = self._require_flow()
        with synccore.LOCK:
            expected: synccore.State = {
                "nodes": patch["nodes"] if patch.get("nodes") is not None else list(flow.nodes),
                "edges": patch["edges"] if patch.get("edges") is not None else list(flow.edges),
            }
            self._last_from_client = expected
            # Batch so observers see the final state once (no intermediate push).
            with flow.hold_trait_notifications():
                if patch.get("nodes") is not None:
                    flow.nodes = patch["nodes"]
                if patch.get("edges") is not None:
                    flow.edges = patch["edges"]
        if self._handler is not None:
            self._handler(expected)

    def register_stream(self) -> "queue.Queue[Optional[str]]":
        """Register a new SSE stream; returns its message queue."""
        q: "queue.Queue[Optional[str]]" = queue.Queue()
        with self._streams_lock:
            self._streams.add(q)
        return q

    def unregister_stream(self, q: "queue.Queue[Optional[str]]") -> None:
        """Drop a disconnected SSE stream."""
        with self._streams_lock:
            self._streams.discard(q)

    def _broadcast(self, message: Dict[str, Any]) -> None:
        data = json.dumps(message)
        with self._streams_lock:
            streams = list(self._streams)
        for q in streams:
            q.put(data)

    def _dispatch_event(self, event: Optional[str], payload: Any) -> None:
        handlers = self._require_flow()._handlers.get(event or "", [])
        for cb in list(handlers):
            cb(payload)

    def _require_flow(self) -> "Flow":
        if self._flow is None:
            raise RuntimeError("ServerAdapter used before bind()")
        return self._flow


_ASSET_MIME = {"widget.js": "text/javascript", "widget.css": "text/css"}


class _Handler(BaseHTTPRequestHandler):
    """Routes for the SSE+POST server; one instance per request thread."""

    # Silence the default stderr request logging (noisy in notebooks/REPLs).
    def log_message(self, *args: Any) -> None:  # noqa: D401
        return None

    @property
    def _adapter(self) -> ServerAdapter:
        return self.server.adapter  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._send_bytes(
                200, "text/html; charset=utf-8", self._adapter.host_page().encode("utf-8")
            )
        elif path in ("/widget.js", "/widget.css"):
            name = path.lstrip("/")
            self._send_bytes(200, _ASSET_MIME[name], (_STATIC / name).read_bytes())
        elif path == "/state":
            self._send_bytes(
                200, "application/json", self._adapter.state_json().encode("utf-8")
            )
        elif path == "/events":
            self._serve_events()
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/change":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            patch = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self.send_error(400)
            return
        self._adapter.handle_change(patch)
        self.send_response(204)
        self.end_headers()

    def _serve_events(self) -> None:
        q = self._adapter.register_stream()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        try:
            while True:
                try:
                    msg = q.get(timeout=15)
                except queue.Empty:
                    # Keepalive comment so proxies/clients hold the connection.
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    continue
                if msg is None:  # shutdown sentinel
                    break
                self.wfile.write(f"data: {msg}\n\n".encode("utf-8"))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self._adapter.unregister_stream(q)

    def _send_bytes(self, code: int, mime: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
