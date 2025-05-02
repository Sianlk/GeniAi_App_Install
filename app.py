from flask import Flask
from genesis_engine import GenesisEngine

app = Flask(__name__)
engine = GenesisEngine()

@app.route("/")
def home():
    return "GenesisOS API Online"

if __name__ == "__main__":
    app.run(debug=True)
