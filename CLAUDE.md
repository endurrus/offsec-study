# CLAUDE.md — repo conventions for OSED Fast-Track

This repo is a **practical study kit** for the OffSec EXP-301 / OSED exam (Windows
user-mode exploit development, x86). It is documentation + templates, not an application.

## What this repo is
A learn-by-doing system: decision playbooks, command cheatsheets, copy-paste exploit
templates, drill material, lab walkthroughs, and an offline HTML dashboard.

## Structure
```
QUICK-REFERENCE.md   one-page essentials (the "pin to the wall" sheet)
README.md            master index + how-to-use-by-time-available
00-methodology/      decision tree, per-bug-class playbooks, troubleshooting
01-cheatsheets/      WinDbg, mona, nasm, msfvenom, badchars, x86 asm, IDA/RE
02-templates/        Python exploit skeletons + send_helpers.py
03-shellcode/        hand-rolled shellcode + build/extract workflow
04-drills/           flashcards.csv, spaced-repetition plan, exam-day checklist
05-labs/             lab setup, practice progression, VulnServer walkthroughs
dashboard.html       self-contained offline study console (also published as an Artifact)
```

## Conventions when editing
- **Accuracy is paramount.** This is security education — a wrong offset, opcode, or
  command teaches the wrong reflex. Verify technical claims; prefer canonical values
  (e.g. VulnServer TRUN offset 2003, GMON nSEH 3515) and tell the reader to confirm with
  `mona findmsp` rather than trusting a hardcoded number blindly.
- **Practical over theoretical.** The user learns fast and hates filler. Lead with the
  command/action; keep prose tight. Tables and code blocks over paragraphs.
- **Legal/ethical framing.** All content assumes authorized lab practice and exam prep.
  Keep the "practice only on systems you own / are authorized to test" framing intact.
- **Templates are skeletons**, deliberately with blanks (`shellcode = b""`) for the
  learner to fill — don't ship a working weaponized exploit; ship the scaffold.

## The dashboard (dashboard.html)
- Fully self-contained; opens offline from disk (has its own `<!doctype>`/`<head>`/`<body>`).
- Also published as a private Artifact for phone use. To update the Artifact, strip the
  outer skeleton (`<title>`…`</script>`) into a scratchpad file and republish to the same
  URL: https://claude.ai/artifact/KN9bmAzFDwn4WN169wPfzS
- Data (loop steps, triage tree, cheats, flashcards, playbooks, lab steps, quiz) lives in
  JS arrays near the top of the `<script>` block — edit those to change content.
- Theme-aware (light/dark), no external deps except optional Google Fonts.

## Branch / workflow
- Development branch: `claude/osed-fast-track-t40iqt`.
- Commit in logical batches with descriptive messages; push after each meaningful unit.
