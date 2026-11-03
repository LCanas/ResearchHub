"""Share the demo publicly via a Cloudflare quick tunnel — no account, no IT.

What it does:
  1. makes sure the database is seeded,
  2. serves the production app locally (waitress),
  3. opens a Cloudflare tunnel to it (a public https URL),
  4. writes a QR code for that URL to `demo_qr.png`.

Show the QR code (or share the URL). Anyone who scans it reaches the live demo
**while this window stays open and your PC is on**. The URL is new each run.

Run:    python share_demo.py       (press Ctrl+C to stop sharing)
Login:  s.cooper@kcl.ac.uk / password123
"""
import os
import re
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED = os.path.join(HERE, "cloudflared.exe")
PORT = 8000


def _serve():
    from waitress import serve
    import wsgi
    serve(wsgi.app, host="127.0.0.1", port=PORT)


def _announce(url):
    import qrcode
    # Write the URL to a file first (flushes immediately, unlike buffered stdout).
    with open(os.path.join(HERE, "demo_url.txt"), "w", encoding="utf-8") as f:
        f.write(url + "\n")
    out = os.path.join(HERE, "demo_qr.png")
    qrcode.make(url).save(out)
    bar = "=" * 66
    print("\n" + bar, flush=True)
    print("  PUBLIC DEMO URL:   " + url, flush=True)
    print("  QR CODE SAVED TO:  " + out, flush=True)
    print("  LOGIN:             s.cooper@kcl.ac.uk  /  password123", flush=True)
    print(bar, flush=True)
    print("  Show the QR code (open demo_qr.png). Keep this window open and your",
          flush=True)
    print("  PC awake during the demo. Press Ctrl+C here to stop sharing.",
          flush=True)
    print(bar + "\n", flush=True)


def main():
    if not os.path.exists(CLOUDFLARED):
        sys.exit("cloudflared.exe not found next to this script.")

    # 1. Ensure the database exists and is seeded.
    import init_db
    init_db.main()

    # 2. Start the local production server in the background.
    threading.Thread(target=_serve, daemon=True).start()
    time.sleep(2)
    print(f"Local server running on http://127.0.0.1:{PORT}")

    # 3. Open the Cloudflare tunnel and watch its output for the public URL.
    print("Opening Cloudflare tunnel… (this can take ~10 seconds)")
    proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    url = None
    try:
        for line in proc.stdout:
            if url is None:
                m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
                if m:
                    url = m.group(0)
                    _announce(url)
        proc.wait()
    except KeyboardInterrupt:
        print("\nStopping tunnel…")
    finally:
        try:
            proc.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    main()
