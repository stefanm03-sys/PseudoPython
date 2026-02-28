# PseudoPy VS Code Language Extension (Local)

This folder contains a minimal VS Code language extension that adds syntax highlighting for `.ppy` files.

## Use it immediately (without packaging)

1. Open this folder in VS Code.
2. Press `F5` to launch an Extension Development Host.
3. In the new window, open any `.ppy` file.

## Install as VSIX (optional)

1. Install `vsce` once: `npm i -g @vscode/vsce`
2. From `vscode-pseudopy/`, run: `vsce package`
3. In VS Code: Extensions -> `...` -> `Install from VSIX...`

## Keyword color

A workspace color customization is in `.vscode/settings.json`:

- `keyword.control.pseudopy` is set to orange (`#FF6B35`) and bold.

Adjust that color anytime in `.vscode/settings.json`.
