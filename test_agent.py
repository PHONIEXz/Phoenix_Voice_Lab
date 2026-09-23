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


if __name__ == "__main__":
    unittest.main()
