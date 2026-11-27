#!/usr/bin/env python3
"""
CyberShield AI Independent Web Server, Real Forensics REST API & Bot Runner
Serves index.html, shield.html, static assets, and real live REST scan endpoints.
"""

from __future__ import annotations

import base64
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import subprocess
import sys
import threading

import cybershield_engine as engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", 10000))
MAX_POST_BYTES = 20 * 1024 * 1024


class CyberShieldWebHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]

        if path == "/api/status":
            self._send_json(200, {"ok": True, **engine.get_api_status()})
            return

        if path in ("/healthz", "/status"):
            self._send_json(200, {"status": "online", "service": "CyberShield AI", "version": "2.5"})
            return

        if path.startswith("/app") or path.startswith("/shield"):
            file_path = os.path.join(BASE_DIR, "shield.html")
            content_type = "text/html; charset=utf-8"
        elif path.startswith("/avatar"):
            file_path = os.path.join(BASE_DIR, "avatar.jpg")
            content_type = "image/jpeg"
        elif path == "/robots.txt":
            file_path = os.path.join(BASE_DIR, "robots.txt")
            content_type = "text/plain; charset=utf-8"
        elif path == "/sitemap.xml":
            file_path = os.path.join(BASE_DIR, "sitemap.xml")
            content_type = "application/xml; charset=utf-8"
        else:
            file_path = os.path.join(BASE_DIR, "index.html")
            content_type = "text/html; charset=utf-8"

        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if not path.startswith("/api/"):
            self._send_json(404, {"error": "Endpoint no encontrado"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_POST_BYTES:
            self._send_json(400, {"error": "Payload vacío o demasiado grande"})
            return

        try:
            raw = self.rfile.read(length)
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "JSON inválido"})
            return

        try:
            if path == "/api/scan-url":
                res = engine.audit_url(body.get("url", ""))
                self._send_json(200, res)
            elif path == "/api/scan-crypto":
                res = engine.audit_crypto_address(body.get("address", ""))
                self._send_json(200, res)
            elif path == "/api/scan-message":
                res = engine.audit_message(body.get("text", ""))
                self._send_json(200, res)
            elif path == "/api/scan-hash":
                res = engine.audit_file_or_hash(hash_str=body.get("hash", ""))
                self._send_json(200, res)
            elif path == "/api/scan-receipt":
                b64 = body.get("image_base64", "")
                if "," in b64 and b64.startswith("data:"):
                    b64 = b64.split(",", 1)[1]
                img_bytes = base64.b64decode(b64)
                res = engine.audit_bank_receipt(
                    image_bytes=img_bytes,
                    filename=body.get("filename", "comprobante.png"),
                    include_b64_heatmap=True,
                )
                self._send_json(200, res)
            else:
                self._send_json(404, {"error": "API desconocida"})
        except Exception as e:
            self._send_json(500, {"error": f"Error en auditoría: {e}"})

    def log_message(self, format, *args):
        pass


def run_bot_worker():
    bot_script = os.path.join(BASE_DIR, "bot.py")
    if os.path.exists(bot_script):
        print(f"[{datetime.utcnow()}] Iniciando CyberShield Bot en segundo plano...", flush=True)
        subprocess.Popen([sys.executable, bot_script], cwd=BASE_DIR)


if __name__ == "__main__":
    t = threading.Thread(target=run_bot_worker, daemon=True)
    t.start()

    server = ThreadingHTTPServer(("0.0.0.0", PORT), CyberShieldWebHandler)
    print(f"[{datetime.utcnow()}] CyberShield Web + API Server escuchando en puerto {PORT}...", flush=True)
    server.serve_forever()
