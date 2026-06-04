#!/usr/bin/env bash
set -euo pipefail

echo "Configuring Git SSH signing..."

git config --local gpg.ssh.allowedSignersFile "$HOME/.ssh/allowed_signers"
git config --local user.signingkey "$HOME/.ssh/id_ed25519.pub"

echo "Git SSH signing configured."
