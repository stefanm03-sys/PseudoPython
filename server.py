import flask
from flask import Flask

@app.route("/")
def home():
  return "App Online!", 200

if __name__ ==  "__main__":
  import os
  port = int(os.environ.get("PORT", 3000))
  app.run(host="0.0.0.0", port=port)