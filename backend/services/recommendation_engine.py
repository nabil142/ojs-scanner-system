def get_recommendation(vuln_name):
    vuln_name = vuln_name.lower()

    if "sql" in vuln_name or "injection" in vuln_name:
        return "Use parameterized queries, ORM protections, and limit database privileges."
    elif "xss" in vuln_name or "cross-site" in vuln_name:
        return "Escape or sanitize user input, use CSP headers, and validate output contexts."
    elif "csrf" in vuln_name:
        return "Implement CSRF tokens, same-site cookies, and validate state-changing requests."
    elif "auth" in vuln_name or "login" in vuln_name or "session" in vuln_name:
        return "Enforce strong authentication, session timeout, and multi-factor controls."
    elif "config" in vuln_name or "misconfig" in vuln_name or "server" in vuln_name:
        return "Harden server settings, remove default pages, and keep software up to date."
    elif "exposure" in vuln_name or "leak" in vuln_name or "disclosure" in vuln_name:
        return "Remove sensitive data from responses and protect assets with access controls."
    else:
        return "Review the finding and apply security best practices or vendor guidance."