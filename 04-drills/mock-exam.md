# Mock Exam — simulate the pressure before it's real

The OSED exam is 48 hours, points-based. You don't rise to the occasion; you fall to your
level of practice. Run these mocks so exam day is just another rep. Do them in your lab on
targets you're authorized to test.

## How to run a mock
1. Pick targets you've **never exploited** (fresh VulnHub box, an exploit-db app with the
   writeup hidden, or a lab app with mitigations toggled).
2. Set a **hard clock**. Phone timer, visible.
3. Allowed: these cheatsheets + `QUICK-REFERENCE.md`. **Not** allowed: walkthroughs,
   writeups, prior solutions.
4. Screenshot as you go (you're also practicing the report).
5. Score yourself with the rubric below. Log weaknesses in `spaced-repetition.md`.

---

## Mock A — "warm-up single" (3 hours)
One target, DEP off, straightforward stack BOF or SEH.
- [ ] Crash found & classified correctly (decision tree) — **10 pts**
- [ ] Offset + control proven (int3 breaks where expected) — **20 pts**
- [ ] Badchars fully enumerated — **15 pts**
- [ ] Reliable jump/gadget chosen (non-ASLR, clean) — **15 pts**
- [ ] Shell / code exec achieved — **30 pts**
- [ ] Reproducible notes + proof screenshots — **10 pts**

**Pass = 80+.** Under 3h with a shell and clean notes = you're on track.

## Mock B — "mitigations on" (5 hours)
One target with **DEP on** (and ASLR if you can arrange it).
- [ ] Correctly identify DEP from `mona mod` — **10 pts**
- [ ] Working ROP chain to VirtualProtect (single-stepped & understood) — **35 pts**
- [ ] ASLR handled (non-ASLR module or leak+RVA) if present — **20 pts**
- [ ] Shell / code exec — **25 pts**
- [ ] Reproducible notes + proof — **10 pts**

**Pass = 80+.** If you can't finish in 5h, note exactly which step ate the time.

## Mock C — "the 48h simulation" (full weekend, optional but gold)
Three targets of mixed difficulty across two days. Rules that mirror the real thing:
- [ ] Budget: no more than ~5h on any one target in the first pass — bank points, move on.
- [ ] **Sleep.** Schedule a real sleep block. Fatigue debugging is negative-productivity.
- [ ] Reserve the final 6–8h for the **report only**.
- [ ] Every exploit: full code saved, every address/offset noted, proof screenshots.

Scoring: sum each target with Mock A/B rubrics; set your own pass line (the real exam
publishes a threshold — practice clearing it with margin).

---

## The self-scoring rubric (apply to any target)
| Area | What "full marks" looks like |
|---|---|
| **Triage** | Ran the 4 commands, classified in <5 min, picked the right playbook |
| **Control** | Proved it with int3 before touching real shellcode |
| **Badchars** | Enumerated methodically; none missed (no silent truncation) |
| **Reliability** | Jump/gadgets from non-ASLR modules; works on repeat runs |
| **Mitigations** | Identified from `mona mod`; defeated the right way, understood why |
| **Payload** | Correct msfvenom flags (-b, EXITFUNC=thread); shell is stable |
| **Report** | A stranger could reproduce it from your notes alone |

## Time-sink log (fill after every mock — this IS your study plan)
```
Target: __________   Time: ____   Result: shell / stuck at: __________
Where the clock went:
  - ____ min on: __________________
  - ____ min on: __________________
Biggest lesson: ____________________
Drill to add to spaced-repetition.md: ____________________
```

## Reading your scores over time
- Triage/Control slow → drill the dashboard **Quiz** + flashcards; it's reflex, not knowledge.
- Badchars eating time → you're skipping the ritual; make it mechanical.
- ROP is the wall → do `05-labs/dep-rop-walkthrough.md` until you can single-step blind.
- Report always rushed → screenshot *as you go*, not at the end.

The graduation signal: **Mock B passed, under time, on a target you'd never seen.** When
that's repeatable, the real exam is just a longer version of a thing you already do.
