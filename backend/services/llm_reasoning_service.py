import json
import os

import requests

from backend import config


def _get_llm_settings():
    file_values = config.read_env_file()
    env_path = config.env_file_path()
    provider = (
        os.environ.get("LLM_PROVIDER")
        or file_values.get("LLM_PROVIDER")
        or config.LLM_PROVIDER
    ).strip().lower()
    api_key = (
        os.environ.get("LLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or file_values.get("LLM_API_KEY")
        or file_values.get("OPENAI_API_KEY")
        or config.LLM_API_KEY
    )
    model = os.environ.get("LLM_MODEL") or file_values.get("LLM_MODEL") or config.LLM_MODEL
    base_url = os.environ.get("LLM_BASE_URL") or file_values.get("LLM_BASE_URL") or config.LLM_BASE_URL
    timeout = int(os.environ.get("LLM_TIMEOUT") or file_values.get("LLM_TIMEOUT") or str(config.LLM_TIMEOUT))

    if not provider and api_key:
        provider = "openai"

    return {
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "base_url": base_url,
        "timeout": timeout,
        "env_file": str(env_path),
        "env_file_exists": env_path.exists(),
    }


def _normalize_provider():
    return _get_llm_settings()["provider"]


def _priority_for_level(level):
    level = (level or "").lower()
    if level == "critical":
        return "Segera"
    if level == "high":
        return "Tinggi"
    if level == "medium":
        return "Sedang"
    return "Rendah"


def _critical_area(vulnerability):
    text = " ".join([
        vulnerability.get("type", ""),
        vulnerability.get("description", ""),
        vulnerability.get("owasp", ""),
        vulnerability.get("source", ""),
    ]).lower()

    if any(term in text for term in ["content-security-policy", "x-frame", "x-content-type", "referrer-policy", "permissions-policy", "header"]):
        return "HTTP Security Header"
    if any(term in text for term in ["login", "auth", "session", "cookie", "csrf"]):
        return "Authentication and Session"
    if any(term in text for term in ["sql", "injection", "xss", "cross-site", "command"]):
        return "Input Validation"
    if any(term in text for term in ["directory", "listing", "git", "config", "exposure", "disclosure", "backup"]):
        return "Sensitive File Exposure"
    if any(term in text for term in ["ssl", "tls", "https", "hsts"]):
        return "Transport Security"
    if any(term in text for term in ["server", "apache", "nginx", "php", "deprecated", "outdated"]):
        return "Server Configuration"
    return "Application Security"


def _fallback_reasoning(vulnerability):
    level = vulnerability.get("level", "Low")
    vuln_type = vulnerability.get("type", "Unknown vulnerability")
    area = _critical_area(vulnerability)
    recommendation = vulnerability.get("recommendation", "Review the finding and apply security best practices.")

    reason_by_level = {
        "Critical": "Temuan ini berisiko sangat tinggi karena dapat berdampak langsung pada kerahasiaan, integritas, atau ketersediaan repository OJS.",
        "High": "Temuan ini perlu diprioritaskan karena dapat memperbesar peluang eksploitasi atau membuka akses ke informasi penting.",
        "Medium": "Temuan ini meningkatkan permukaan serangan dan dapat menjadi bagian dari rantai eksploitasi jika digabung dengan kelemahan lain.",
        "Low": "Temuan ini berisiko rendah, tetapi tetap sebaiknya diperbaiki untuk memperkuat baseline keamanan repository.",
    }

    return {
        **vulnerability,
        "critical_area": area,
        "severity_reason": reason_by_level.get(level, reason_by_level["Low"]),
        "repair_steps": recommendation,
        "priority": _priority_for_level(level),
        "llm_used": False,
        "reasoning_source": "fallback",
        "reasoning_error": "",
    }


def _build_prompt(target, repository_status, vulnerabilities):
    compact_findings = []
    for index, item in enumerate(vulnerabilities):
        compact_findings.append({
            "index": index,
            "type": item.get("type", ""),
            "level": item.get("level", ""),
            "score": item.get("score", ""),
            "owasp": item.get("owasp", ""),
            "source": item.get("source", ""),
            "location": item.get("location", ""),
            "file_path": item.get("file_path", ""),
            "line_number": item.get("line_number", ""),
            "code_snippet": item.get("code_snippet", ""),
            "description": item.get("description", ""),
            "recommendation": item.get("recommendation", ""),
        })

    context = {
        "target": target,
        "repository_status": {
            "is_ojs": repository_status.get("is_ojs", False),
            "ojs_version": repository_status.get("version", ""),
            "status": repository_status.get("status", ""),
            "indicators": repository_status.get("indicators", []),
        },
        "findings": compact_findings,
    }

    return (
        "Anda adalah analis keamanan aplikasi web dan OJS. "
        "Tugas Anda menjelaskan hasil scanner secara ringkas, faktual, dan tidak mengarang temuan baru. "
        "Gunakan bahasa Indonesia. Untuk setiap finding, berikan area kritis, alasan severity, prioritas, "
        "dan langkah perbaikan praktis. Jawab hanya JSON valid dengan schema: "
        '{"items":[{"index":0,"critical_area":"...","severity_reason":"...",'
        '"priority":"Segera|Tinggi|Sedang|Rendah","repair_steps":"..."}]}. '
        f"Data scanner: {json.dumps(context, ensure_ascii=False)}"
    )


def _parse_llm_items(content):
    content = (content or "").strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:].strip()

    data = json.loads(content)
    items = data.get("items", [])
    return {
        int(item["index"]): item
        for item in items
        if "index" in item
    }


def _call_openai_compatible(prompt, settings):
    base_url = (settings["base_url"] or "https://api.openai.com/v1").rstrip("/")
    headers = {
        "Authorization": f"Bearer {settings['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings["model"],
        "messages": [
            {"role": "system", "content": "You return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=settings["timeout"],
    )
    if response.status_code == 400 and "response_format" in response.text:
        payload.pop("response_format", None)
        response = requests.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=settings["timeout"],
        )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_ollama(prompt, settings):
    base_url = (settings["base_url"] or "http://localhost:11434").rstrip("/")
    response = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": settings["model"],
            "messages": [
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        },
        timeout=settings["timeout"],
    )
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


def enrich_vulnerabilities_with_reasoning(target, repository_status, vulnerabilities):
    fallback_items = [_fallback_reasoning(item) for item in vulnerabilities]
    settings = _get_llm_settings()
    if not vulnerabilities:
        return fallback_items, {
            "enabled": False,
            "provider": settings["provider"] or "fallback",
            "model": settings["model"] if settings["provider"] else "",
            "error": "",
        }

    provider = settings["provider"]
    if not provider:
        env_hint = (
            f"File .env belum ditemukan di {settings['env_file']}."
            if not settings["env_file_exists"]
            else f"File .env ditemukan di {settings['env_file']}, tetapi LLM_PROVIDER belum terisi."
        )
        return fallback_items, {
            "enabled": False,
            "provider": "fallback",
            "model": "",
            "error": f"{env_hint} Isi LLM_PROVIDER dan LLM_API_KEY/OPENAI_API_KEY.",
        }

    if provider in {"openai", "openai-compatible"} and not settings["api_key"]:
        return fallback_items, {
            "enabled": False,
            "provider": "fallback",
            "model": settings["model"],
            "error": f"Provider OpenAI dipilih, tetapi LLM_API_KEY atau OPENAI_API_KEY belum terbaca dari {settings['env_file']} atau environment variable.",
        }

    try:
        prompt = _build_prompt(target, repository_status, vulnerabilities[:20])
        if provider == "ollama":
            content = _call_ollama(prompt, settings)
        elif provider in {"openai", "openai-compatible"}:
            content = _call_openai_compatible(prompt, settings)
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

        llm_items = _parse_llm_items(content)
        enriched = []
        for index, item in enumerate(fallback_items):
            llm_item = llm_items.get(index, {})
            enriched.append({
                **item,
                "critical_area": llm_item.get("critical_area") or item["critical_area"],
                "severity_reason": llm_item.get("severity_reason") or item["severity_reason"],
                "priority": llm_item.get("priority") or item["priority"],
                "repair_steps": llm_item.get("repair_steps") or item["repair_steps"],
                "llm_used": index in llm_items,
                "reasoning_source": provider if index in llm_items else "fallback",
                "reasoning_error": "",
            })

        return enriched, {
            "enabled": True,
            "provider": provider,
            "model": settings["model"],
            "error": "",
        }
    except Exception as exc:
        return fallback_items, {
            "enabled": False,
            "provider": "fallback",
            "model": settings["model"],
            "error": f"LLM reasoning gagal, fallback lokal digunakan: {exc}",
        }
