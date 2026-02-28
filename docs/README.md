# PseudoPy Online Interpreter

This directory contains the web interface for running PseudoPy code in your browser.

## How it works

- **index.html** - The main web interface for the PseudoPy interpreter
- Uses [Pyodide](https://pyodide.org/) to run Python in the browser
- No server required - everything runs client-side!

## Enable GitHub Pages

1. Go to your repository settings on GitHub
2. Scroll to **"Pages"** section
3. Under **"Source"**, select:
   - Branch: `main`
   - Folder: `/docs`
4. Click **Save**

Your site will be live at: `https://stefanm03-sys.github.io/pseudopy/`

## Features

- 📝 Code editor with syntax highlighting
- ▶️ Run button to execute code
- 📤 Real-time output display
- 🎨 Modern, responsive interface
- ⌨️ Keyboard shortcut: `Ctrl+Enter` to run code

## Current Limitations

- Uses Python runtime (Pyodide), not the native PseudoPy interpreter
- For full functionality, you'd need to port your interpreter to JavaScript or create a backend API

## Future Improvements

- Integrate your custom PseudoPy interpreter logic
- Add syntax highlighting for `.ppy` files
- Support for file uploads
- Dark mode
