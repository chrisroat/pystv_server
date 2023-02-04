import csv
import io
import os

import pystv
from flask import Flask, render_template, request
from flask.helpers import send_from_directory
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]


@app.route("/static/<path:path>")
def send_static(path):
    return send_from_directory("static", path)


class UploadForm(FlaskForm):
    results_csv = FileField(
        "Election Results CSV File",
        validators=[FileRequired(), FileAllowed(["csv"], "CSV Files only!")],
    )


@app.route("/", methods=["GET", "POST"])
def upload():
    form = UploadForm()

    if request.method == "POST":
        file_storage = form.results_csv.data
        filename = file_storage.filename

        results_txt = io.StringIO(
            file_storage.read().decode("latin-1"),
            newline=None,
        )
        reader = csv.reader(results_txt)
        rows = [row for row in reader]
        races = pystv.parse_rows(rows)
        sankey_figs = []
        for race in races:
            results = pystv.run_stv(race)
            sankey_data = pystv.results_to_sankey_data(results)
            fig = pystv.create_sankey_fig(sankey_data)
            sankey_figs.append(fig)

        return render_template(
            "results.html", filename=filename, sankey_figs=sankey_figs
        )

    return render_template("index.html", form=form)


@app.route("/instructions", methods=["GET"])
def instructions():
    return render_template("instructions.html")
