ARG DEBIAN_VERSION=bookworm
ARG UV_VERSION=0.5.9
ARG PYTHON_VERSION=3.13

FROM ghcr.io/astral-sh/uv:$UV_VERSION AS uv

FROM mcr.microsoft.com/vscode/devcontainers/base:$DEBIAN_VERSION

# install mcfly as root
RUN curl -LSfs https://raw.githubusercontent.com/cantino/mcfly/master/ci/install.sh | sh -s -- --git cantino/mcfly 

USER vscode

# Install and configure starship.rs prompt
RUN curl -fsSL https://starship.rs/install.sh | sh -s -- --yes
RUN echo "eval \"\$(starship init bash)\"" >> ~/.bashrc && echo "eval \"\$(starship init zsh)\"" >> ~/.zshrc

# install mcfly config
RUN echo 'eval "$(mcfly init zsh)"' >> ~/.zshrc \
    && touch ~/.zsh_history

# Install UV/Python
COPY --from=uv --chown=vscode: /uv /uvx /bin/
RUN uv python install $PYTHON_VERSION

# Install foundry
RUN curl -L https://foundry.paradigm.xyz | bash
RUN /home/vscode/.foundry/bin/foundryup
