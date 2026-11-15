# SPDX-License-Identifier: Apache-2.0 OR MIT
#
# Rendered by `make demo` (vhs, https://github.com/charmbracelet/vhs) from
# the repository root, against a crypto-server already listening on
# 127.0.0.1:3106 with CRYPTO_SERVICE_URL and CRYPTO_SERVICE_API_KEY set
# in the environment (see CONTRIBUTING.md). On screen: three digests of
# the same text with the blocking client, then an Ed25519 signature made
# with a server-held key, checked, and refused for a changed message.
# Nothing leaves loopback.
Output .github/demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 560
Set Padding 20
Set Theme "Catppuccin Mocha"
Set WaitTimeout 60s
Set WaitPattern /^\$ ?$/

Hide
Type `export PS1='$ ' && uv sync --frozen -q && clear`
Enter
Sleep 2s
Show

Type "uv run python examples/hash.py 'hello, crypto-server'"
Sleep 500ms
Enter
Wait
Sleep 4s

Type "uv run python examples/ed25519_sign_verify.py"
Sleep 500ms
Enter
Wait
Sleep 8s
