# Phoenix Assist learning lab

This is a local simulation using fictional bank records. It does not contact a bank, make calls, record audio, or change a real card. The mock banking-app approval is a teaching aid, not identity verification.

## Run it

Use Python 3.10 or newer. From this folder:

```bash
python agent.py
python -m unittest -v
```

## Speak in a browser

Run `python web.py`, then open `http://127.0.0.1:8765`. Type a response or click **Speak** and allow microphone access. The browser reads the agent's replies aloud. Click **New case** to restart. Press Ctrl+C in the terminal to stop the server.

To try the trust gate: reply `yes`, open **Mock banking app** in its own tab, click **Approve this demo case** within two minutes, return to Phoenix Assist and click **Check approval**. Then enter `LOST`, `STATUS`, or `HUMAN`. Say `VERIFY` in the conversation first to see that it does not approve the case. A new case needs a new approval; an old approval cannot authorize it.

When the case ends, click **View case passport**. The local reviewer screen shows the consent and mock approval states, request type, simulated action, outcome, reason for handoff, and an event trail. It intentionally omits raw caller messages and the approval ID. A case must finish before its passport is available. This reviewer screen has no real staff authentication.

The microphone uses your browser's speech recognition, if it is available. Some browsers send audio to an online recognition service; this demo does not save audio. If speech recognition is unavailable, typed input still works. Browser voices differ by operating system. No ElevenLabs account or key is needed for this local lesson.

`web.py` listens only on your own computer and sends each message to the same `Case.reply()` function as the terminal app. The browser sends JSON to `/api/reply` and displays the response. This is how we keep the conversation rules in one place while changing the interface.

Choose **العربية** in the browser to start an Arabic case. Try `نعم`, approve it in the separate mock app, then enter `بطاقة مفقودة`, or `الحالة` for status. The dropdown also switches the browser speech language. Arabic pronunciation and recognition quality depend on voices and services available in your browser; typed Arabic always works.

If your Windows installation uses the Python launcher, use `py` in place of `python`.

The terminal version is useful for exploring consent and handoff. Use the browser version to try a simulated freeze, because approval must come through the separate mock screen.

## Lesson one: follow the state

`Stage` is the step of the conversation. `Case` stores what happened during one call. `reply()` reads one answer, checks the current step, changes the case, and returns the next line. The `main()` function handles keyboard input and output.

The critical rule lives in the REQUEST step: a temporary freeze is simulated only when `verified` is true and the caller says `LOST`. The `reply()` method cannot set `verified`; only `approve_mock_bank()` can. We log event names, not what the caller typed.

## Lesson two: a new request without changing the card

After verification, `LOST` sets `temporary_freeze` to `True`. `STATUS` only reads that value and reports the result. `HUMAN` sets `human_handoff` to `True`. A check that only reads data should not silently change data.

Look at the three branches inside `if self.stage is Stage.REQUEST:`. Each branch ends this simple demo after one request. This is useful for learning because you can trace each path from input to final state.

## Your small exercises

1. Change the greeting and run the program again. Which line changed?
2. Run `STATUS`, then inspect `status_checked` in the audit events.
3. Change `STATUS` to `CHECK` in the code and update its test too. What happens if you change only one of them?

Next we can connect this conversation to a voice interface and a mock API. A real deployment would need institution-approved verification, consent, security review, and precise language support.
