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

    def get(self, path, cookie=None):
        port = self.server.server_address[1]
        conn = http.client.HTTPConnection("127.0.0.1", port)
        conn.request("GET", path, headers={"Cookie": cookie} if cookie else {})
        response = conn.getresponse()
        result = response.status, response.read().decode("utf-8")
        conn.close()
        return result

    def test_browser_case_preserves_state_and_protects_actions(self):
        status, initial, header = self.post("/api/new", {})
        self.assertEqual(status, 200)
        self.assertIn("Phoenix Assist", initial["message"])
        cookie = header.split(";", 1)[0]
        _, consent, _ = self.post("/api/reply", {"message": "yes"}, cookie)
        _, untrusted, _ = self.post("/api/reply", {"message": "VERIFY"}, cookie)
        self.assertIn("waiting", untrusted["message"].lower())
        status, approved, _ = self.post("/api/mock-approve", {"approval_id": consent["approval_id"]}, cookie)
        self.assertEqual(status, 200)
        self.assertTrue(approved["approved"])
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

    def test_browser_arabic_case(self):
        status, initial, header = self.post("/api/new", {"language": "ar"})
        self.assertEqual(status, 200)
        self.assertIn("مرحباً", initial["message"])
        cookie = header.split(";", 1)[0]
        _, consent, _ = self.post("/api/reply", {"message": "نعم"}, cookie)
        self.post("/api/reply", {"message": "تحقق"}, cookie)
        self.post("/api/mock-approve", {"approval_id": consent["approval_id"]}, cookie)
        status, result, _ = self.post("/api/reply", {"message": "الحالة"}, cookie)
        self.assertEqual(status, 200)
        self.assertIn("لا يوجد تجميد", result["message"])
        self.assertNotIn("temporary_freeze_simulated", result["events"])

    def test_approval_is_bound_to_its_case(self):
        _, _, first_header = self.post("/api/new", {})
        first = first_header.split(";", 1)[0]
        _, first_consent, _ = self.post("/api/reply", {"message": "yes"}, first)
        _, _, second_header = self.post("/api/new", {})
        second = second_header.split(";", 1)[0]
        _, second_consent, _ = self.post("/api/reply", {"message": "yes"}, second)
        self.post("/api/mock-approve", {"approval_id": first_consent["approval_id"]}, first)
        status, _, _ = self.post("/api/mock-approve", {"approval_id": first_consent["approval_id"]}, second)
        self.assertEqual(status, 409)
        self.assertNotEqual(first_consent["approval_id"], second_consent["approval_id"])
        status, state, _ = self.post("/api/reply", {"message": "LOST"}, second)
        self.assertEqual(status, 200)
        self.assertFalse(state["done"])
        self.assertNotIn("temporary_freeze_simulated", state["events"])

    def test_bank_page_accepts_case_link(self):
        port = self.server.server_address[1]
        conn = http.client.HTTPConnection("127.0.0.1", port)
        conn.request("GET", "/bank?case=example")
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        conn.close()
        self.assertEqual(response.status, 200)
        self.assertIn("Mock banking app", body)

    def test_passport_requires_completed_case_and_contains_outcome(self):
        _, _, header = self.post("/api/new", {})
        cookie = header.split(";", 1)[0]
        status, _ = self.get("/api/passport", cookie)
        self.assertEqual(status, 409)
        self.post("/api/reply", {"message": "no"}, cookie)
        status, raw = self.get("/api/passport", cookie)
        self.assertEqual(status, 200)
        passport = json.loads(raw)
        self.assertEqual(passport["outcome"], "consent_declined")
        self.assertEqual(passport["action"], "none")
        status, page = self.get("/review", cookie)
        self.assertEqual(status, 200)
        self.assertIn("Demo case passport", page)


if __name__ == "__main__":
    unittest.main()
