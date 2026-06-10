import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable

from backend.services.risk_engine import calculate_risk


TEXT_EXTENSIONS = {
    ".php",
    ".inc",
    ".ini",
    ".conf",
    ".env",
    ".json",
    ".xml",
    ".yml",
    ".yaml",
    ".tpl",
    ".js",
    ".htaccess",
}

SKIP_DIRS = {
    ".git",
    "cache",
    "node_modules",
    "vendor",
    "public",
    "tmp",
    "logs",
}

RISKY_PHP_FUNCTIONS = [
    "eval",
    "exec",
    "shell_exec",
    "system",
    "passthru",
    "proc_open",
    "popen",
    "assert",
    "unserialize",
]


@dataclass
class OjsSastContext:
    root: Path
    scanned_at: str


@dataclass
class OjsScannerAgentConfig:
    source_path: str = os.environ.get("OJS_SOURCE_PATH", "/var/www/html")
    output_path: str = os.environ.get("SCANNER_OUTPUT_PATH", "/scan-output/latest.json")
    trigger_path: str = os.environ.get("SCANNER_TRIGGER_PATH", "")
    interval_seconds: int = int(os.environ.get("SCANNER_INTERVAL_SECONDS", "300"))
    once: bool = os.environ.get("SCANNER_ONESHOT", "false").lower() in {"1", "true", "yes", "on"}
    watch_changes: bool = os.environ.get("SCANNER_WATCH_CHANGES", "true").lower() in {"1", "true", "yes", "on"}
    watch_interval_seconds: int = int(os.environ.get("SCANNER_WATCH_INTERVAL_SECONDS", "5"))


SastPlugin = Callable[[OjsSastContext], list[dict]]


def _risk(level):
    level = level.lower()
    if level == "critical":
        return calculate_risk(3, 3, 3)
    if level == "high":
        return calculate_risk(3, 3, 2)
    if level == "medium":
        return calculate_risk(2, 2, 2)
    return calculate_risk(1, 1, 1)


def _finding(
    vuln_type,
    level,
    description,
    recommendation,
    path="",
    line=None,
    owasp="A05:2021 - Security Misconfiguration",
    code_snippet="",
    source="OJS SAST Agent",
):
    location = path
    if line:
        location = f"{path}:{line}"

    return {
        "type": vuln_type,
        "vulnerability_type": vuln_type,
        "level": level,
        "severity": level,
        "score": _risk(level),
        "owasp": owasp,
        "recommendation": recommendation,
        "source": source,
        "description": description,
        "file_path": path,
        "line_number": line,
        "code_snippet": code_snippet.strip() if code_snippet else "",
        "vulnerable_code": code_snippet.strip() if code_snippet else "",
        "location": location,
    }


def _read_text(path):
    try:
        if path.stat().st_size > 2_000_000:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _read_line(path, line_no):
    if not line_no:
        return ""
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for current_no, line in enumerate(handle, start=1):
                if current_no == line_no:
                    return line.strip()
    except OSError:
        return ""
    return ""


def _relative(root, path):
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _parse_ini_value(text, key):
    pattern = rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$"
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if not match:
        return ""
    return match.group(1).strip().strip('"').strip("'")


def _find_ini_line(text, key):
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=", re.IGNORECASE)
    for line_no, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            return line_no, line.strip()
    return None, ""


def _iter_scannable_files(root):
    count = 0
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [item for item in dirs if item not in SKIP_DIRS]

        for file_name in files:
            path = Path(current_root) / file_name
            suffix = path.suffix.lower()
            if suffix not in TEXT_EXTENSIONS and file_name not in {".env", ".htaccess"}:
                continue
            count += 1
            if count > 5000:
                return
            yield path


def _source_signature(root):
    root = Path(root).expanduser()
    if not root.exists() or not root.is_dir():
        return None

    latest_mtime = root.stat().st_mtime_ns
    file_count = 0
    total_size = 0

    for path in _iter_scannable_files(root):
        try:
            stat = path.stat()
        except OSError:
            continue

        file_count += 1
        total_size += stat.st_size
        latest_mtime = max(latest_mtime, stat.st_mtime_ns)

    return file_count, total_size, latest_mtime


def _trigger_signature(trigger_path):
    if not trigger_path:
        return None

    path = Path(trigger_path).expanduser()
    if not path.exists() or not path.is_file():
        return None

    try:
        stat = path.stat()
    except OSError:
        return None

    return stat.st_size, stat.st_mtime_ns


def _extract_ojs_version(root):
    candidates = [
        root / "dbscripts" / "xml" / "version.xml",
        root / "lib" / "pkp" / "dbscripts" / "xml" / "version.xml",
    ]

    for candidate in candidates:
        if not candidate.exists():
            continue

        text = _read_text(candidate)
        release = re.search(r"<release>([^<]+)</release>", text, re.IGNORECASE)
        version = re.search(r"<version>([^<]+)</version>", text, re.IGNORECASE)
        if release:
            return release.group(1).strip(), _relative(root, candidate)
        if version:
            return version.group(1).strip(), _relative(root, candidate)

    return "", ""


def detect_ojs_source(source_path):
    root = Path(source_path).expanduser()
    if not root.exists() or not root.is_dir():
        return {
            "ok": False,
            "is_ojs": False,
            "status": "OJS source path not found",
            "message": f"Path source OJS tidak ditemukan atau bukan direktori: {source_path}",
            "version": "",
            "version_source": "",
            "indicators": [],
        }

    root = root.resolve()
    config_exists = (root / "config.inc.php").exists()
    config_template_exists = (root / "config.TEMPLATE.inc.php").exists()
    pkp_lib_exists = (root / "lib" / "pkp").exists()
    ojs_index_exists = (root / "index.php").exists()
    ojs_structure_exists = (root / "classes").exists() and (root / "plugins").exists()
    version, version_source = _extract_ojs_version(root)

    indicators = []
    if config_exists:
        indicators.append("config.inc.php")
    if config_template_exists:
        indicators.append("config.TEMPLATE.inc.php")
    if pkp_lib_exists:
        indicators.append("lib/pkp")
    if ojs_index_exists:
        indicators.append("index.php")
    if ojs_structure_exists:
        indicators.append("classes/plugins")
    if version:
        indicators.append("version.xml")

    is_ojs_source = (
        (config_exists or config_template_exists)
        and (pkp_lib_exists or ojs_structure_exists)
        and ojs_index_exists
    )

    return {
        "ok": True,
        "is_ojs": is_ojs_source,
        "status": "PKP OJS Source Detected" if is_ojs_source else "PKP OJS source indicators not found",
        "message": (
            "Path terlihat sebagai source/root instalasi PKP OJS."
            if is_ojs_source
            else "Path belum terlihat sebagai root source PKP OJS."
        ),
        "version": version,
        "version_source": version_source,
        "version_message": "Versi OJS dibaca dari file source." if version else "Versi OJS tidak ditemukan dari source.",
        "indicators": indicators,
        "path": str(root),
    }


def config_security_plugin(context):
    root = context.root
    findings = []
    config_path = root / "config.inc.php"
    template_path = root / "config.TEMPLATE.inc.php"
    if not config_path.exists():
        if not template_path.exists():
            findings.append(_finding(
                "Missing OJS config.inc.php",
                "Low",
                "File config.inc.php tidak ditemukan pada root OJS.",
                "Pastikan agent diarahkan ke root instalasi OJS yang benar. Untuk production, config.inc.php harus tersedia dengan permission aman.",
                "config.inc.php",
                code_snippet="config.inc.php not found",
            ))
        return findings

    rel = _relative(root, config_path)
    text = _read_text(config_path)
    checks = [
        ("installed", {"off", "false", "0", "no"}, "OJS Installer Still Enabled", "Critical", "Set installed = On setelah instalasi selesai agar installer tidak dapat digunakan ulang."),
        ("display_errors", {"on", "true", "1", "yes"}, "PHP Error Display Enabled", "Medium", "Set display_errors = Off pada production dan kirim error ke log internal."),
        ("debug", {"on", "true", "1", "yes"}, "OJS Debug Mode Enabled", "High", "Nonaktifkan debug mode pada production agar path, query, dan detail internal tidak bocor."),
        ("session_check_ip", {"off", "false", "0", "no"}, "Session IP Check Disabled", "Low", "Evaluasi session_check_ip sesuai arsitektur reverse proxy dan jaringan kampus."),
    ]

    for key, bad_values, vuln_type, level, recommendation in checks:
        value = _parse_ini_value(text, key).lower()
        if value in bad_values:
            line_no, code = _find_ini_line(text, key)
            findings.append(_finding(
                vuln_type,
                level,
                f"Nilai {key} pada config.inc.php adalah {value}.",
                recommendation,
                rel,
                line_no,
                code_snippet=code,
            ))

    encryption = _parse_ini_value(text, "encryption").lower()
    if encryption in {"", "none", "off", "false", "0"}:
        line_no, code = _find_ini_line(text, "encryption")
        findings.append(_finding(
            "Weak or Missing OJS Encryption Setting",
            "Medium",
            "Konfigurasi encryption tidak ditemukan atau tidak aktif.",
            "Gunakan konfigurasi enkripsi yang direkomendasikan OJS/PKP dan pastikan secret/salt tersimpan aman.",
            rel,
            line_no,
            code_snippet=code or "encryption setting not found",
        ))

    password = _parse_ini_value(text, "password")
    if password == "":
        line_no, code = _find_ini_line(text, "password")
        findings.append(_finding(
            "Empty Database Password in OJS Config",
            "High",
            "Password database pada config.inc.php kosong.",
            "Gunakan password database yang kuat dan batasi privilege akun database hanya untuk kebutuhan OJS.",
            rel,
            line_no,
            owasp="A07:2021 - Identification and Authentication Failures",
            code_snippet=code,
        ))

    return findings


def sensitive_file_plugin(context):
    root = context.root
    findings = []
    sensitive_names = {
        ".env",
        ".env.local",
        ".env.production",
        "backup.sql",
        "database.sql",
        "dump.sql",
    }
    backup_patterns = (".bak", ".backup", ".old", ".orig", ".save", ".sql", ".zip")

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if name in sensitive_names or name.endswith(backup_patterns):
            rel = _relative(root, path)
            findings.append(_finding(
                "Sensitive or Backup File Present in OJS Directory",
                "Medium",
                f"File sensitif/backup ditemukan pada folder OJS: {rel}.",
                "Pindahkan backup, dump database, dan file env keluar dari web root serta lindungi dengan access control.",
                rel,
                owasp="A01:2021 - Broken Access Control",
                code_snippet=f"Sensitive file present: {rel}",
            ))
    return findings


def risky_code_plugin(context):
    root = context.root
    findings = []
    function_pattern = re.compile(
        r"\b(" + "|".join(re.escape(name) for name in RISKY_PHP_FUNCTIONS) + r")\s*\(",
        re.IGNORECASE,
    )
    sql_concat_pattern = re.compile(
        r"(SELECT|INSERT|UPDATE|DELETE).*(\$_GET|\$_POST|\$_REQUEST|\$_COOKIE)",
        re.IGNORECASE,
    )

    for path in _iter_scannable_files(root):
        rel = _relative(root, path)
        text = _read_text(path)
        if not text:
            continue

        for line_no, line in enumerate(text.splitlines(), start=1):
            function_match = function_pattern.search(line)
            if function_match:
                findings.append(_finding(
                    "Risky PHP Function Usage",
                    "High",
                    f"Fungsi PHP berisiko '{function_match.group(1)}' ditemukan pada kode OJS/plugin.",
                    "Review penggunaan fungsi ini. Hindari eksekusi command/code dinamis, validasi input, dan gunakan API aman.",
                    rel,
                    line_no,
                    owasp="A03:2021 - Injection",
                    code_snippet=line,
                ))
                break

        for line_no, line in enumerate(text.splitlines(), start=1):
            if sql_concat_pattern.search(line):
                findings.append(_finding(
                    "Potential SQL Injection Pattern",
                    "High",
                    "Query SQL terlihat menggunakan input request secara langsung.",
                    "Gunakan prepared statement/DAO OJS dan validasi input sebelum dipakai dalam query.",
                    rel,
                    line_no,
                    owasp="A03:2021 - Injection",
                    code_snippet=line,
                ))
                break

    return findings


def source_hygiene_plugin(context):
    root = context.root
    findings = []
    git_path = root / ".git"
    if git_path.exists():
        findings.append(_finding(
            "Git Directory Present in OJS Root",
            "High",
            "Folder .git ditemukan pada root OJS. Jika web server salah konfigurasi, riwayat source code dapat terekspos.",
            "Hapus folder .git dari production atau pastikan web server memblokir akses ke dotfiles.",
            ".git",
            owasp="A01:2021 - Broken Access Control",
            code_snippet="Directory present: .git",
        ))
    return findings


def _semgrep_rules_path():
    return Path(__file__).resolve().parents[1] / "rules" / "semgrep-ojs.yml"


def _semgrep_level(severity):
    severity = (severity or "").upper()
    if severity == "ERROR":
        return "High"
    if severity == "WARNING":
        return "Medium"
    return "Low"


def semgrep_engine_plugin(context):
    if os.environ.get("SEMGREP_ENABLED", "true").lower() not in {"1", "true", "yes", "on"}:
        return []

    semgrep_bin = shutil.which("semgrep")
    rules_path = _semgrep_rules_path()
    if not semgrep_bin or not rules_path.exists():
        return []

    timeout = int(os.environ.get("SEMGREP_TIMEOUT_SECONDS", "90"))
    max_targets = int(os.environ.get("SEMGREP_MAX_TARGETS", "30"))
    target_candidates = []
    token_pattern = re.compile(
        r"\b(" + "|".join(re.escape(name) for name in RISKY_PHP_FUNCTIONS) + r")\s*\(|\$_(GET|POST|REQUEST|COOKIE)",
        re.IGNORECASE,
    )
    for path in _iter_scannable_files(context.root):
        if path.suffix.lower() not in {".php", ".inc"}:
            continue
        text = _read_text(path)
        if token_pattern.search(text):
            target_candidates.append(path)
        if len(target_candidates) >= max_targets:
            break

    targets = [str(path) for path in target_candidates]
    if not targets:
        return []

    command = [
        semgrep_bin,
        "--json",
        "--quiet",
        "--config",
        str(rules_path),
        "--jobs",
        os.environ.get("SEMGREP_JOBS", "2"),
        "--timeout",
        os.environ.get("SEMGREP_PER_FILE_TIMEOUT", "5"),
        "--exclude",
        "vendor",
        "--exclude",
        "node_modules",
        "--exclude",
        "cache",
        "--exclude",
        "public",
        *targets,
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []

    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return []

    findings = []
    for result in payload.get("results", []):
        path = Path(result.get("path", ""))
        rel = _relative(context.root, path) if path else ""
        extra = result.get("extra", {})
        metadata = extra.get("metadata", {}) or {}
        start = result.get("start", {}) or {}
        line_no = start.get("line")
        code = _read_line(path, line_no) or (extra.get("lines") or "").strip()
        recommendation = (
            metadata.get("recommendation")
            or metadata.get("fix")
            or "Review temuan Semgrep ini, validasi input, dan gunakan API/framework OJS yang aman."
        )
        owasp = metadata.get("owasp") or "A03:2021 - Injection"
        vuln_type = metadata.get("vulnerability_type") or result.get("check_id", "Semgrep Finding")

        findings.append(_finding(
            vuln_type,
            _semgrep_level(extra.get("severity")),
            extra.get("message", "Semgrep menemukan pola kode yang berisiko."),
            recommendation,
            rel,
            line_no,
            owasp=owasp,
            code_snippet=code,
            source="Semgrep Engine",
        ))

    return findings


BUILTIN_PLUGINS: list[SastPlugin] = [
    config_security_plugin,
    sensitive_file_plugin,
    risky_code_plugin,
    source_hygiene_plugin,
    semgrep_engine_plugin,
]


def _metadata(root, repository_status):
    plugin_dir = root / "plugins"
    plugins = []
    if plugin_dir.exists():
        plugins = [item.name for item in plugin_dir.iterdir() if item.is_dir()][:50]

    return {
        "path": str(root),
        "is_ojs_source": repository_status.get("is_ojs", False),
        "ojs_version": repository_status.get("version", ""),
        "version_source": repository_status.get("version_source", ""),
        "plugin_count": len(plugins),
        "plugins": plugins,
        "scanner_mode": "agent_sast",
    }


def run_ojs_sast_scan(source_path, plugins: Iterable[SastPlugin] | None = None):
    if not source_path:
        return {
            "ok": False,
            "enabled": False,
            "error": "SAST agent skipped because no OJS source path was provided.",
            "findings": [],
            "metadata": {},
        }

    repository_status = detect_ojs_source(source_path)
    if not repository_status.get("ok"):
        return {
            "ok": False,
            "enabled": True,
            "error": repository_status.get("message", "OJS source path cannot be scanned."),
            "findings": [],
            "metadata": {},
            "repository_status": repository_status,
        }

    root = Path(source_path).expanduser().resolve()
    context = OjsSastContext(root=root, scanned_at=datetime.utcnow().isoformat())
    findings = []

    if not repository_status.get("is_ojs"):
        findings.append(_finding(
            "Path Does Not Look Like PKP OJS Source Root",
            "Low",
            "Path internal tidak memiliki kombinasi indikator root PKP OJS seperti config.inc.php/config.TEMPLATE.inc.php, index.php, serta lib/pkp atau struktur classes/plugins.",
            "Pastikan path diarahkan ke root instalasi/source code PKP OJS, bukan folder aplikasi lain.",
            str(root),
        ))
    else:
        for plugin in plugins or BUILTIN_PLUGINS:
            findings.extend(plugin(context))

    return {
        "ok": True,
        "enabled": True,
        "error": "",
        "findings": findings,
        "metadata": _metadata(root, repository_status),
        "repository_status": repository_status,
        "scanned_at": context.scanned_at,
    }


class OjsScannerAgent:
    def __init__(self, config=None, plugins=None):
        self.config = config or OjsScannerAgentConfig()
        self.plugins = plugins or BUILTIN_PLUGINS

    def scan_once(self):
        result = run_ojs_sast_scan(self.config.source_path, self.plugins)
        self.write_output(result)
        return result

    def write_output(self, result):
        output_path = Path(self.config.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    def run_forever(self):
        last_signature = None
        last_trigger_signature = None
        last_scan_at = 0

        while True:
            now = time.monotonic()
            signature = _source_signature(self.config.source_path)
            trigger_signature = _trigger_signature(self.config.trigger_path)
            interval_due = now - last_scan_at >= max(10, self.config.interval_seconds)
            source_changed = signature is not None and signature != last_signature
            trigger_changed = trigger_signature is not None and trigger_signature != last_trigger_signature

            if signature is None or not self.config.watch_changes or source_changed or trigger_changed or interval_due:
                self.scan_once()
                last_scan_at = now
                last_signature = signature
                last_trigger_signature = trigger_signature

            if self.config.once:
                break
            if self.config.watch_changes:
                time.sleep(max(1, self.config.watch_interval_seconds))
            else:
                time.sleep(max(10, self.config.interval_seconds))


def get_target_metadata(source_path: str):
    from pathlib import Path
    repo_status = detect_ojs_source(source_path)
    file_count = 0
    root = Path(source_path).expanduser()
    if root.exists() and root.is_dir():
        root = root.resolve()
        for path in _iter_scannable_files(root):
            file_count += 1
            
    return {
        "is_ojs": repo_status.get("is_ojs", False),
        "version": repo_status.get("version") or "Tidak terdeteksi",
        "file_count": file_count,
        "path": str(root),
    }

