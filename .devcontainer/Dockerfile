ARG VARIANT=3.9-bookworm
# requires rosetta 2 on apple chips
ARG PLATFORM=linux/amd64
FROM --platform=${PLATFORM} mcr.microsoft.com/devcontainers/python:${VARIANT}

# install mcfly as root
RUN curl -LSfs https://raw.githubusercontent.com/cantino/mcfly/master/ci/install.sh | sh -s -- --git cantino/mcfly 

USER vscode

# Install and configure starship.rs prompt
RUN curl -fsSL https://starship.rs/install.sh | sh -s -- --yes
RUN echo "eval \"\$(starship init bash)\"" >> ~/.bashrc && echo "eval \"\$(starship init zsh)\"" >> ~/.zshrc

# install mcfly config
RUN echo 'eval "$(mcfly init zsh)"' >> ~/.zshrc \
    && touch ~/.zsh_history

# Install foundry
RUN curl -L https://foundry.paradigm.xyz | bash
RUN /home/vscode/.foundry/bin/foundryup
