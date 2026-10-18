"""Small Flask application for classifying UTF-8 text logs."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
import shutil
import uuid

from flask import Flask, abort, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

app = Flask(__name__)
MAX_FILE_SIZE = 5 * 1024 * 1024
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE + 64 * 1024
UPLOAD_DIR = Path(__file__).resolve().parent / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)
LEVEL_PATTERN = re.compile(r'\b(INFO|WARNING|WARN|ERROR)\b', re.IGNORECASE)
INDIA_TIME = timezone(timedelta(hours=5, minutes=30))


def allowed_file(filename):
    return Path(filename).suffix.lower() in {'.log', '.txt'}


def analyze_log_file(path):
    counts = dict.fromkeys(['INFO', 'WARNING', 'ERROR', 'OTHER'], 0)
    errors = Counter()
    with path.open(encoding='utf-8-sig') as log_file:
        for raw_line in log_file:
            if any(ord(char) < 32 and char not in '\t\r\n' for char in raw_line):
                raise ValueError('This file contains binary or unreadable content. Upload UTF-8 text.')
            line = raw_line.strip()
            if not line:
                continue
            match = LEVEL_PATTERN.search(line)
            level = match.group(1).upper() if match else 'OTHER'
            if level == 'WARN':
                level = 'WARNING'
            counts[level] += 1
            if level == 'ERROR':
                message = line[match.end():].lstrip(' \t:]-') or '(No error message)'
                errors[message] += 1
    total = sum(counts.values())
    if not total:
        raise ValueError('No readable log entries found. Choose a file with non-blank text.')
    return {'counts': counts, 'total': total, 'errors': errors.most_common()}


def create_report(result, report_path):
    counts = result['counts']
    lines = ['AUTOMATED LOG FILE ANALYZER REPORT', '=' * 48,
             f"File Name       : {result['filename']}",
             f"Generated At    : {result['generated']} (IST)",
             f"Total Log Lines : {result['total']}", '', 'MESSAGE SUMMARY', '-' * 48]
    lines += [f'{level} Messages : {counts[level]}' for level in ['INFO', 'WARNING', 'ERROR']]
    lines += [f"Other Messages : {counts['OTHER']}", '', 'SEVERITY SUMMARY', '-' * 48,
              f"Low Severity    : {counts['INFO']}", f"Medium Severity : {counts['WARNING']}",
              f"High Severity   : {counts['ERROR']}", '', 'ERROR FREQUENCY', '-' * 48]
    lines += [f'{message} : {count}' for message, count in result['errors']]
    if result['errors']:
        message, count = result['errors'][0]
        lines += ['', f'Most Frequent Error : {message}', f'Frequency : {count}']
    else:
        lines += ['No ERROR messages found.', '', 'Most Frequent Error : None', 'Frequency : 0']
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def cleanup_old_uploads():
    """Reports expire after 24 hours; cleanup runs when another file is uploaded."""
    cutoff = datetime.now().timestamp() - 86400
    for folder in UPLOAD_DIR.iterdir():
        if folder.is_dir() and re.fullmatch(r'[0-9a-f]{32}', folder.name):
            try:
                if folder.stat().st_mtime < cutoff:
                    shutil.rmtree(folder)
            except OSError:
                app.logger.warning('Could not clean an expired upload')


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    job_dir = None
    try:
        upload = request.files.get('file')
        if not upload or not upload.filename:
            raise ValueError('Choose a log file before analyzing.')
        if not allowed_file(upload.filename):
            raise ValueError('Unsupported file type. Please upload a .log or .txt file.')
        filename = secure_filename(upload.filename)
        if not filename:
            raise ValueError('Please rename this file and try again.')
        content = upload.stream.read(MAX_FILE_SIZE + 1)
        if len(content) > MAX_FILE_SIZE:
            raise RequestEntityTooLarge()
        if not content:
            raise ValueError('This file is empty. Choose a file containing log entries.')
        cleanup_old_uploads()
        token = uuid.uuid4().hex
        job_dir = UPLOAD_DIR / token
        job_dir.mkdir()
        # A separate source folder prevents an uploaded report.txt from being overwritten.
        (job_dir / 'source').mkdir()
        path = job_dir / 'source' / filename
        path.write_bytes(content)
        result = analyze_log_file(path)
        result.update(filename=filename, generated=datetime.now(INDIA_TIME).strftime('%d %b %Y, %I:%M:%S %p'), token=token)
        create_report(result, job_dir / 'report.txt')
        return render_template('index.html', result=result)
    except RequestEntityTooLarge:
        if job_dir:
            shutil.rmtree(job_dir, ignore_errors=True)
        raise
    except (ValueError, UnicodeError) as error:
        if job_dir:
            shutil.rmtree(job_dir, ignore_errors=True)
        message = 'Unable to read this file. Please upload UTF-8 text.' if isinstance(error, UnicodeError) else str(error)
        return render_template('index.html', error=message), 400
    except OSError:
        if job_dir:
            shutil.rmtree(job_dir, ignore_errors=True)
        app.logger.exception('File processing failed')
        return render_template('index.html', error='Unable to process the file. Please try again.'), 500


@app.get('/report/<token>')
def download_report(token):
    if not re.fullmatch(r'[0-9a-f]{32}', token):
        abort(404)
    path = UPLOAD_DIR / token / 'report.txt'
    if not path.is_file():
        return render_template('index.html', error='This report has expired or is unavailable. Upload your file again.'), 404
    return send_file(path, as_attachment=True, download_name='log_analysis_report.txt', mimetype='text/plain')


@app.errorhandler(413)
def too_large(error):
    return render_template('index.html', error='The file is too large. Maximum size is 5 MB.'), 413


@app.errorhandler(500)
def server_error(error):
    return render_template('index.html', error='Something went wrong. Please try again.'), 500


@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    return response


if __name__ == '__main__':
    app.run(debug=True)
