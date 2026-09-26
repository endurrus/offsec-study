# OSED Fast-Track — Practical Exploit Dev Study Kit

**Goal:** pass EXP-301 / OSED by *doing*, not reading. Everything here is copy-paste
ready, decision-driven, and built for short sessions. No wall-of-text theory —
just what you actually type at the keyboard on exam day.

> The 48-hour exam gives you 3 machines. You need muscle memory for the workflow,
> not encyclopedic recall. This kit trains the workflow.

---

## How to use this (pick your session length)

| You have… | Do this |
|-----------|---------|
| **5 min** | Open `dashboard.html` on your phone. Flip 5 flashcards from `04-drills/flashcards.csv`. |
| **15 min** | Read ONE playbook in `00-methodology/`. Trace the steps out loud. |
| **30 min** | Take a template from `02-templates/`, and rebuild it from memory in a blank file. |
| **60 min+** | Spin a vuln app in your lab, drive a full playbook end-to-end using only the cheatsheets. |

> **On your phone / away from the lab?** The same dashboard is published as a private
> Artifact you can open anywhere: **https://claude.ai/artifact/KN9bmAzFDwn4WN169wPfzS**
> (only you can open it). Or just open `dashboard.html` from this repo — it's fully offline.

The single most important habit: **never look at a full solution first.** Try the
step, get stuck, *then* peek. That struggle is what makes it stick.

---

## The map

```
00-methodology/   ← START HERE. Decision tree, 6 playbooks, troubleshooting guide.
01-cheatsheets/   ← The commands. WinDbg, mona, nasm, msfvenom, badchars, asm, IDA/RE.
02-templates/     ← Copy-paste Python exploit skeletons. Fill in the blanks.
03-shellcode/     ← Hand-rolled shellcode + how to assemble/extract it.
04-drills/        ← Flashcards, spaced-rep schedule, exam-day checklist.
05-labs/          ← Lab setup, ordered practice progression, full worked example.
dashboard.html    ← Everything above, browsable on a phone. Open it directly.
```

**Never done a full exploit start to finish?** Go straight to
`05-labs/vulnserver-trun-walkthrough.md` and build it in your lab. Seeing one complete
exploit, once, is worth ten pages of theory. Then follow `05-labs/practice-progression.md`.

## The 7 things OSED tests (and where to train each)

1. **WinDbg fluency** → `01-cheatsheets/windbg.md` + drill until commands are reflex
2. **Stack buffer overflow** → `00-methodology/stack-bof-playbook.md` + `02-templates/stack_bof.py`
3. **SEH overflow** → `00-methodology/seh-playbook.md` + `02-templates/seh_overflow.py`
4. **Egghunters (space constraints)** → `00-methodology/egghunter-playbook.md`
5. **DEP bypass with ROP** → `00-methodology/dep-rop-playbook.md` + `02-templates/dep_rop.py`
6. **ASLR bypass** → `00-methodology/aslr-bypass-playbook.md`
7. **Format string specifiers** → `00-methodology/format-string-playbook.md`
8. *(bonus)* **Custom shellcode / RE for bugs** → `03-shellcode/` + IDA notes in cheatsheets

## The universal loop (memorize this — it's every exploit)

```
1. FUZZ / crash it        → confirm you control the crash
2. FIND the offset        → pattern_create / pattern_offset  (or mona)
3. CONTROL the pointer     → EIP / nSEH+SEH / a saved return
4. FIND badchars          → send \x00..\xff, compare in memory
5. FIND a jump            → mona jmp/seh/rop  → a reliable address w/o badchars
6. GET space + stage       → egghunter? jump backwards? direct shellcode?
7. DEFEAT mitigations      → DEP→ROP, ASLR→leak/non-ASLR module
8. LAND shellcode          → align, decode if encoded, pop shell
```

Every playbook in `00-methodology/` is just this loop specialized. When you're lost
mid-exam, come back to these 8 steps and ask "which step am I on?"

---
_Study kit — keep it in your lab VM, keep it offline, make it yours._
