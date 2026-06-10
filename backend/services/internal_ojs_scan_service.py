from backend.services.ojs_scanner import run_ojs_sast_scan


def run_internal_ojs_scan(internal_path):
    return run_ojs_sast_scan(internal_path)
