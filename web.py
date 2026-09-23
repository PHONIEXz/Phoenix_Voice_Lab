"""Local browser interface for the fictional Phoenix Assist case."""

from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets

from agent import Case, Stage


PAGE = Path(__file__).with_name("index.html").read_bytes()
SESSIONS: dict[str, Case] = {}
MAX_BODY = 4096


class Handler(BaseHTTPRequestHandler):
    def respond_json(self, status: HTTPStatus, body: dict, cookie: str = "") -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if cookie:
            self.send_header("Set-Cookie", f"session={cookie}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        if self.path != "/":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(PAGE)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(PAGE)

    def do_POST(self) -> None:
        if self.path not in ("/api/new", "/api/reply"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        # Only requests from this local page are accepted by the demo server.
        origin = self.headers.get("Origin")
        expected = f"http://{self.headers.get('Host', '')}"
        if origin != expected or self.headers.get("Content-Type") != "application/json":
            self.respond_json(HTTPStatus.FORBIDDEN, {"error": "Invalid request origin or type"})
            return
        try:
            size = int(self.headers.get("Content-Length", ""))
            if not 0 <= size <= MAX_BODY:
                raise ValueError("Request too large")
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError("Expected object")
        except (ValueError, json.JSONDecodeError):
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid request"})
            return

        if self.path == "/api/new":
            token = secrets.token_urlsafe(32)
            case = Case()
            SESSIONS[token] = case
            message = case.reply("start")
            self.respond_json(HTTPStatus.OK, {"message": message, "done": False}, token)
            return

        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
            token = cookies["session"].value
        except (KeyError, ValueError):
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Start a new case"})
            return
        case = SESSIONS.get(token)
        message = payload.get("message")
        if case is None or not isinstance(message, str) or len(message) > 300:
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid case or message"})
            return
        reply = case.reply(message)
        self.respond_json(HTTPStatus.OK, {
            "message": reply,
            "done": case.stage is Stage.DONE,
            "events": case.audit if case.stage is Stage.DONE else [],
        })


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Open http://127.0.0.1:8765 in your browser. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
