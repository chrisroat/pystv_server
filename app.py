import io
import json
import os

import plotly
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
def index():
    form = UploadForm()

    if request.method == "POST":
        file_storage = form.results_csv.data
        filename = file_storage.filename

        buffer = io.StringIO(
            file_storage.read().decode("latin-1"),
            newline=None,
        )
        races = pystv.parse_google_form_csv(buffer)
        data = []
        for race in races:
            result = pystv.run_stv(race)
            names = result.metadata.names
            
            # -1 because the elected indexing starts from 1.
            winners = [names[e-1] for r in result.rounds for e in r.elected]

            df_nodes, df_links = pystv.result_to_sankey_data(result)
            fig = pystv.create_sankey_fig(df_nodes, df_links)
            fig = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

            data.append(
                {"metadata": result.metadata, "winners": winners, "figure": fig}
            )

        return render_template("results.html", filename=filename, data=data)

    return render_template("index.html", form=form)


@app.route("/instructions", methods=["GET"])
def instructions():
    return render_template("instructions.html")
