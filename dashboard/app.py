#!/usr/bin/env python3
"""Webshare-style proxy list dashboard for the Coolify Telegram proxy stack."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.error
import urllib.request
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HOST = os.environ.get("DASHBOARD_BIND", "0.0.0.0")
PORT = int(os.environ.get("DASHBOARD_PORT", "3000"))
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET") or secrets.token_hex(32)
PUBLIC_HOST = os.environ.get("PROXY_PUBLIC_HOST", "127.0.0.1")
HTTP_PORT = int(os.environ.get("PROXY_HTTP_PORT", "8080"))
SOCKS_PORT = int(os.environ.get("PROXY_SOCKS_PORT", "1080"))
COUNTRY = os.environ.get("PROXY_COUNTRY", "—")
INTERNAL_PROXY_HOST = os.environ.get("INTERNAL_PROXY_HOST", "proxy")
INTERNAL_HTTP_PORT = int(os.environ.get("INTERNAL_HTTP_PORT", "8080"))
TEMPLATES = Path(__file__).resolve().parent / "templates"

_login_attempts: dict[str, list[float]] = {}


def _users() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(username: str, password: str) -> None:
        username = username.strip()
        password = password.strip()
        if not username or not password or username in seen:
            return
        seen.add(username)
        rows.append({"username": username, "password": password})

    add(os.environ.get("PROXY_USERNAME", ""), os.environ.get("PROXY_PASSWORD", ""))
    extra = os.environ.get("PROXY_USERS", "")
    if extra.strip():
        for pair in extra.split(","):
            pair = pair.strip()
            if ":" not in pair:
                continue
            user, password = pair.split(":", 1)
            add(user, password)
    return rows


def _proxy_records() -> list[dict]:
    records = []
    for index, user in enumerate(_users(), start=1):
        records.append(
            {
                "id": f"p-{index:02d}",
                "username": user["username"],
                "password": user["password"],
                "proxy_address": PUBLIC_HOST,
                "http_port": HTTP_PORT,
                "socks5_port": SOCKS_PORT,
                "country_code": COUNTRY,
                "valid": True,
                "protocols": ["HTTP", "SOCKS5"],
            }
        )
    return records


def _sign(value: str) -> str:
    sig = hmac.new(SESSION_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()
    return f"{value}.{sig}"


def _verify(token: str | None) -> bool:
    if not token or "." not in token:
        return False
    value, sig = token.rsplit(".", 1)
    expected = hmac.new(SESSION_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return False
    try:
        issued = int(value)
    except ValueError:
        return False
    return (time.time() - issued) < 60 * 60 * 24 * 7


def _rate_limited(ip: str) -> bool:
    now = time.time()
    window = [t for t in _login_attempts.get(ip, []) if now - t < 600]
    _login_attempts[ip] = window
    return len(window) >= 12


def _record_fail(ip: str) -> None:
    _login_attempts.setdefault(ip, []).append(time.time())


def _check_telegram() -> dict:
    users = _users()
    if not users:
        return {"ok": False, "error": "No proxy users configured"}
    user = users[0]
    proxy = f"http://{user['username']}:{user['password']}@{INTERNAL_PROXY_HOST}:{INTERNAL_HTTP_PORT}"
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": proxy, "https": proxy})
    )
    req = urllib.request.Request(
        "https://api.telegram.org/bot/getMe",
        headers={"User-Agent": "coolify-telegram-proxy/1.0"},
        method="GET",
    )
    started = time.time()
    try:
        with opener.open(req, timeout=15) as resp:
            status = resp.status
            body = resp.read(200).decode("utf-8", "replace")
    except urllib.error.HTTPError as err:
        status = err.code
        body = err.read(200).decode("utf-8", "replace")
        if status in (401, 404) or "ok" in body:
            return {
                "ok": True,
                "status": status,
                "ms": int((time.time() - started) * 1000),
                "detail": "Telegram Bot API reachable through HTTP proxy",
            }
        return {"ok": False, "status": status, "error": body[:180]}
    except Exception as err:  # noqa: BLE001
        return {"ok": False, "error": str(err)}
    return {
        "ok": True,
        "status": status,
        "ms": int((time.time() - started) * 1000),
        "detail": "Telegram Bot API reachable through HTTP proxy",
        "body": body[:120],
    }


def _render(name: str, **ctx: str) -> bytes:
    html = (TEMPLATES / name).read_text(encoding="utf-8")
    for key, value in ctx.items():
        html = html.replace(f"{{{{{key}}}}}", value)
    return html.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "CoolifyProxyDashboard/1.0"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003
        print(f"{self.address_string()} {fmt % args}")

    def _ip(self) -> str:
        return self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()

    def _authed(self) -> bool:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        morsel = cookie.get("cp_session")
        return _verify(morsel.value if morsel else None)

    def _set_cookie(self, headers: list[tuple[str, str]], token: str, max_age: int) -> None:
        headers.append(
            (
                "Set-Cookie",
                (
                    f"cp_session={token}; HttpOnly; Path=/; SameSite=Lax; Max-Age={max_age}"
                    + ("; Secure" if self.headers.get("X-Forwarded-Proto", "").lower() == "https" else "")
                ),
            )
        )

    def _send(self, code: int, body: bytes, content_type: str, extra: list[tuple[str, str]] | None = None) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        if extra:
            for key, value in extra:
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict | list) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._json(200, {"ok": True, "users": len(_users())})
            return
        if path == "/login":
            if self._authed():
                self._send(302, b"", "text/html; charset=utf-8", [("Location", "/")])
                return
            self._send(200, _render("login.html", error=""), "text/html; charset=utf-8")
            return
        if not self._authed():
            if path.startswith("/api/") or path.endswith(".txt"):
                self._json(401, {"ok": False, "error": "unauthorized"})
                return
            self._send(302, b"", "text/html; charset=utf-8", [("Location", "/login")])
            return
        if path == "/":
            self._send(200, _render("index.html"), "text/html; charset=utf-8")
            return
        if path == "/api/proxy/list":
            self._json(200, {"count": len(_proxy_records()), "results": _proxy_records()})
            return
        if path == "/api/status":
            self._json(200, _check_telegram())
            return
        if path == "/download.txt":
            lines = ["# HTTP  ip:port:username:password", "# SOCKS5  ip:port:username:password"]
            for row in _proxy_records():
                lines.append(
                    f"{row['proxy_address']}:{row['http_port']}:{row['username']}:{row['password']}"
                )
                lines.append(
                    f"{row['proxy_address']}:{row['socks5_port']}:{row['username']}:{row['password']}"
                )
            body = ("\n".join(lines) + "\n").encode("utf-8")
            self._send(
                200,
                body,
                "text/plain; charset=utf-8",
                [("Content-Disposition", 'attachment; filename="proxy-list.txt"')],
            )
            return
        self._send(404, b"Not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/login":
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(min(length, 4096)).decode("utf-8", "replace")
        password = (parse_qs(raw).get("password") or [""])[0]
        ip = self._ip()
        if not DASHBOARD_PASSWORD:
            self._send(
                200,
                _render("login.html", error="DASHBOARD_PASSWORD is not set on the server."),
                "text/html; charset=utf-8",
            )
            return
        if _rate_limited(ip):
            self._send(
                429,
                _render("login.html", error="Too many attempts. Try again in a few minutes."),
                "text/html; charset=utf-8",
            )
            return
        if not hmac.compare_digest(password, DASHBOARD_PASSWORD):
            _record_fail(ip)
            self._send(
                401,
                _render("login.html", error="Wrong password."),
                "text/html; charset=utf-8",
            )
            return
        token = _sign(str(int(time.time())))
        extra = [("Location", "/")]
        self._set_cookie(extra, token, 60 * 60 * 24 * 7)
        self._send(302, b"", "text/html; charset=utf-8", extra)


def main() -> None:
    if not DASHBOARD_PASSWORD:
        print("WARNING: DASHBOARD_PASSWORD is empty — login will be rejected.")
    if not _users():
        print("WARNING: no proxy users configured.")
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Dashboard listening on {HOST}:{PORT} public_host={PUBLIC_HOST}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
