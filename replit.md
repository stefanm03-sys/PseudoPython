# PseudoPython IDE

This is a web-based IDE for PseudoPython, allowing users to edit code, run it in a pre-built environment, and configure syntax/error messages.

## Project Structure

- `src/`: Core PseudoPython interpreter logic.
- `app.py`: Flask backend serving the IDE and API.
- `templates/`: HTML templates for the frontend.
- `public/static/`: CSS and JS assets for the frontend.

## Getting Started

1. The application runs via the "Web IDE" workflow.
2. Open the web preview to access the IDE.
3. Use the "Run Code" button to execute PseudoPy code.
4. Use "Configure Syntax/Errors" to modify the environment.

## Connect This Repl to GitHub

Use the repository URL (not the `/tree/main` page):

```bash
https://github.com/stefanm03-sys/PseudoPython.git
```

From the Replit shell, run:

```bash
git init
git branch -M main
git remote add origin https://github.com/stefanm03-sys/PseudoPython.git
git add .
git commit -m "Initial commit from Replit"
git push -u origin main
```

If git is already initialized, update the remote instead:

```bash
git remote -v
git remote set-url origin https://github.com/stefanm03-sys/PseudoPython.git
git push -u origin main
```

## Recommended Branch Workflow (Replit Branch -> main)

If you are working on a Replit branch (for example `replit`), commit there first and then open a pull request into `main`:

```bash
git checkout replit
git add .
git commit -m "Describe your change"
git push -u origin replit
```

Then create a pull request on GitHub from `replit` to `main`.
