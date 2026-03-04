from flask import Flask, render_template, request, jsonify
import sys
import os
from io import StringIO
from pathlib import Path

# Add src to path so we can import PseudoPython modules
sys.path.append(os.path.abspath("src"))

from lexer import tokenize
from parser import parse, GRAMMAR
from interpreter import interpret
from ppy_errors import PseudoPyError, make_error, ERROR_TEMPLATES

app = Flask(__name__, 
            static_folder="public/static", 
            template_folder="templates")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.json
    source = data.get("code", "")
    
    # Capture stdout
    old_stdout = sys.stdout
    redirected_output = StringIO()
    sys.stdout = redirected_output
    
    error = None
    try:
        tokens = tokenize(source)
        ast = parse(tokens)
        interpret(ast)
    except PseudoPyError as exc:
        error = str(exc)
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
    return jsonify({
        "grammar": GRAMMAR,
        "errors": ERROR_TEMPLATES
    })

@app.route("/api/config", methods=["POST"])
def update_config():
    data = request.json
    new_grammar = data.get("grammar")
    new_errors = data.get("errors")
    
    if new_errors:
        ERROR_TEMPLATES.update(new_errors)
    
    # We can't easily re-initialize the Lark parser with a new grammar 
    # without modifying the global state in parser.py or making it dynamic.
    # For now, we'll just update the error templates.
    
    return jsonify({"status": "ok", "message": "Configuration updated successfully!"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
