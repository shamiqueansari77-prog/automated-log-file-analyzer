# Automated Log File Analyzer

A modern, responsive Flask web application designed for automated system log analysis, anomaly detection, rule-based system health calculation, and report generation.

This project is built from scratch as an academic mini-project for Computer Science & Engineering (CSE) and Artificial Intelligence & Machine Learning (AIML) curriculums. It demonstrates core principles of server-side text parsing, pattern normalization, web security, and automated report synthesis without relying on heavyweight machine learning dependencies or complex databases.

---

## Overview

Modern server environments, web services, and cloud platforms produce massive amounts of diagnostic log output daily. Identifying recurring errors, severe outages, and capacity warnings manually from raw text files is tedious and prone to human error.

**Automated Log File Analyzer** provides a browser-based developer dashboard where administrators, engineers, and students can upload standard `.log` or `.txt` log files, immediately view key health and severity metrics, detect repeated recurring faults, and export structured analysis reports for record-keeping and troubleshooting.

---

## Key Features

- **Web-First Architecture**: Built entirely as a web application with zero terminal prompts or `input()` calls. Fully compatible with production WSGI servers like Gunicorn.
- **Multi-Level Severity Detection**: Automatically identifies `INFO`, `WARNING` (including `WARN`), `ERROR`, `CRITICAL` (including `FATAL`), and `DEBUG` levels case-insensitively across diverse log line formats.
- **Rule-Based System Health Engine**: Calculates overall system status (`Healthy`, `Warning`, `Needs Attention`, `High Risk`, `Critical`) using deterministic logic with human-readable explanations.
- **Repeated Issue Detection**: Normalizes log messages by stripping changing timestamps, process tags, and prefixes to group and count identical recurring problems.
- **Important Issues Summary**: Highlights unique critical errors and high-frequency warnings without flooding the UI with redundant entries.
- **Interactive Log Browser**: Browse and inspect parsed log entries with real-time text search and severity filters.
- **Automated Plain-Text Report Export**: Generates a downloadable, timestamped `.txt` report containing metrics, health status, and top anomalies.
- **Secure File Handling**: Enforces file format validation (`.log`, `.txt`), a 5 MB upload ceiling, filename sanitization via `secure_filename`, and UUID-based collision avoidance.
- **Responsive Dark Theme UI**: Tailored developer-dashboard interface that adapts smoothly to 1920px desktops, 768px tablets, and 360px mobile screens without page-level horizontal overflow.

---

## Technology Stack

- **Backend**: Python 3, Flask
- **Frontend**: HTML5, CSS3 (CSS Grid & Flexbox), Vanilla JavaScript
- **Production WSGI Server**: Gunicorn
- **Deployment Platform**: Render
- **Version Control**: Git / GitHub

---

## Project Structure

```text
Automated_Log_File_Analyzer/
│
├── app.py                  # Main Flask application, routes, upload handling, error handling
├── analyzer.py             # Pure Python parsing engine, severity detection, health logic
├── requirements.txt        # Production dependencies (Flask, Gunicorn, Werkzeug)
├── README.md               # Complete project documentation and deployment guide
├── .gitignore              # Ignores bytecode, venv, and runtime uploads/reports
├── sample.log              # Realistic 35+ line sample log file for testing
│
├── templates/
│   └── index.html          # Responsive developer dashboard template
│
├── static/
│   └── style.css           # Modern dark-theme stylesheet
│
├── uploads/
│   └── .gitkeep            # Upload directory preserved in git
│
└── reports/
    └── .gitkeep            # Reports directory preserved in git
```

---

## How It Works

1. **File Upload & Sanitization (`app.py`)**:
   - The user selects or drags a `.log` or `.txt` file into the upload zone.
   - Flask validates the file extension and ensures the payload does not exceed 5 MB (`MAX_CONTENT_LENGTH`).
   - `secure_filename` strips potentially malicious path traversal elements, and a UUID is prefixed before saving to `uploads/`.

2. **Parsing & Classification (`analyzer.py`)**:
   - The log file is read using UTF-8 (with automatic fallback to Latin-1).
   - `detect_severity()` scans each line with regular expressions to classify its log level.
   - `normalize_message()` removes variable timestamps and prefixes to identify the underlying message signature.

3. **Metric Aggregation & Rule-Based Health Evaluation**:
   - The analyzer computes total line counts and frequency counts for each severity level.
   - System Health is evaluated deterministically:
     - **Critical**: One or more `CRITICAL` events detected.
     - **High Risk**: $\ge 10$ `ERROR` events or errors represent $\ge 20\%$ of detected logs.
     - **Needs Attention**: One or more `ERROR` events detected.
     - **Warning**: One or more `WARNING` events detected without errors.
     - **Healthy**: Zero warnings, errors, or critical events.

4. **Report Synthesis & Delivery**:
   - An analysis summary is formatted into plain text and stored under `reports/<report_id>.txt`.
   - The user can download this report via `/download-report/<report_id>`.

---

## Running Locally

Follow these step-by-step instructions to run the application on your computer.

### Prerequisites
- Python 3.9 or newer installed on your machine.
- Git installed (optional, for cloning).

### 1. Set Up Virtual Environment

Open your terminal or command prompt inside the project folder:

```bash
python -m venv venv
```

Activate the virtual environment:

- **Windows (Command Prompt / PowerShell)**:
  ```powershell
  venv\Scripts\activate
  ```
- **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Flask Web Application

```bash
python app.py
```

### 4. Access the Dashboard

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## Using the Application

1. Open `http://127.0.0.1:5000` in your browser.
2. Drag and drop the included `sample.log` (or your own server log) onto the upload box, or click **browse file**.
3. Click the blue **Analyze Log** button.
4. Review the generated dashboard:
   - **Severity Cards**: Total logs, INFO, WARNING, ERROR, CRITICAL, and DEBUG tallies.
   - **System Health**: Health status pill with detailed rule-based justification.
   - **Important Issues**: Prioritized view of critical events and high-frequency errors.
   - **Repeated Issues**: Messages that occurred multiple times with occurrence counts.
   - **Log Details**: Searchable, filterable table of log entries.
5. Click **EXPORT REPORT** in the top action bar to download the structured text report.

---

## GitHub Deployment

To upload this project to your GitHub account:

### Step 1: Initialize Git and Commit
```bash
git init
git add .
git commit -m "Initial commit: Automated Log File Analyzer"
git branch -M main
```

### Step 2: Link Remote Repository and Push
```bash
git remote add origin YOUR_GITHUB_REPOSITORY_URL
git push -u origin main
```
*(Replace `YOUR_GITHUB_REPOSITORY_URL` with your actual repository link from GitHub, e.g., `https://github.com/username/Automated_Log_File_Analyzer.git`)*

### Future Code Updates
Whenever you make updates to the code, push them using:
```bash
git add .
git commit -m "Update project"
git push
```

---

## Deploying to Render

This application is pre-configured for seamless cloud deployment on [Render](https://render.com).

### Step-by-Step Render Setup:
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository (`Automated_Log_File_Analyzer`).
4. Configure the Web Service settings exactly as follows:
   - **Name**: `automated-log-file-analyzer` (or your choice)
   - **Language / Environment**: `Python`
   - **Branch**: `main`
   - **Region**: Choose the closest region (e.g., Singapore, Frankfurt, Oregon)
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     gunicorn app:app
     ```
   - **Plan**: `Free`
5. Click **Deploy Web Service**.

Render will install packages from `requirements.txt`, launch Gunicorn with `app:app`, and provide you with a live public URL (e.g., `https://automated-log-file-analyzer.onrender.com`).

---

## Viva & Presentation Tips for Students

- **Q: Why is there no `input()` function in the code?**
  *A: Web applications are driven by HTTP requests and browser forms, not terminal consoles. Using `input()` in web frameworks like Flask halts the server worker waiting for non-existent terminal stdin, which causes `EOFError` during cloud deployment.*

- **Q: How does Gunicorn start the application?**
  *A: Gunicorn runs `gunicorn app:app`, which imports the Python module `app.py` and locates the top-level `app = Flask(__name__)` object to bind it to worker threads.*

- **Q: Does this project use Artificial Intelligence?**
  *A: No. It uses deterministic, rule-based text analysis, regex pattern extraction, and statistical thresholds. This ensures full transparency, predictable behavior, and zero latency overhead.*

---

## Future Improvements

- Add export support for PDF and CSV report formats.
- Implement time-window filtering (e.g., view only logs between 08:00 and 09:00).
- Add support for compressed archive log formats (`.gz`, `.zip`).
- Implement basic keyword alerting thresholds.
