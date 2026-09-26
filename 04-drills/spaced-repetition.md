# Spaced Repetition Plan (for people with no time)

The trick isn't more hours — it's hitting the same material at widening intervals so it
moves to long-term memory with minimal total time. This is built around ~20 min/day.

## Import the cards
`flashcards.csv` is Anki-ready (`front,back` header). In Anki:
`File > Import > flashcards.csv > Fields separated by Comma > map Field 1→Front,
Field 2→Back`. Study 10–15 new cards/day, review all due. That's it.

No Anki? Use the manual schedule below with the CSV as your question bank.

## The 2-week ramp (then maintenance)

| Day | New focus (15 min) | Review (5 min) |
|-----|--------------------|----------------|
| 1 | WinDbg triage + opcodes cards | — |
| 2 | mona commands cards | Day 1 |
| 3 | Stack BOF playbook (trace it) | Day 1–2 |
| 4 | SEH playbook (trace it) | Day 2–3 |
| 5 | Badchars ritual + assembly cards | Day 1, 3 |
| 6 | Egghunter playbook | Day 4–5 |
| 7 | **Rebuild stack_bof.py from memory** | all cards, quick |
| 8 | DEP/ROP playbook | Day 3, 6 |
| 9 | ASLR bypass playbook | Day 4, 8 |
| 10 | Format string playbook + cards | Day 5, 9 |
| 11 | Shellcode: assemble reverse_shell skeleton | Day 6, 8 |
| 12 | **Rebuild seh_overflow.py from memory** | all cards |
| 13 | Full run: pick a lab vuln app, stack BOF end-to-end | weak cards |
| 14 | Full run: SEH or DEP end-to-end | weak cards |
| 15+ | Maintenance: 1 full exploit run + due cards every 2–3 days | rotate |

## The "active recall" rule
Reading ≠ learning. For each playbook, after one read, **close it and write the 8 steps
from memory**. Check. The gap you find IS the thing you didn't actually know.

## The "blank file" drill (highest ROI)
Once a week, open an empty `.py` and rebuild a full exploit template from scratch:
- socket send + `p32` helper
- offset → EIP overwrite → JMP ESP → NOPs → shellcode
Time it. When you can do a stack BOF skeleton in <5 min without notes, that reflex is
exam-ready. Repeat for SEH, then DEP/ROP.

## Weakness log
Keep a running list here of the exact commands/steps you fumble. Drill ONLY these on
low-energy days:

```
- [ ] (example) I keep forgetting mona compare needs the .bin path AND -a address
- [ ]
- [ ]
```

## Energy-matched sessions
- **Tired / 5 min:** phone flashcards or `dashboard.html`. Passive-ish but counts.
- **Medium / 20 min:** one playbook + active recall write-up.
- **Fresh / 60 min:** blank-file drill or a full lab run. Do the hard thing when fresh.
