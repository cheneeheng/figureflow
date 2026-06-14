FROM ubuntu:24.04

# =============================================================================
# OS SETUP
# =============================================================================

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Berlin

# Install sudo and other essentials
RUN apt-get update && apt-get install -y \
    sudo \
    curl \
    git \
    nano \
    wget \
    unzip \
    gnupg2 \
    python3 \
    python3-pip \
    python3-venv \
    jq

RUN mkdir -p -m 755 /etc/apt/keyrings \
	&& out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
	&& cat $out | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
	&& chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
	&& mkdir -p -m 755 /etc/apt/sources.list.d \
	&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
	&& apt-get update \
	&& apt-get install gh -y

RUN rm -rf /var/lib/apt/lists/*

# # Create a new user 'vscode' with sudo privileges
# RUN useradd -m vscode \
#     && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/vscode 
RUN echo "ubuntu ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/ubuntu

# Create /figureflow directory and set permissions
RUN mkdir /figureflow \
    && chown ubuntu:ubuntu /figureflow \
    && chmod 755 /figureflow

# Set user
USER ubuntu
ENV HOME_DIR=/home/ubuntu

# Set working directory
WORKDIR /figureflow

# =============================================================================
# NODE JS
# =============================================================================

# Install Node.js + npm + bun
ENV NVM_DIR=$HOME_DIR/nvm
RUN mkdir $NVM_DIR \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash \
    && \. "$NVM_DIR/nvm.sh" \
    && nvm install 24 \
    && npm install -g bun \
    && echo 'source $NVM_DIR/nvm.sh' >> $HOME_DIR/.bashrc

# =============================================================================
# PYTHON
# =============================================================================

# Install uv - a fast Python package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/ubuntu/.local/bin:${PATH}"

# Python venv setup
RUN uv python install 3.12.13
RUN uv venv --prompt .venv .venv
RUN uv python pin 3.12

# Python cache
ENV PYTHONPYCACHEPREFIX=/tmp/pycache

# =============================================================================
# CLAUDE CODE
# =============================================================================

RUN curl -fsSL https://claude.ai/install.sh | bash

# =============================================================================
# PRE STARTUP
# =============================================================================
