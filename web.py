"""Local browser interface for the fictional Phoenix Assist case."""

from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
from urllib.parse import urlsplit

from agent import Case, LINES, Stage


PAGE = Path(__file__).with_name("index.html").read_bytes()
BANK_PAGE = Path(__file__).with_name("bank.html").read_bytes()
REVIEW_PAGE = Path(__file__).with_name("review.html").read_bytes()
SESSIONS: dict[str, Case] = {}
MAX_BODY = 4096


class Handler(BaseHTTPRequestHandler):
    def current_case(self) -> Case | None:
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
            return SESSIONS.get(cookies["session"].value)
        except (KeyError, ValueError):
            return None

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
        path = urlsplit(self.path).path
        if path == "/api/state":
            case = self.current_case()
            if case is None:
                self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Start a new case"})
                return
            self.respond_json(HTTPStatus.OK, {
                "approved": case.verified,
                "done": case.stage is Stage.DONE,
                "message": LINES[case.language]["request"] if case.verified else "",
            })
            return
        if path == "/api/passport":
            case = self.current_case()
            if case is None:
                self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Start a new case"})
            elif case.stage is not Stage.DONE:
                self.respond_json(HTTPStatus.CONFLICT, {"error": "The case has not ended"})
            else:
                self.respond_json(HTTPStatus.OK, case.passport())
            return
        if path not in ("/", "/bank", "/review"):
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        page = {"/": PAGE, "/bank": BANK_PAGE, "/review": REVIEW_PAGE}[path]
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(page)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(page)

    def do_POST(self) -> None:
        if self.path not in ("/api/new", "/api/reply", "/api/mock-approve"):
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
            language = payload.get("language", "en")
            if language not in ("en", "ar"):
                self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Unsupported language"})
                return
            token = secrets.token_urlsafe(32)
            case = Case(language=language)
            SESSIONS[token] = case
            message = case.reply("start")
            self.respond_json(HTTPStatus.OK, {"message": message, "done": False}, token)
            return

        case = self.current_case()
        if case is None:
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Start a new case"})
            return
        if self.path == "/api/mock-approve":
            approval_id = payload.get("approval_id")
            if isinstance(approval_id, str) and case.approve_mock_bank(approval_id):
                self.respond_json(HTTPStatus.OK, {"approved": True, "message": LINES[case.language]["request"]})
            else:
                self.respond_json(HTTPStatus.CONFLICT, {"error": "Wrong case, approval already used, or approval expired"})
            return
        message = payload.get("message")
        if not isinstance(message, str) or len(message) > 300:
            self.respond_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid case or message"})
            return
        reply = case.reply(message)
        self.respond_json(HTTPStatus.OK, {
            "message": reply,
            "done": case.stage is Stage.DONE,
            "approval_id": case.approval_id if case.stage is Stage.VERIFY else None,
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
