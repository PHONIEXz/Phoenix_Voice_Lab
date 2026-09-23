import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from web import Handler


class BrowserFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def post(self, path, body, cookie=None, origin=None):
        port = self.server.server_address[1]
        conn = http.client.HTTPConnection("127.0.0.1", port)
        headers = {
            "Content-Type": "application/json",
            "Origin": origin or f"http://127.0.0.1:{port}",
        }
        if cookie:
            headers["Cookie"] = cookie
        conn.request("POST", path, json.dumps(body), headers)
        response = conn.getresponse()
        result = response.status, json.loads(response.read()), response.getheader("Set-Cookie")
        conn.close()
        return result

    def test_browser_case_preserves_state_and_protects_actions(self):
        status, initial, header = self.post("/api/new", {})
        self.assertEqual(status, 200)
        self.assertIn("Phoenix Assist", initial["message"])
        cookie = header.split(";", 1)[0]
        self.post("/api/reply", {"message": "yes"}, cookie)
        self.post("/api/reply", {"message": "VERIFY"}, cookie)
        status, result, _ = self.post("/api/reply", {"message": "STATUS"}, cookie)
        self.assertEqual(status, 200)
        self.assertTrue(result["done"])
        self.assertIn("No temporary freeze", result["message"])
        self.assertNotIn("temporary_freeze_simulated", result["events"])

    def test_reply_requires_own_case_and_local_origin(self):
        status, _, _ = self.post("/api/reply", {"message": "lost"})
        self.assertEqual(status, 400)
        status, _, _ = self.post("/api/new", {}, origin="https://elsewhere.example")
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
