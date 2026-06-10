from datetime import datetime
import json
import os
from pathlib import Path


def _clean_text(value):
    text = str(value or "-")
    return text.replace("\r", " ").replace("\n", " ").strip()


def _get_severity_color(level):
    """Get color based on severity level"""
    level_str = str(level or "Low").lower()
    colors = {
        "critical": "#dc2626",
        "high": "#ea580c",
        "medium": "#f59e0b",
        "low": "#3b82f6",
    }
    return colors.get(level_str, "#6b7280")


def _get_severity_badge_bg(level):
    """Get background color for severity badge"""
    level_str = str(level or "Low").lower()
    colors = {
        "critical": "#fee2e2",
        "high": "#fed7aa",
        "medium": "#fef3c7",
        "low": "#dbeafe",
    }
    return colors.get(level_str, "#f3f4f6")


def _severity_counts(vulnerabilities):
    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for item in vulnerabilities:
        level = str(item.get("level", "Low")).capitalize()
        if level not in counts:
            counts[level] = 0
        counts[level] += 1
    return counts


def generate_html_report(scan_record, vulnerabilities, output_dir="reports"):
    """Generate an HTML report from scan results"""
    
    # Create reports directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    counts = _severity_counts(vulnerabilities)
    total = len(vulnerabilities)
    
    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_report_{scan_record.id}_{timestamp}.html"
    filepath = os.path.join(output_dir, filename)
    
    # Build HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OJS Security Report - {scan_record.id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f9fafb;
            color: #1f2937;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 0;
            margin-bottom: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
        }}
        
        .summary-card h3 {{
            color: #6b7280;
            font-size: 0.875em;
            text-transform: uppercase;
            margin-bottom: 10px;
            letter-spacing: 0.5px;
        }}
        
        .summary-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #1f2937;
        }}
        
        .severity-distribution {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 40px;
        }}
        
        .severity-item {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .severity-item .count {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .severity-item .label {{
            font-size: 0.875em;
            color: #6b7280;
            text-transform: uppercase;
        }}
        
        .critical-count {{ color: #dc2626; }}
        .high-count {{ color: #ea580c; }}
        .medium-count {{ color: #f59e0b; }}
        .low-count {{ color: #3b82f6; }}
        
        .meta-info {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 40px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .meta-info table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .meta-info tr {{
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .meta-info tr:last-child {{
            border-bottom: none;
        }}
        
        .meta-info th {{
            background-color: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #4b5563;
            width: 30%;
        }}
        
        .meta-info td {{
            padding: 12px;
            color: #1f2937;
        }}
        
        h2 {{
            color: #1f2937;
            font-size: 1.875em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        
        .vulnerabilities {{
            margin-bottom: 40px;
        }}
        
        .vulnerability-item {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border-left: 4px solid #667eea;
        }}
        
        .vulnerability-item.critical {{
            border-left-color: #dc2626;
        }}
        
        .vulnerability-item.high {{
            border-left-color: #ea580c;
        }}
        
        .vulnerability-item.medium {{
            border-left-color: #f59e0b;
        }}
        
        .vulnerability-item.low {{
            border-left-color: #3b82f6;
        }}
        
        .vulnerability-header {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            gap: 10px;
        }}
        
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .vulnerability-title {{
            flex: 1;
            font-size: 1.25em;
            font-weight: 600;
            color: #1f2937;
        }}
        
        .vulnerability-details {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 15px;
        }}
        
        .detail-item {{
            background-color: #f9fafb;
            padding: 12px;
            border-radius: 4px;
            border-left: 3px solid #e5e7eb;
        }}
        
        .detail-label {{
            font-size: 0.875em;
            color: #6b7280;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        
        .detail-value {{
            color: #1f2937;
            word-break: break-word;
        }}
        
        .vulnerability-description {{
            background-color: #f9fafb;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 15px;
            border-left: 3px solid #e5e7eb;
        }}
        
        .no-vulnerabilities {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            text-align: center;
            color: #6b7280;
        }}
        
        .no-vulnerabilities h3 {{
            color: #16a34a;
            font-size: 1.5em;
            margin-bottom: 10px;
        }}
        
        footer {{
            background-color: #f3f4f6;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            border-radius: 8px;
            margin-top: 40px;
            font-size: 0.875em;
        }}
        
        @media print {{
            body {{
                background-color: white;
            }}
            .container {{
                max-width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 OJS Repository Security Scan Report</h1>
            <p>Comprehensive vulnerability assessment report</p>
        </header>
        
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Scan Target</h3>
                <div class="value">{_clean_text(scan_record.target)}</div>
            </div>
            <div class="summary-card">
                <h3>Total Vulnerabilities</h3>
                <div class="value">{total}</div>
            </div>
            <div class="summary-card">
                <h3>Scanner Source</h3>
                <div class="value">{_clean_text(scan_record.source)}</div>
            </div>
        </div>
        
        <div class="meta-info">
            <table>
                <tr>
                    <th>Report ID</th>
                    <td>{scan_record.id}</td>
                </tr>
                <tr>
                    <th>Scan Timestamp</th>
                    <td>{_clean_text(scan_record.timestamp)}</td>
                </tr>
                <tr>
                    <th>Report Generated</th>
                    <td>{generated_at}</td>
                </tr>
                <tr>
                    <th>Report Type</th>
                    <td>OJS Security Scan Report (HTML)</td>
                </tr>
            </table>
        </div>
        
        <h2>Severity Distribution</h2>
        <div class="severity-distribution">
            <div class="severity-item">
                <div class="count critical-count">{counts.get("Critical", 0)}</div>
                <div class="label">Critical</div>
            </div>
            <div class="severity-item">
                <div class="count high-count">{counts.get("High", 0)}</div>
                <div class="label">High</div>
            </div>
            <div class="severity-item">
                <div class="count medium-count">{counts.get("Medium", 0)}</div>
                <div class="label">Medium</div>
            </div>
            <div class="severity-item">
                <div class="count low-count">{counts.get("Low", 0)}</div>
                <div class="label">Low</div>
            </div>
        </div>
"""
    
    # Add vulnerabilities section
    if not vulnerabilities:
        html_content += """        <h2>Vulnerability Details</h2>
        <div class="no-vulnerabilities">
            <h3>✓ No Vulnerabilities Found</h3>
            <p>The scan completed successfully with no vulnerabilities detected.</p>
        </div>
"""
    else:
        html_content += """        <h2>Vulnerability Details</h2>
        <div class="vulnerabilities">
"""
        for idx, vuln in enumerate(vulnerabilities, 1):
            severity = str(vuln.get("level", "Low")).lower()
            color = _get_severity_color(vuln.get("level", "Low"))
            bg_color = _get_severity_badge_bg(vuln.get("level", "Low"))
            
            html_content += f"""            <div class="vulnerability-item {severity}">
                <div class="vulnerability-header">
                    <span class="severity-badge" style="background-color: {bg_color}; color: {color};">
                        {_clean_text(vuln.get("level", "Low"))}
                    </span>
                    <div class="vulnerability-title">
                        {idx}. {_clean_text(vuln.get("type", "Unknown Vulnerability"))}
                    </div>
                </div>
                
                <div class="vulnerability-details">
                    <div class="detail-item">
                        <div class="detail-label">Score</div>
                        <div class="detail-value">{_clean_text(vuln.get("score", "N/A"))}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Priority</div>
                        <div class="detail-value">{_clean_text(vuln.get("priority", "N/A"))}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">OWASP Category</div>
                        <div class="detail-value">{_clean_text(vuln.get("owasp", "N/A"))}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Critical Area</div>
                        <div class="detail-value">{_clean_text(vuln.get("critical_area", "N/A"))}</div>
                    </div>
                </div>
                
                <div class="vulnerability-description">
                    <div class="detail-label">File Location</div>
                    <div class="detail-value"><code>{_clean_text(vuln.get("location") or vuln.get("file_path", "N/A"))}</code></div>
                </div>
                
                <div class="vulnerability-description">
                    <div class="detail-label">Description</div>
                    <div class="detail-value">{_clean_text(vuln.get("description", "No description available"))}</div>
                </div>
                
                <div class="vulnerability-description">
                    <div class="detail-label">Recommendation</div>
                    <div class="detail-value">{_clean_text(vuln.get("recommendation", "Please review this finding for potential security implications."))}</div>
                </div>
            </div>
"""
        html_content += """        </div>
"""
    
    # Add footer
    html_content += f"""        <footer>
            <p>This report was automatically generated by OJS Security Scanner.</p>
            <p>Generated at {generated_at}</p>
        </footer>
    </div>
</body>
</html>"""
    
    # Write to file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return filepath
