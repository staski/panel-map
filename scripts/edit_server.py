#!/usr/bin/env python3
"""
edit_server.py — serve panelmap_editor.html with a cockpit image + areas.json
pre-loaded, and receive the edited areas.json back. The interactive step of the
automated pipeline (build_panel.sh).

The editor can't read local files over file://, so everything is served from
localhost: the editor auto-loads /image and /areas.json (announced by
/session.json), and its "Save" button POSTs the edited map to /save, which
writes it back to the areas.json path and stops the server — the signal for the
build to continue.

Usage:
  python3 scripts/edit_server.py --image cockpit.jpg --areas areas.json [--port 8765] [--no-open]

Exits 0 after a successful save; non-zero if interrupted before saving.
"""

import argparse
import http.server
import json
import mimetypes
import os
import socketserver
import sys
import threading
import webbrowser


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    p = argparse.ArgumentParser(description="Serve the panel-map editor pre-loaded, save the result back.")
    p.add_argument("--editor", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "panelmap_editor.html"))
    p.add_argument("--image", required=True, help="cockpit image to edit against")
    p.add_argument("--areas", required=True, help="areas.json to edit (overwritten on Save)")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-open", action="store_true", help="don't auto-open the browser")
    args = p.parse_args()

    for f in (args.editor, args.image, args.areas):
        if not os.path.isfile(f):
            sys.exit(f"edit_server: not found: {f}")

    saved = {"ok": False}
    img_ctype = mimetypes.guess_type(args.image)[0] or "application/octet-stream"

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass  # quiet

        def _send(self, code, ctype, body):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path in ("/", "/index.html", "/editor"):
                self._send(200, "text/html; charset=utf-8", open(args.editor, "rb").read())
            elif self.path == "/session.json":
                self._send(200, "application/json",
                           json.dumps({"image": "/image", "areas": "/areas.json", "save": "/save"}).encode())
            elif self.path == "/image":
                self._send(200, img_ctype, open(args.image, "rb").read())
            elif self.path in ("/areas.json", "/areas"):
                self._send(200, "application/json", open(args.areas, "rb").read())
            else:
                self._send(404, "text/plain", b"not found")

        def do_POST(self):
            if self.path != "/save":
                self._send(404, "text/plain", b"not found")
                return
            n = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(n)
            try:
                json.loads(body)                       # must be valid JSON
            except Exception as e:
                self._send(400, "text/plain", ("invalid JSON: " + str(e)).encode())
                return
            with open(args.areas, "wb") as fh:
                fh.write(body)
            saved["ok"] = True
            self._send(200, "application/json", b'{"status":"saved"}')
            threading.Thread(target=self.server.shutdown, daemon=True).start()

    # bind (retry a few ports if the default is busy)
    httpd = None
    for port in range(args.port, args.port + 10):
        try:
            httpd = Server(("127.0.0.1", port), H)
            break
        except OSError:
            continue
    if httpd is None:
        sys.exit(f"edit_server: no free port in {args.port}..{args.port + 9}")

    url = f"http://127.0.0.1:{httpd.server_address[1]}/"
    print(f"edit_server: editing {args.areas}")
    print(f"edit_server: {url}  — press Save in the editor to continue the build")
    if not args.no_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

    if saved["ok"]:
        print(f"edit_server: saved {args.areas}")
        sys.exit(0)
    print("edit_server: no save received (interrupted)", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
