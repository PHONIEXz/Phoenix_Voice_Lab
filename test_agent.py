import unittest

from agent import Case, Stage


class AgentTests(unittest.TestCase):
    def test_consent_declined_ends_without_action(self):
        case = Case()
        case.reply("start")
        case.reply("no")
        self.assertEqual(case.stage, Stage.DONE)
        self.assertFalse(case.temporary_freeze)

    def test_verification_failure_cannot_freeze_card(self):
        case = Case()
        case.reply("start")
        case.reply("yes")
        case.reply("lost")
        case.reply("lost")
        self.assertFalse(case.temporary_freeze)
        self.assertTrue(case.human_handoff)

    def test_verified_lost_card_can_simulate_temporary_freeze(self):
        case = Case()
        for text in ("start", "yes", "verify", "lost"):
            case.reply(text)
        self.assertTrue(case.temporary_freeze)
        self.assertFalse(case.human_handoff)
        self.assertEqual(case.stage, Stage.DONE)

    def test_raw_secret_is_never_logged(self):
        case = Case()
        case.reply("start")
        case.reply("yes")
        case.reply("1234")
        self.assertNotIn("1234", " ".join(case.audit))

    def test_status_does_not_change_card(self):
        case = Case()
        for text in ("start", "yes", "verify"):
            case.reply(text)
        response = case.reply("status")
        self.assertIn("No temporary freeze", response)
        self.assertFalse(case.temporary_freeze)
        self.assertFalse(case.human_handoff)

    def test_human_request_hands_off_without_card_action(self):
        case = Case()
        for text in ("start", "yes", "verify", "human"):
            case.reply(text)
        self.assertTrue(case.human_handoff)
        self.assertFalse(case.temporary_freeze)

    def test_arabic_lost_card_uses_same_guard(self):
        case = Case(language="ar")
        responses = [case.reply(text) for text in ("ابدأ", "نعم", "تحقق", "بطاقة مفقودة")]
        self.assertIn("مرحباً", responses[0])
        self.assertTrue(case.temporary_freeze)
        self.assertIn("تجميد", responses[-1])

    def test_arabic_unverified_caller_cannot_freeze(self):
        case = Case(language="ar")
        for text in ("ابدأ", "نعم", "بطاقة مفقودة"):
            case.reply(text)
        self.assertFalse(case.temporary_freeze)
        self.assertTrue(case.human_handoff)


if __name__ == "__main__":
    unittest.main()
