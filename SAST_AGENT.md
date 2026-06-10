# OJS SAST Agent

Project ini sekarang difokuskan sebagai scanner SAST untuk PKP OJS. Scanner berjalan sebagai agent/container pendamping OJS dan membaca source code OJS dari volume yang di-mount secara read-only.

## Arsitektur

- `ojs`: container aplikasi PKP OJS.
- `scanner-agent`: agent SAST berkala yang membaca `/ojs` dan menulis hasil ke `/scan-output/latest.json`.
- `scannerTrigger`: plugin generic OJS yang menulis trigger kecil saat halaman OJS dirender. Agent membaca trigger ini dan menjalankan scan di sidecar.
- `scanner-api`: API FastAPI untuk menjalankan scan manual, melihat history, dan membuat report PDF.
- `ojs-db`: database untuk OJS.

Scanner tidak lagi menjalankan Nuclei, Nikto, login OJS, crawling, atau pemeriksaan header HTTP. Fokusnya hanya analisis statis source OJS dan plugin.

## Plugin SAST Bawaan

Plugin/rule bawaan ada di `backend/services/ojs_scanner.py`:

- `config_security_plugin`: audit `config.inc.php`.
- `sensitive_file_plugin`: deteksi `.env`, dump SQL, backup, dan file sensitif.
- `risky_code_plugin`: deteksi pola fungsi PHP berisiko dan SQL injection sederhana.
- `source_hygiene_plugin`: deteksi `.git` pada root OJS.

Rule baru bisa ditambahkan sebagai fungsi dengan signature:

```python
def custom_plugin(context):
    return []
```

Lalu daftarkan ke `BUILTIN_PLUGINS`.

## Menjalankan Dengan Docker Compose

```bash
docker compose up --build
```

Endpoint API:

- OJS: `http://localhost:8080`
- Scanner API: `http://localhost:8000`

Scan manual:

```bash
curl -X POST http://localhost:8000/scan/ \
  -H "Content-Type: application/json" \
  -d "{\"internal_path\":\"/ojs\"}"
```

Untuk local tanpa Docker, gunakan path repo OJS:

```bash
curl -X POST http://localhost:8000/scan/ \
  -H "Content-Type: application/json" \
  -d "{\"internal_path\":\"ojs/ojs-main\"}"
```

## Konfigurasi Agent

Environment variable:

- `OJS_SOURCE_PATH`: path source OJS di dalam container. Default `/var/www/html` untuk agent, `/ojs` pada compose.
- `SCANNER_OUTPUT_PATH`: file output JSON agent. Default `/scan-output/latest.json`.
- `SCANNER_INTERVAL_SECONDS`: interval scan berkala. Default `300`.
- `SCANNER_ONESHOT`: `true` untuk scan sekali lalu exit.
- `SCANNER_WATCH_CHANGES`: `true` untuk scan otomatis saat path OJS sudah ter-mount atau file source berubah. Default `true`.
- `SCANNER_WATCH_INTERVAL_SECONDS`: interval pengecekan perubahan source saat watcher aktif. Default `5`.
- `SCANNER_TRIGGER_PATH`: path file trigger dari plugin OJS, contoh `/scan-trigger/ojs-page-trigger.json`.
- `OJS_SCANNER_TRIGGER_FILE`: path file trigger yang ditulis plugin OJS.
- `OJS_SCANNER_TRIGGER_THROTTLE_SECONDS`: jeda minimum antar trigger page-render. Default pada compose `60` agar scan tidak berjalan terlalu sering saat user berpindah halaman.

## Plugin OJS Page Trigger

Plugin `scannerTrigger` dicopy ke image OJS pada build dan tersedia di menu plugin OJS sebagai **OJS Scanner Trigger**.

Aktifkan plugin dari dashboard OJS. Setelah aktif, setiap render halaman OJS akan memperbarui file trigger bersama. `scanner-agent` mendeteksi perubahan file ini dan menjalankan scan otomatis. Nilai throttle bisa diatur ke `0` jika benar-benar ingin trigger setiap pindah halaman, tetapi ini bisa berat karena scan SAST membaca banyak file.
