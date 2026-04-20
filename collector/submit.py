#!/usr/bin/env python3
"""
PRAXIS Data Submission Tool
Generates anonymized ZIP and opens browser UI for easy submission.
No external dependencies — Python 3.8+ stdlib only.
"""

import http.server
import json
import os
import socket
import socketserver
import subprocess
import sys
import threading
import webbrowser
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs

# ── Config ──────────────────────────────────────────────────────
KIT_DIR = Path(__file__).resolve().parent
PRAXIS_DIR = None  # Found at runtime
PARTICIPANT_ID = "unknown"
EMAIL_TO = "hello@javierherreros.xyz"
EMAIL_SUBJECT = ""

# ── Helpers ─────────────────────────────────────────────────────

def find_praxis_dir():
    """Walk up from cwd to find .praxis/ directory."""
    p = Path.cwd()
    for _ in range(20):
        if (p / ".praxis").is_dir():
            return p / ".praxis"
        if p.parent == p:
            break
        p = p.parent
    return None


def get_machine_id():
    """Generate a short, stable machine identifier (NOT the MAC address for privacy)."""
    import hashlib
    try:
        # Combine hostname + username for a stable but not uniquely identifying hash
        raw = f"{os.uname().nodename if hasattr(os, 'uname') else os.getenv('COMPUTERNAME', 'pc')}-{os.getenv('USERNAME', os.getenv('USER', 'user'))}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]
    except Exception:
        return "unknown"


def generate_zip(praxis_dir: Path) -> dict:
    """Generate anonymized ZIP from .praxis/ data."""
    global PARTICIPANT_ID, EMAIL_SUBJECT

    mid = get_machine_id()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"praxis_data_{mid}_{timestamp}.zip"
    output_path = praxis_dir.parent / zip_name

    # Load participant ID
    state_file = praxis_dir / "state.json"
    if state_file.exists():
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            PARTICIPANT_ID = state.get("participant_id", mid)
        except Exception:
            PARTICIPANT_ID = mid
    else:
        PARTICIPANT_ID = mid

    EMAIL_SUBJECT = f"PRAXIS data submission [{PARTICIPANT_ID}]"

    files_added = 0
    errors = []

    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add all .jsonl and .json files (metrics, incidents)
            for pattern in ["*.jsonl", "*.json"]:
                for f in praxis_dir.glob(pattern):
                    # Skip any file with "raw" in name for extra safety
                    if "raw" not in f.name.lower():
                        zf.write(f, f.name)
                        files_added += 1

            # Add survey responses
            surveys_dir = praxis_dir / "surveys"
            if surveys_dir.exists():
                for f in surveys_dir.glob("*.json"):
                    zf.write(f, f"surveys/{f.name}")
                    files_added += 1

            # Add metadata
            meta = {
                "participant_id": PARTICIPANT_ID,
                "export_timestamp": datetime.now().isoformat(),
                "kit_version": "0.2.0",
                "files_included": files_added,
            }
            zf.writestr("_meta.json", json.dumps(meta, indent=2))

        return {
            "success": True,
            "zip_path": str(output_path),
            "zip_name": zip_name,
            "files_added": files_added,
            "participant_id": PARTICIPANT_ID,
            "folder_path": str(output_path.parent),
        }

    except Exception as e:
        return {"success": False, "error": str(e), "zip_path": None}


# ── HTTP Server ─────────────────────────────────────────────────

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PRAXIS — Submit Your Data</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0d1117; color: #e6edf3; display: flex; justify-content: center;
         align-items: center; min-height: 100vh; padding: 20px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 12px;
          padding: 40px; max-width: 500px; width: 100%; text-align: center; }
  .logo { font-size: 28px; margin-bottom: 8px; }
  h1 { font-size: 20px; margin-bottom: 24px; color: #e6edf3; }
  .status-box { padding: 20px; border-radius: 8px; margin-bottom: 20px; }
  .status-success { background: #0d2818; border: 1px solid #238636; }
  .status-error { background: #2d1215; border: 1px solid #da3633; }
  .status-icon { font-size: 48px; margin-bottom: 8px; }
  .status-text { font-size: 16px; line-height: 1.5; }
  .detail { color: #8b949e; font-size: 13px; margin-top: 12px; }
  .detail code { background: #21262d; padding: 2px 6px; border-radius: 4px; color: #79c0ff; }
  .btn { display: inline-block; padding: 12px 24px; border-radius: 8px; border: none;
         font-size: 15px; font-weight: 600; cursor: pointer; margin: 6px; text-decoration: none;
         color: white; transition: opacity 0.2s; }
  .btn:hover { opacity: 0.85; }
  .btn-primary { background: #238636; }
  .btn-secondary { background: #30363d; border: 1px solid #484f58; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .log { background: #0d1117; border: 1px solid #21262d; border-radius: 6px;
         padding: 12px; font-family: monospace; font-size: 12px; text-align: left;
         color: #8b949e; margin-top: 16px; max-height: 120px; overflow-y: auto;
         display: none; }
  .log.visible { display: block; }
  .footer { color: #484f58; font-size: 11px; margin-top: 24px; }
</style>
</head>
<body>
<div class="card">
  <div class="logo">👑</div>
  <h1>PRAXIS Data Submission</h1>

  <div id="loading">Preparing your data...</div>

  <div id="success-box" class="status-box status-success" style="display:none">
    <div class="status-icon">[OK]</div>
    <div class="status-text">
      <strong>Your data is ready!</strong><br>
      <span id="file-info"></span>
    </div>
    <div class="detail">
      File: <code id="zip-name"></code><br>
      ID: <code id="participant-id"></code><br>
      Files included: <span id="file-count"></span>
    </div>
  </div>

  <div id="error-box" class="status-box status-error" style="display:none">
    <div class="status-icon">[ERROR]</div>
    <div class="status-text">
      <strong>Something went wrong</strong>
    </div>
  </div>

  <div id="actions" style="display:none; margin-top: 20px;">
    <a id="email-btn" class="btn btn-primary" href="#">📧 Open Email &amp; Attach File</a>
    <button id="folder-btn" class="btn btn-secondary" onclick="openFolder()">📁 Open Folder</button>
    <div class="detail" style="margin-top: 12px;">
      Click "Open Email" — your email app will open with the address pre-filled.<br>
      Then drag the ZIP file from the folder onto the email.
    </div>
  </div>

  <div id="log" class="log"></div>
  <div class="footer">PRAXIS Universal Kit v0.2 · Universidad Complutense de Madrid</div>
</div>

<script>
const result = __RESULT_JSON__;

window.addEventListener('load', () => {
  document.getElementById('loading').style.display = 'none';
  const log = document.getElementById('log');
  log.classList.add('visible');

  if (result.success) {
    document.getElementById('success-box').style.display = 'block';
    document.getElementById('actions').style.display = 'block';
    document.getElementById('zip-name').textContent = result.zip_name;
    document.getElementById('participant-id').textContent = result.participant_id;
    document.getElementById('file-count').textContent = result.files_added;
    log.textContent = 'OK ZIP generated: ' + result.zip_path + '\\nOK Files: ' + result.files_added + '\\nOK Ready to submit.';

    // Email button
    const subject = encodeURIComponent('PRAXIS data submission [' + result.participant_id + ']');
    const body = encodeURIComponent(
      'Hi,\\n\\nHere is my PRAXIS data submission.\\n\\nParticipant ID: ' + result.participant_id +
      '\\nFile: ' + result.zip_name +
      '\\n\\nPlease find the ZIP file attached.\\n\\nThank you!'
    );
    document.getElementById('email-btn').href = 'mailto:hello@javierherreros.xyz?subject=' + subject + '&body=' + body;
  } else {
    document.getElementById('error-box').style.display = 'block';
    log.textContent = '✗ Error: ' + (result.error || 'Unknown error');
  }
});

function openFolder() {
  fetch('/open-folder').then(() => {});
}
</script>
</body>
</html>"""


class SubmitHandler(http.server.BaseHTTPRequestHandler):
    """Tiny HTTP server to serve the submission page and handle actions."""

    result_data = {}

    def do_GET(self):
        if self.path == "/open-folder":
            # Open the folder containing the zip
            folder = self.result_data.get("folder_path", "")
            if folder:
                try:
                    if sys.platform == "win32":
                        os.startfile(folder)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", folder])
                    else:
                        subprocess.run(["xdg-open", folder])
                except Exception:
                    pass
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok")
            return

        # Serve the HTML page with result injected
        html = HTML_PAGE.replace("__RESULT_JSON__", json.dumps(self.result_data))
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Suppress server logs


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


# ── Main ────────────────────────────────────────────────────────

def main():
    global PRAXIS_DIR

    print("PRAXIS Data Submission Tool")
    print("=" * 40)

    # Find .praxis directory
    PRAXIS_DIR = find_praxis_dir()
    if PRAXIS_DIR is None:
        print("[ERROR] No PRAXIS project found. Run this from your project directory.")
        print("   (The directory must contain a .praxis/ folder)")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print(f"Found PRAXIS data at: {PRAXIS_DIR}")

    # Generate ZIP
    print("Generating anonymized ZIP...")
    result = generate_zip(PRAXIS_DIR)

    if result["success"]:
        print(f"[OK] ZIP created: {result['zip_name']}")
        print(f"   Files included: {result['files_added']}")
        print(f"   Participant ID: {result['participant_id']}")
    else:
        print(f"[ERROR] {result['error']}")

    # Prepare result for HTML
    SubmitHandler.result_data = result

    # Start local server and open browser
    port = find_free_port()
    server = http.server.HTTPServer(("127.0.0.1", port), SubmitHandler)

    print(f"\nOpening submission page in browser...")
    print(f"   If it doesn't open, go to: http://127.0.0.1:{port}")

    webbrowser.open(f"http://127.0.0.1:{port}")

    # Serve for 5 minutes, then auto-close
    print(f"   (This page will auto-close after 5 minutes)")

    timer = threading.Timer(300, server.shutdown)
    timer.daemon = True
    timer.start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

    print("\n[OK] Submission tool closed. Thank you!")


if __name__ == "__main__":
    main()
