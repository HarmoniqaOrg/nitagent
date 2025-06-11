# NitAgent

This repository contains an AI-powered agent for scraping contact information of Belgian AISBL organizations.

## Usage

1. Prepare a CSV file with a column `organization_name` listing the AISBL names.
2. Install requirements with `pip install -r requirements.txt`.
3. Run `python -m aisbl_agent <input.csv> <output.csv>`.

The script uses OpenAI's API and heuristics to locate official websites and extract contact details.

## Web interface

To try the agent in your browser, run the built-in Flask app:

```bash
python -m aisbl_agent.webapp
```

Then open [http://localhost:5000](http://localhost:5000) and upload your CSV.
The results will be shown in a table with a link to download them as a CSV file.
