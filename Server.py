from flask import Flask, render_template, request
import flask
import os
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route("/submit", methods=["POST"])
def submit():
    #return "WAIT WUT", request.form["serverVisualisation"])
    with open("sample_server.txt", "w") as f:
        f.write(request.form['serverVisualisation'])

    os.system("python3 visualise.py")

    return "<img src='../result.png'>"


@app.route("/<path:path>")
def staticHost(path):
    return flask.send_from_directory("", path)


if __name__ == '__main__':
    app.run()
