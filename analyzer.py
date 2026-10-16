"""
analyzer.py - Log Parsing and Analysis Engine
Automated Log File Analyzer (CSE/AIML Academic Mini-Project)

This module handles:
1. Detecting severity levels (INFO, WARNING, ERROR, CRITICAL, DEBUG)
2. Normalizing log messages for pattern matching
3. Aggregating severity metrics and counts
4. Detecting repeated issues across the log stream
5. Calculating system health via rule-based logic
6. Formatting structured text reports for download
"""

import re
from collections import Counter
from datetime import datetime


def detect_severity(line):
    """
    Detects the log severity level from a line of text.
    Recognizes INFO, WARNING, WARN (as WARNING), ERROR, CRITICAL, and DEBUG.
    Case-insensitive matching with word boundary detection.
    
    Returns standard severity string ('INFO', 'WARNING', 'ERROR', 'CRITICAL', 'DEBUG')
    or 'OTHER' if no severity keyword is identified.
    """
    # Regex pattern to match standard log severities case-insensitively
    pattern = r"\b(CRITICAL|FATAL|ERROR|WARNING|WARN|INFO|DEBUG)\b"
    match = re.search(pattern, line, re.IGNORECASE)
    
    if not match:
        return "OTHER"
    
    matched_text = match.group(1).upper()
    
    # Normalize aliases: WARN and FATAL to standard names
    if matched_text == "WARN":
        return "WARNING"
    if matched_text == "FATAL":
        return "CRITICAL"
        
    return matched_text


def normalize_message(line, severity):
    """
    Strips changing elements (timestamps, thread IDs, log levels)
    to reveal the core underlying message. This allows identical repeated
    errors with different timestamps to be grouped together.
    """
    text = line.strip()
    
    # 1. Remove common bracketed or ISO timestamps, e.g.,
    # 2026-10-16 08:00:01, [2026-10-16T08:00:01.123Z], [16/Oct/2026:08:00:01]
    text = re.sub(r"^\[?\d{4}[-/.]\d{2}[-/.]\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?\]?", "", text)
    text = re.sub(r"^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d+\s+\d{2}:\d{2}:\d{2}", "", text)
    text = text.strip()
    
    # 2. Remove process/thread/host identifiers, e.g., "host app[1234]:", "[worker-3]"
    text = re.sub(r"^[a-zA-Z0-9_\-\.]+\[\d+\]:\s*", "", text)
    text = re.sub(r"^\[[\w\-\s]+\]\s*", "", text)
    text = text.strip()
    
    # 3. Remove leading severity tag, e.g., "ERROR", "[ERROR]", "ERROR:", "WARNING -"
    text = re.sub(r"^\[?(?:CRITICAL|FATAL|ERROR|WARNING|WARN|INFO|DEBUG)\]?[:\s\-–—]*", "", text, flags=re.IGNORECASE)
    text = text.strip()
    
    # 4. Remove leading punctuation remnants like ': ', '- '
    text = re.sub(r"^[:\s\-–—|]+\s*", "", text)
    text = text.strip()
    
    # If stripping resulted in empty string, fallback to original line
    return text if text else line.strip()


def calculate_health(critical_count, error_count, warning_count, total_detected):
    """
    Calculates overall system health using a clear rule-based decision tree.
    This logic is strictly deterministic and straightforward for viva explanation.
    
    Rules:
    - Critical: If any CRITICAL events occurred.
    - High Risk: If >= 10 errors OR errors exceed 20% of classified logs.
    - Needs Attention: If any ERROR events occurred.
    - Warning: If any WARNING events occurred (without errors).
    - Healthy: No warnings, errors, or critical events.
    """
    if critical_count > 0:
        return {
            "status": "Critical",
            "explanation": "Critical events were detected in this log file.",
            "css_class": "status-critical"
        }
    
    # Calculate error percentage relative to all classified logs
    error_percentage = (error_count / total_detected) if total_detected > 0 else 0
    
    if error_count >= 10 or (total_detected >= 5 and error_percentage >= 0.20):
        return {
            "status": "High Risk",
            "explanation": f"High error volume detected ({error_count} errors, {error_percentage:.1%} of logs).",
            "css_class": "status-high-risk"
        }
        
    if error_count > 0:
        return {
            "status": "Needs Attention",
            "explanation": f"Errors detected ({error_count} errors) requiring investigation.",
            "css_class": "status-needs-attention"
        }
        
    if warning_count > 0:
        return {
            "status": "Warning",
            "explanation": "Warnings detected; system is operational but needs review.",
            "css_class": "status-warning"
        }
        
    return {
        "status": "Healthy",
        "explanation": "No errors or critical events were detected in this log file.",
        "css_class": "status-healthy"
    }


def find_repeated_issues(entries):
    """
    Finds messages that occurred more than once.
    Prioritizes CRITICAL, ERROR, and WARNING messages.
    Returns a sorted list of repeated issues with their severity and counts.
    """
    # Track counts keyed by (severity, normalized_message)
    counts = Counter()
    
    for entry in entries:
        severity = entry["severity"]
        # Only track issues for warnings, errors, and critical events
        if severity in ("CRITICAL", "ERROR", "WARNING"):
            norm_msg = normalize_message(entry["message"], severity)
            counts[(severity, norm_msg)] += 1
            
    # Filter to items occurring more than once
    repeated = []
    severity_rank = {"CRITICAL": 1, "ERROR": 2, "WARNING": 3}
    
    for (severity, message), count in counts.items():
        if count > 1:
            repeated.append({
                "severity": severity,
                "message": message,
                "count": count,
                "rank": severity_rank.get(severity, 99)
            })
            
    # Sort first by severity rank (CRITICAL first, then ERROR, then WARNING), then count desc
    repeated.sort(key=lambda item: (item["rank"], -item["count"]))
    
    # Remove internal rank before returning
    for item in repeated:
        del item["rank"]
        
    return repeated


def find_important_issues(entries, repeated_issues):
    """
    Builds a concise summary of critical and high-priority problems.
    Avoids flooding the dashboard with thousands of raw duplicates.
    Prioritizes:
    - Unique CRITICAL issues
    - Unique ERROR issues
    - Repeated WARNING issues
    """
    important = []
    seen_messages = set()
    
    # Priority 1: All CRITICAL logs (deduplicated by message)
    for entry in entries:
        if entry["severity"] == "CRITICAL":
            msg = normalize_message(entry["message"], "CRITICAL")
            if msg not in seen_messages:
                seen_messages.add(msg)
                important.append({
                    "severity": "CRITICAL",
                    "line_number": entry["line_number"],
                    "message": msg
                })
                
    # Priority 2: Distinct ERROR logs (up to 10 unique patterns)
    error_count = 0
    for entry in entries:
        if entry["severity"] == "ERROR":
            msg = normalize_message(entry["message"], "ERROR")
            if msg not in seen_messages:
                seen_messages.add(msg)
                important.append({
                    "severity": "ERROR",
                    "line_number": entry["line_number"],
                    "message": msg
                })
                error_count += 1
                if error_count >= 10:
                    break
                    
    # Priority 3: Frequent WARNINGs from repeated issues list
    for rep in repeated_issues:
        if rep["severity"] == "WARNING" and rep["message"] not in seen_messages:
            seen_messages.add(rep["message"])
            important.append({
                "severity": "WARNING",
                "line_number": "-",
                "message": f"{rep['message']} (Repeated {rep['count']} times)"
            })
            
    return important


def analyze_log(raw_content):
    """
    Main analysis pipeline.
    Parses every line in the raw log content and computes:
    - Line counts & severity distribution
    - System health
    - Repeated issues
    - Important issues
    - Parsed entries list
    """
    # Split content into individual lines
    lines = raw_content.splitlines()
    total_lines = len(lines)
    
    entries = []
    info_count = 0
    warning_count = 0
    error_count = 0
    critical_count = 0
    debug_count = 0
    
    for idx, line in enumerate(lines, start=1):
        # Skip completely empty blank lines
        if not line.strip():
            continue
            
        severity = detect_severity(line)
        cleaned_msg = normalize_message(line, severity)
        
        # Accumulate severity metrics
        if severity == "INFO":
            info_count += 1
        elif severity == "WARNING":
            warning_count += 1
        elif severity == "ERROR":
            error_count += 1
        elif severity == "CRITICAL":
            critical_count += 1
        elif severity == "DEBUG":
            debug_count += 1
            
        entries.append({
            "line_number": idx,
            "severity": severity,
            "message": cleaned_msg,
            "raw_line": line
        })
        
    total_detected = info_count + warning_count + error_count + critical_count + debug_count
    
    # Calculate health status
    health = calculate_health(critical_count, error_count, warning_count, total_detected)
    
    # Detect repeated issues
    repeated = find_repeated_issues(entries)
    
    # Identify high priority problems
    important = find_important_issues(entries, repeated)
    
    # Limit displayed rows to 500 for snappy browser rendering
    display_limit = 500
    displayed_entries = entries[:display_limit]
    is_truncated = len(entries) > display_limit
    
    return {
        "total_lines": total_lines,
        "total_parsed": len(entries),
        "info": info_count,
        "warning": warning_count,
        "error": error_count,
        "critical": critical_count,
        "debug": debug_count,
        "health": health,
        "repeated_issues": repeated,
        "important_issues": important,
        "entries": displayed_entries,
        "display_limit": display_limit,
        "is_truncated": is_truncated
    }


def generate_report(analysis_results, original_filename, report_id):
    """
    Generates a structured, clean plain-text report summarizing
    the analysis results. The output is saved to the reports/ directory
    and can be downloaded by the user.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Build repeated issues block
    if analysis_results["repeated_issues"]:
        repeated_block = []
        for issue in analysis_results["repeated_issues"]:
            repeated_block.append(f"  [{issue['severity']}] (Occurrences: {issue['count']})\n    {issue['message']}")
        repeated_text = "\n\n".join(repeated_block)
    else:
        repeated_text = "  No repeated issues detected."
        
    # Build important issues block
    if analysis_results["important_issues"]:
        important_block = []
        for issue in analysis_results["important_issues"]:
            line_str = f"Line {issue['line_number']}" if issue['line_number'] != "-" else "Multiple Lines"
            important_block.append(f"  [{issue['severity']}] ({line_str})\n    {issue['message']}")
        important_text = "\n\n".join(important_block)
    else:
        important_text = "  No critical or high-priority issues detected."
        
    report = f"""================================================================================
AUTOMATED LOG FILE ANALYZER - ANALYSIS REPORT
================================================================================

File Name:          {original_filename}
Report ID:          {report_id}
Analysis Date/Time: {timestamp}
Total Lines:        {analysis_results['total_lines']}
Total Classified:   {analysis_results['total_parsed']}

--------------------------------------------------------------------------------
SUMMARY METRICS
--------------------------------------------------------------------------------
Total Log Entries:  {analysis_results['total_lines']}
INFO Count:         {analysis_results['info']}
WARNING Count:      {analysis_results['warning']}
ERROR Count:        {analysis_results['error']}
CRITICAL Count:     {analysis_results['critical']}
DEBUG Count:        {analysis_results['debug']}

--------------------------------------------------------------------------------
SYSTEM HEALTH
--------------------------------------------------------------------------------
Status:             {analysis_results['health']['status']}
Explanation:        {analysis_results['health']['explanation']}

--------------------------------------------------------------------------------
IMPORTANT ISSUES
--------------------------------------------------------------------------------
{important_text}

--------------------------------------------------------------------------------
REPEATED ISSUES
--------------------------------------------------------------------------------
{repeated_text}

================================================================================
End of Report - Generated by Automated Log File Analyzer
================================================================================
"""
    return report
