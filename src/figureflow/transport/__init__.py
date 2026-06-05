"""Transport seam — one renderer, three interchangeable pipes.

The renderer never knows which pipe it sits on. ``base.Transport`` is the
contract; concrete adapters fill it iteration by iteration:

- ``anywidget_adapter.AnywidgetAdapter`` — notebook, kernel round-trip (ITER_V2_01).
- ``static_export.StaticExportAdapter`` — frozen offline snapshot (ITER_V2_02).
- ``server_adapter.ServerAdapter`` — plain browser, stdlib SSE+POST (ITER_V2_03).

See SKELETON_V2 §02, §04.
"""

from __future__ import annotations

from figureflow.transport.base import Transport

__all__ = ["Transport"]
