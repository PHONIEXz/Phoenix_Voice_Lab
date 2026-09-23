# Phoenix Assist learning lab

This is a local text simulation using fictional bank records. It does not contact a bank, make calls, record audio, or change a real card. The words VERIFY and LOST are demo commands, not real authentication.

## Run it

Use Python 3.10 or newer. From this folder:

```bash
python agent.py
python -m unittest -v
```

If your Windows installation uses the Python launcher, use `py` in place of `python`.

Try a successful path by entering `yes`, `VERIFY`, `LOST`. Then restart and try `no`, or enter something other than `VERIFY`.

## Lesson one: follow the state

`Stage` is the step of the conversation. `Case` stores what happened during one call. `reply()` reads one answer, checks the current step, changes the case, and returns the next line. The `main()` function handles keyboard input and output.

The critical rule lives in the REQUEST step: a temporary freeze is simulated only when `verified` is true and the caller says `LOST`. The VERIFY step stands in for an external banking-app approval; typing VERIFY is not real identity verification. We log event names, not what the caller typed.

## Your small exercises

1. Change the greeting and run the program again. Which line changed?
2. Add a `STATUS` option after verification that says no freeze was applied.
3. Add a test showing `HUMAN` hands off without freezing.

Next we can connect this conversation to a voice interface and a mock API. A real deployment would need institution-approved verification, consent, security review, and precise language support.
