from flask import Flask, render_template, request
import flask
import os
import uuid
app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route("/submit", methods=["POST"])
def submit():

    unique_id = uuid.uuid4()
    file_name = "%s.txt" % unique_id
    with open(file_name, "w") as f:
        f.write(request.form['serverVisualisation'])

    os.system("python3 visualise.py %s" % file_name)

    return "<img src='../%s.png'>" % unique_id


@app.route("/<path:path>")
def staticHost(path):
    return flask.send_from_directory("", path)


if __name__ == '__main__':
    app.run()
