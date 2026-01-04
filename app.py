from flask import Flask, render_template, redirect, url_for, request

app = Flask(__name__)
app.config['SECRET_KEY'] = "demo-only-not-secure"

# -----------------------------
# Pages
# -----------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/imgcrypt")
def imgcrypt():
    return render_template("imgcrypt.html")

@app.route("/textcrypt")
def textcrypt():
    return render_template("textcrypt.html")

@app.route("/about")
def about():
    return render_template("about.html")

# -----------------------------
# External Navigation (Showcase)
# -----------------------------

@app.route("/go/github")
def go_github():
    return redirect("https://github.com/shubhamos-ai")

@app.route("/go/google")
def go_google():
    return redirect("https://google.com")

@app.route("/go/docs")
def go_docs():
    return redirect("https://flask.palletsprojects.com")

# -----------------------------
# Fake API (Demo Response)
# -----------------------------

@app.route("/api/demo", methods=["POST"])
def demo_api():
    return {
        "status": "success",
        "message": "This is a demo-only API. No real encryption happens.",
        "note": "Showpiece build"
    }

# -----------------------------
# Run Server
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
