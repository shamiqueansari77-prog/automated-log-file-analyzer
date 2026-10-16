"""
app.py - Main Flask Web Application
Automated Log File Analyzer (CSE/AIML Academic Mini-Project)

Production command for Render:
    gunicorn app:app

Local development command:
    python app.py
"""

import os
import re
import uuid
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    abort
)
from werkzeug.utils import secure_filename
import analyzer

# Module-level Flask application instance (Required by Gunicorn)
app = Flask(__name__)

# Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "log-analyzer-academic-key-2026")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit

# Safe runtime directories using absolute paths based on this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
REPORTS_FOLDER = os.path.join(BASE_DIR, "reports")

# Ensure required directories exist at runtime (safe for temporary filesystems like Render)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["REPORTS_FOLDER"] = REPORTS_FOLDER

ALLOWED_EXTENSIONS = {".log", ".txt"}


def allowed_file(filename):
    """
    Validates whether the uploaded file has an allowed extension (.log, .txt).
    """
    if not filename or "." not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET"])
def index():
    """
    Renders the main dashboard page in its initial state (ready for upload).
    """
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """
    Handles file upload, input validation, log parsing, system health calculation,
    and report generation.
    """
    # 1. Verify file part exists in request
    if "log_file" not in request.files:
        flash("No file part detected in request. Please select a log file.", "error")
        return redirect(url_for("index"))
        
    file = request.files["log_file"]
    
    # 2. Check if a file was actually selected
    if file.filename == "":
        flash("No file was selected. Please choose a .log or .txt file to analyze.", "error")
        return redirect(url_for("index"))
        
    # 3. Validate file extension
    if not allowed_file(file.filename):
        flash("Unsupported file format. Please upload a file ending in .log or .txt.", "error")
        return redirect(url_for("index"))
        
    # 4. Secure filename and prepend UUID to prevent collisions and path traversal
    safe_filename = secure_filename(file.filename)
    if not safe_filename:
        safe_filename = "uploaded_log.log"
        
    unique_file_id = uuid.uuid4().hex[:12]
    stored_filename = f"{unique_file_id}_{safe_filename}"
    saved_file_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_filename)
    
    try:
        # Save file safely to uploads folder
        file.save(saved_file_path)
        
        # 5. Read file content with encoding fallback
        try:
            with open(saved_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # Fallback for logs encoded with latin-1 or Windows-1252
            with open(saved_file_path, "r", encoding="latin-1") as f:
                content = f.read()
                
        # 6. Check if file is empty
        if not content or not content.strip():
            flash("The uploaded file is empty. Please upload a file with log entries.", "error")
            return redirect(url_for("index"))
            
        # 7. Analyze log content
        results = analyzer.analyze_log(content)
        
        # 8. Generate plain-text summary report with unique report ID
        report_id = uuid.uuid4().hex[:16]
        report_text = analyzer.generate_report(results, safe_filename, report_id)
        
        report_filename = f"{report_id}.txt"
        report_path = os.path.join(app.config["REPORTS_FOLDER"], report_filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)
            
        # 9. Render the dashboard with analysis results
        return render_template(
            "index.html",
            results=results,
            report_id=report_id,
            filename=safe_filename
        )
        
    except Exception as e:
        # Catch internal processing errors gracefully without exposing stack traces
        flash("An error occurred while processing the log file. Please verify the file format and try again.", "error")
        return redirect(url_for("index"))


@app.route("/download-report/<report_id>", methods=["GET"])
def download_report(report_id):
    """
    Downloads the plain-text analysis report for a given report ID.
    Validates report ID to prevent directory traversal attacks.
    """
    # Strict validation: report_id must be alphanumeric hex characters only
    if not re.match(r"^[a-f0-9]{8,32}$", report_id):
        flash("Invalid report identifier specified.", "error")
        return redirect(url_for("index"))
        
    report_filename = f"{report_id}.txt"
    report_path = os.path.join(app.config["REPORTS_FOLDER"], report_filename)
    
    if not os.path.exists(report_path):
        flash("Requested report was not found or has expired.", "error")
        return redirect(url_for("index"))
        
    return send_from_directory(
        app.config["REPORTS_FOLDER"],
        report_filename,
        as_attachment=True,
        download_name=f"log_analysis_report_{report_id}.txt",
        mimetype="text/plain"
    )


@app.errorhandler(413)
def request_entity_too_large(error):
    """
    Handles uploads exceeding MAX_CONTENT_LENGTH (5 MB).
    """
    flash("The uploaded file exceeds the 5 MB maximum file size limit. Please upload a smaller file.", "error")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(error):
    """
    Handles 404 Not Found errors gracefully.
    """
    flash("The requested page or resource could not be found.", "error")
    return redirect(url_for("index"))


@app.errorhandler(500)
def server_error(error):
    """
    Handles unexpected 500 server errors cleanly without exposing stack traces.
    """
    flash("A server error occurred while processing your request.", "error")
    return redirect(url_for("index"))


# Local development entry point ONLY
# Gunicorn will NOT execute this block when importing app:app
if __name__ == "__main__":
    app.run(debug=True)
