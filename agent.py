"""A text prototype of a voice agent using fictional records only."""

from dataclasses import dataclass, field
from enum import Enum, auto
import time
import secrets


APPROVAL_WINDOW_SECONDS = 120


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
        "verification": "Approve this case in the separate mock banking-app screen. Words spoken here cannot verify you. Never enter a PIN, password, or one-time code here.",
        "waiting": "Still waiting for approval in the mock banking app. You can also say HUMAN for a person.",
        "expired": "The mock approval window expired. I will refer this case to a person.",
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
        "verification": "وافق على هذه الحالة في شاشة تطبيق البنك التجريبي المنفصلة. الكلام هنا لا يثبت هويتك. لا تذكر رمزك السري أو كلمة المرور أو رمز التحقق.",
        "waiting": "ما زلنا ننتظر الموافقة في تطبيق البنك التجريبي. يمكنك قول موظف للتحدث إلى شخص.",
        "expired": "انتهت مدة الموافقة التجريبية. سأحيل الحالة إلى موظف.",
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
    challenged_at: float | None = None
    approval_id: str | None = None

    def __post_init__(self) -> None:
        if self.language not in LINES:
            raise ValueError("Unsupported language")

    def approve_mock_bank(self, approval_id: str, now: float | None = None) -> bool:
        """Simulate approval from a separate mock bank app, never from caller text."""
        if (self.stage is not Stage.VERIFY or self.challenged_at is None
                or self.approval_id is None or approval_id != self.approval_id):
            return False
        elapsed = (time.monotonic() if now is None else now) - self.challenged_at
        if elapsed < 0 or elapsed > APPROVAL_WINDOW_SECONDS:
            self.stage = Stage.DONE
            self.human_handoff = True
            self.audit.append("mock_approval_expired_handoff")
            return False
        self.verified = True
        self.approval_id = None
        self.stage = Stage.REQUEST
        self.audit.append("mock_bank_approval")
        return True

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
            self.challenged_at = time.monotonic()
            self.approval_id = secrets.token_urlsafe(16)
            self.audit.append("consent_granted")
            return line["verification"]

        if self.stage is Stage.VERIFY:
            if answer in ("human", "موظف"):
                self.stage = Stage.DONE
                self.human_handoff = True
                self.audit.append("human_handoff_requested")
                return line["verify_failed"]
            if time.monotonic() - self.challenged_at > APPROVAL_WINDOW_SECONDS:
                self.stage = Stage.DONE
                self.human_handoff = True
                self.audit.append("mock_approval_expired_handoff")
                return line["expired"]
            return line["waiting"]

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
