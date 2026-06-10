def map_to_owasp(name):
    name = name.lower()

    if "sql" in name:
        return "A03: Injection"
    elif "xss" in name:
        return "A03: Injection"
    elif "csrf" in name:
        return "A01: Broken Access Control"
    elif "auth" in name:
        return "A07: Auth Failures"
    elif "config" in name:
        return "A05: Security Misconfiguration"
    else:
        return "A09: Logging & Monitoring"