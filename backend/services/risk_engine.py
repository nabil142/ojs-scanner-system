def calculate_risk(impact, likelihood, exploitability):
    return impact * likelihood * exploitability

def risk_level(score):
    if score >= 20:
        return "Critical"
    elif score >= 15:
        return "High"
    elif score >= 8:
        return "Medium"
    else:
        return "Low"