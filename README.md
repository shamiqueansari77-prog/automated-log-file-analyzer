# Automated Log File Analyzer

A responsive Flask dashboard that turns system logs into message counts, severity summaries, repeated-error frequencies, and a downloadable text report.

## Features
- Upload `.log` or `.txt` files up to 5 MiB (5,242,880 bytes).
- Case-insensitive INFO, WARN/WARNING, ERROR and OTHER classification.
- Four summary cards, CSS distribution bars, most frequent error and sorted frequency table.
- UTF-8 validation, safe filenames, empty/binary/oversized file handling.
- Separate upload and report directories for each analysis.
- Responsive dark interface, filename feedback, reset and report download.

## Technology
Python, Flask, Jinja2, HTML5, CSS3, vanilla JavaScript and Gunicorn. No frontend frameworks or chart dependencies.

## Project structure
```text
automated-log-file-analyzer/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── Procfile
├── render.yaml
├── sample.log
├── templates/
│   └── index.html
├── static/
│   └── style.css
└── uploads/
    └── .gitkeep
```
Runtime files are created under `uploads/<random-analysis-id>/source/` and `uploads/<random-analysis-id>/report.txt`. These are excluded from Git.

## Requirements and installation
Python 3.12 recommended (tested with 3.12.14), pip, and Git for publishing. Gunicorn runs on Linux/macOS; use Flask locally on Windows.

Extract the project, open a terminal in its folder, and optionally create a virtual environment:
```bash
python -m venv .venv
```
Windows PowerShell activation: `.venv\Scripts\Activate.ps1`

macOS/Linux activation: `source .venv/bin/activate`

Install and run:
```bash
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000. Stop with Ctrl+C. Development mode enables debugging; never expose this server publicly.

Production command (Linux/macOS):
```bash
gunicorn app:app
```
Render supplies its port through the environment; Gunicorn supports that environment variable.

## How analysis works
1. Validate the extension, size and sanitized filename.
2. Save in a unique directory inside `uploads`.
3. Read UTF-8 (with optional BOM) line by line, ignoring blank lines.
4. Find the first standalone INFO, WARNING, WARN or ERROR token in each line, ignoring case. This also supports timestamps before the level. If several tokens occur, the first wins. No matching token means OTHER.
5. Map WARN to WARNING; INFO is low severity, WARNING is medium, ERROR is high. OTHER has unclassified severity.
6. Count the text after ERROR using `collections.Counter`. Leading separators are removed. Timestamps before the level are ignored; otherwise error text is grouped exactly, including case. Ties retain first-seen order.
7. Generate a separate `report.txt`, served as `log_analysis_report.txt`.

Reports use India Standard Time (IST). Reset opens the initial upload page; it does not immediately delete the previous report. Uploads older than 24 hours are cleaned on a subsequent upload. Render's ephemeral filesystem can also remove reports during restarts or deployments. Report links use random identifiers and should be treated as private bearer links. This simple application is intended for a single server instance; it does not provide accounts or shared storage across instances.

## Sample input
The supplied `sample.log` contains:
```text
INFO User logged in successfully
WARNING Disk space is low
ERROR Database connection failed
INFO File uploaded successfully
ERROR Database connection failed
WARNING High memory usage detected
INFO User logged out successfully
ERROR Invalid password attempt
INFO Application started
WARNING CPU usage is high
ERROR Database connection failed
ERROR Server timeout
INFO Backup completed successfully
WARNING Network speed is slow
ERROR Server timeout
```

## Sample output
| Metric | Result |
| --- | --- |
| Total Logs | 15 |
| INFO / Low | 5 |
| WARNING / Medium | 4 |
| ERROR / High | 6 |
| OTHER | 0 |
| Most frequent error | Database connection failed |
| Frequency | 3 |

The remaining errors are Server timeout (2) and Invalid password attempt (1).

## Simple viva explanation
Flask receives the file from an HTML form. Python reads each non-blank line. A regular expression finds the message level, and a dictionary counts the levels. Counter counts repeated error messages. Jinja displays the results in HTML. CSS draws the bars and adapts the layout to phones. A separate function writes the report, and Flask sends it as a download. `secure_filename` removes unsafe filename components; random directories prevent upload collisions. Uploaded content is never executed.

## GitHub setup and push
GitHub Repository:
https://github.com/shamiqueansari77-prog/automated-log-file-analyzer

Create this repository in the named GitHub account if it does not exist. Authenticate Git using GitHub CLI or your credential manager. Never place credentials in the project.

For a fresh local project:
```bash
git init
git add .
git status
git commit -m "Initial commit - Automated Log File Analyzer"
git branch -M main
git remote add origin https://github.com/shamiqueansari77-prog/automated-log-file-analyzer.git
git push -u origin main
```
If Git reports a missing author identity, set your name and your actual GitHub email before committing:
```bash
git config --global user.name "Shamique"
```
Run `git config --global user.email` followed by your real GitHub email in quotes. Do not use an invented email.

If origin already exists, use `git remote set-url origin https://github.com/shamiqueansari77-prog/automated-log-file-analyzer.git`. Verify using `git remote -v`. If the remote contains commits, fetch and inspect them, then integrate deliberately; never force-push over existing work.

## Render deployment
1. Sign in to Render and authorize access to the GitHub repository.
2. Create a Web Service from the repository and select branch `main`.
3. Select Python, build command `pip install -r requirements.txt`, and start command `gunicorn app:app`.
4. Select the free instance if available. Set `PYTHON_VERSION` to `3.12.14` to match the tested runtime. The included `render.yaml` defines these settings for a Blueprint deployment.
5. Deploy and review build and runtime logs. Copy the actual public URL shown by Render.
6. At that URL, test the sample upload, expected counts, CSS, report download and Reset on desktop and mobile.
7. Update the Live App section with the verified URL, commit with `git commit -am "Add live application link"`, then `git push`.

Reference: https://render.com/docs/deploy-flask

## Live App
Add Render URL after deployment.

Deployment is not complete until a real public URL has been tested. No live address is assumed.
