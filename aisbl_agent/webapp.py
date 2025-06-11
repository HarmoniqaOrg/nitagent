from flask import Flask, request, render_template_string
from io import StringIO
import csv
import base64
from dataclasses import asdict

from .scraper import process_rows, ContactInfo

app = Flask(__name__)

UPLOAD_FORM = """
<!doctype html>
<title>AISBL Scraper</title>
<h1>Upload CSV with organization names</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=input_csv>
  <input type=submit value="Process">
</form>
"""

RESULT_TEMPLATE = """
<!doctype html>
<title>AISBL Results</title>
<h1>Scraping Results</h1>
<table border=1>
  <tr>
    <th>Organization</th>
    <th>Website</th>
    <th>Emails</th>
    <th>Phones</th>
    <th>Personnel</th>
  </tr>
  {% for row in results %}
  <tr>
    <td>{{ row.organization_name }}</td>
    <td>{{ row.website or '' }}</td>
    <td>{{ ';'.join(row.emails or []) }}</td>
    <td>{{ ';'.join(row.phones or []) }}</td>
    <td>{{ row.personnel or '' }}</td>
  </tr>
  {% endfor %}
</table>
<p><a href="{{ csv_data_uri }}" download="results.csv">Download CSV</a></p>
<p><a href="/">Process another file</a></p>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("input_csv")
        if not file:
            return "No file uploaded", 400
        text = file.read().decode("utf-8")
        reader = csv.DictReader(StringIO(text))
        results = process_rows(reader)
        output = StringIO()
        fieldnames = [
            "organization_name",
            "website",
            "emails",
            "phones",
            "personnel",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for info in results:
            row = asdict(info)
            row["emails"] = ";".join(info.emails or [])
            row["phones"] = ";".join(info.phones or [])
            writer.writerow(row)
        csv_data = output.getvalue()
        b64 = base64.b64encode(csv_data.encode("utf-8")).decode("ascii")
        csv_data_uri = f"data:text/csv;base64,{b64}"
        return render_template_string(RESULT_TEMPLATE, results=results, csv_data_uri=csv_data_uri)
    return UPLOAD_FORM


if __name__ == "__main__":
    app.run(debug=True)
