"""A text prototype of a voice agent using fictional records only."""

from dataclasses import dataclass, field
from enum import Enum, auto


class Stage(Enum):
    START = auto()
    CONSENT = auto()
    VERIFY = auto()
    REQUEST = auto()
    DONE = auto()


@dataclass
class Case:
    stage: Stage = Stage.START
    verified: bool = False
    temporary_freeze: bool = False
    human_handoff: bool = False
    audit: list[str] = field(default_factory=list)

    def reply(self, message: str) -> str:
        """Process a caller message and return the next spoken line."""
        answer = message.strip().lower()
        # The audit records events, never the caller's raw message.
        if self.stage is Stage.START:
            self.stage = Stage.CONSENT
            self.audit.append("agent_disclosed_and_recording_requested")
            return ("Hello, I'm Phoenix Assist, a demo AI for a fictional bank. "
                    "This demo records an event log. Continue? (yes/no)")

        if self.stage is Stage.CONSENT:
            if answer != "yes":
                self.stage = Stage.DONE
                self.audit.append("consent_declined")
                return "Understood. Ending the demo without recording your request."
            self.stage = Stage.VERIFY
            self.audit.append("consent_granted")
            return ("For this demo, type VERIFY to simulate approval in a separate "
                    "banking app. Never enter a PIN, password, or one-time code here.")

        if self.stage is Stage.VERIFY:
            if answer != "verify":
                self.stage = Stage.DONE
                self.human_handoff = True
                self.audit.append("verification_failed_handoff")
                return "Verification was not completed. I will refer this case to a person."
            self.verified = True
            self.stage = Stage.REQUEST
            self.audit.append("mock_verification_success")
            return ("Verification simulated. Say LOST to request a temporary card "
                    "freeze, or HUMAN to speak to a person.")

        if self.stage is Stage.REQUEST:
            self.stage = Stage.DONE
            if answer == "lost" and self.verified:
                self.temporary_freeze = True
                self.audit.append("temporary_freeze_simulated")
                return ("A temporary freeze was simulated on the fictional card. "
                        "A person must review any permanent card action.")
            self.human_handoff = True
            self.audit.append("human_handoff_requested")
            return "I will refer this case to a person. No card action was taken."

        return "This demo case has ended. Start a new case for another request."


def main() -> None:
    print("PHOENIX ASSIST | FICTIONAL BANK DEMO")
    case = Case()
    print("Agent:", case.reply("start"))
    while case.stage is not Stage.DONE:
        try:
            user_text = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nDemo ended.")
            return
        print("Agent:", case.reply(user_text))
    print("Audit events:", ", ".join(case.audit))


if __name__ == "__main__":
    main()
