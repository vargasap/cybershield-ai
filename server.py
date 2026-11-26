#!/usr/bin/env python3
"""
CyberShield AI Independent Web Server & Bot Runner 🛡️
Serves the Multilingual IP Landing Page & Mini App, and runs the Telegram Bot in background.
"""

import os
import sys
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("PORT", 10000))

class CyberShieldWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Mini App route
        if self.path.startswith("/app") or self.path.startswith("/shield"):
            file_path = os.path.join(BASE_DIR, "shield.html")
            content_type = "text/html; charset=utf-8"
        # Health check
        elif self.path in ["/healthz", "/status"]:
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"online","service":"CyberShield AI"}')
            return
        # Avatar image
        elif self.path.startswith("/avatar"):
            file_path = os.path.join(BASE_DIR, "avatar.jpg")
            content_type = "image/jpeg"
        # Root Landing Page
        else:
            file_path = os.path.join(BASE_DIR, "index.html")
            content_type = "text/html; charset=utf-8"

        if os.path.exists(file_path):
            self.send_response(200)
            self.send_header("Content-type", content_type)
            self.end_headers()
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

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
    
    server = HTTPServer(("0.0.0.0", PORT), CyberShieldWebHandler)
    print(f"[{datetime.utcnow()}] CyberShield Web Server escuchando en puerto {PORT}...", flush=True)
    server.serve_forever()
