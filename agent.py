"""A text prototype of a voice agent using fictional records only."""

from dataclasses import dataclass, field
from enum import Enum, auto


class Stage(Enum):
    START = auto()
    CONSENT = auto()
    VERIFY = auto()
    REQUEST = auto()
    DONE = auto()


LINES = {
    "en": {
        "greeting": "Hello, I'm Phoenix Assist, a demo AI for a fictional bank. This demo records an event log. Continue? (yes/no)",
        "declined": "Understood. Ending the demo without recording your request.",
        "verification": "For this demo, type VERIFY to simulate approval in a separate banking app. Never enter a PIN, password, or one-time code here.",
        "verify_failed": "Verification was not completed. I will refer this case to a person.",
        "request": "Verification simulated. Say LOST to request a temporary card freeze, STATUS to check this demo case, or HUMAN to speak to a person.",
        "frozen": "A temporary freeze was simulated on the fictional card. A person must review any permanent card action.",
        "status": "No temporary freeze has been applied to this fictional card.",
        "handoff": "I will refer this case to a person. No card action was taken.",
        "done": "This demo case has ended. Start a new case for another request.",
    },
    "ar": {
        "greeting": "مرحباً، أنا فينيكس أسيست، مساعد تجريبي لبنك افتراضي. تسجل هذه التجربة أحداثاً فقط. هل تريد المتابعة؟ (نعم/لا)",
        "declined": "حسناً. انتهت التجربة دون تسجيل طلبك.",
        "verification": "في هذه التجربة، قل تحقق لمحاكاة الموافقة في تطبيق البنك. لا تذكر رمزك السري أو كلمة المرور أو رمز التحقق هنا.",
        "verify_failed": "لم تكتمل المحاكاة. سأحيل هذه الحالة إلى موظف.",
        "request": "اكتملت محاكاة التحقق. قل بطاقة مفقودة لتجميد مؤقت تجريبي، أو الحالة للاستعلام، أو موظف للتحدث إلى شخص.",
        "frozen": "تمت محاكاة تجميد مؤقت للبطاقة الافتراضية. يراجع الموظف أي إجراء دائم.",
        "status": "لا يوجد تجميد مؤقت على البطاقة الافتراضية.",
        "handoff": "سأحيل الحالة إلى موظف. لم يتم اتخاذ أي إجراء على البطاقة.",
        "done": "انتهت هذه الحالة التجريبية. ابدأ حالة جديدة لطلب آخر.",
    },
}


@dataclass
class Case:
    language: str = "en"
    stage: Stage = Stage.START
    verified: bool = False
    temporary_freeze: bool = False
    human_handoff: bool = False
    audit: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.language not in LINES:
            raise ValueError("Unsupported language")

    def reply(self, message: str) -> str:
        """Process a caller message and return the next spoken line."""
        answer = message.strip().lower()
        words = {
            "نعم": "yes", "لا": "no", "تحقق": "verify",
            "بطاقة مفقودة": "lost", "مفقودة": "lost",
            "الحالة": "status", "موظف": "human",
        }
        answer = words.get(answer, answer)
        line = LINES[self.language]
        # The audit records events, never the caller's raw message.
        if self.stage is Stage.START:
            self.stage = Stage.CONSENT
            self.audit.append("agent_disclosed_and_recording_requested")
            return line["greeting"]

        if self.stage is Stage.CONSENT:
            if answer != "yes":
                self.stage = Stage.DONE
                self.audit.append("consent_declined")
                return line["declined"]
            self.stage = Stage.VERIFY
            self.audit.append("consent_granted")
            return line["verification"]

        if self.stage is Stage.VERIFY:
            if answer != "verify":
                self.stage = Stage.DONE
                self.human_handoff = True
                self.audit.append("verification_failed_handoff")
                return line["verify_failed"]
            self.verified = True
            self.stage = Stage.REQUEST
            self.audit.append("mock_verification_success")
            return line["request"]

        if self.stage is Stage.REQUEST:
            self.stage = Stage.DONE
            if answer == "lost" and self.verified:
                self.temporary_freeze = True
                self.audit.append("temporary_freeze_simulated")
                return line["frozen"]
            if answer == "status" and self.verified:
                self.audit.append("status_checked")
                return line["status"]
            self.human_handoff = True
            self.audit.append("human_handoff_requested")
            return line["handoff"]

        return line["done"]


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
