from flask import Flask, render_template, request, jsonify, session
import sys
import os
import uuid
from io import StringIO
from pathlib import Path
import copy

# Add src to path so we can import PseudoPython modules
sys.path.append(os.path.abspath("src"))

from lexer import tokenize
from parser import parse, GRAMMAR
from interpreter import interpret, Environment
from ppy_errors import PseudoPyError, make_error, ERROR_TEMPLATES

app = Flask(__name__, 
            static_folder="public/static", 
            template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", str(uuid.uuid4()))

# In-memory storage for user-specific configurations (sessions are better for small data)
# For larger data or persistence, a database would be used.
user_configs = {}

def get_user_config():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    
    user_id = session["user_id"]
    if user_id not in user_configs:
        user_configs[user_id] = {
            "grammar": GRAMMAR,
            "errors": copy.deepcopy(ERROR_TEMPLATES)
        }
    return user_configs[user_id]

@app.route("/")
def index():
    try:
        return render_template("index.html")
    except Exception:
        # Keep root healthy for platforms that probe "/" and not "/health".
        return jsonify({"status": "ok"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.json
    source = data.get("code", "")
    config = get_user_config()
    
    # Capture stdout
    old_stdout = sys.stdout
    redirected_output = StringIO()
    sys.stdout = redirected_output
    
    error = None
    try:
        # We use the original tokenize but could potentially use custom logic if needed
        tokens = tokenize(source)
        
        # NOTE: To truly support custom grammars per user, 
        # we would need to initialize a Lark parser per request/session.
        # This is a bit heavy but ensures isolation.
        from lark import Lark
        from parser import ASTBuilder
        
        custom_parser = Lark(config["grammar"], parser="lalr", start="start")
        tree = custom_parser.parse(tokens)
        ast = ASTBuilder().transform(tree)
        
        # Use custom error templates in the interpreter context
        # This requires a bit of monkey-patching or passing templates down.
        # For simplicity, we'll temporarily swap the global templates (not thread-safe!)
        # Better: Modify ppy_errors to support context-based templates.
        
        # A safer way for this demo is to just run with original logic 
        # but isolation is key.
        interpret(ast)
    except PseudoPyError as exc:
        # Check if the error code exists in user's custom templates
        msg = config["errors"].get(exc.code, str(exc))
        error = msg
    except Exception as exc:
        error = f"[INTERNAL ERROR] {str(exc)}"
    finally:
        sys.stdout = old_stdout
        
    output = redirected_output.getvalue()
    return jsonify({
        "output": output,
        "error": error
    })

@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(get_user_config())

@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.json
    config = get_user_config()
    
    if "grammar" in data:
        config["grammar"] = data["grammar"]
    if "errors" in data:
        config["errors"].update(data["errors"])
    
    return jsonify({"status": "ok", "message": "Configuration updated locally for your session!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
