"""Generate a QR code PNG for a URL (e.g. your deployed Render URL).

Usage:   python make_qr.py https://collab-hub-xxxx.onrender.com
Writes:  demo_qr.png   (show/print this so people can scan it)
"""
import sys
import qrcode


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else input("URL: ").strip()
    if not url:
        sys.exit("No URL given.")
    qrcode.make(url).save("demo_qr.png")
    print(f"Saved demo_qr.png for {url}")


if __name__ == "__main__":
    main()
