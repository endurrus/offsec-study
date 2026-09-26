# OSED Exam-Day Checklist

48 hours, 3 machines/assignments, points threshold to pass. This is about *process
discipline* under fatigue — not brilliance. Follow the checklist even when tired,
especially when tired.

## Before you start (setup, ~30 min)
- [ ] Lab/VM snapshots taken (roll back cleanly if you wreck state)
- [ ] WinDbg + pykd + mona loaded and tested (`!py mona config -set workingfolder c:\mona\%p`)
- [ ] Kali tools ready: `msf-pattern_create`, `msf-pattern_offset`, `msfvenom`, `nc`
- [ ] Templates copied locally: `02-templates/` + `send_helpers.py`
- [ ] Screenshot tool ready + a running notes doc for the REPORT (screenshot AS you go)
- [ ] Listener command in clipboard: `nc -lvnp 443`

## Per-target loop (paste-and-go)
```
1. Recon the input surface (which field/packet reaches the parser)
2. FUZZ until crash. Record the crashing length.
3. Attach WinDbg BEFORE sending. Send cyclic pattern.
4. r ; !exchain ; !py mona findmsp ; !py mona mod      <- the 4 triage commands
5. Classify (decision tree): EIP? SEH? tiny space? DEP? ASLR?  -> pick playbook
6. Get offset (findmsp / pattern_offset). Confirm control (BBBB).
7. Badchar ritual: bytearray -> compare -> repeat until clean.
8. Find jump/gadget with the CONFIRMED badchar set (-cpb).
9. Handle mitigations: DEP->ROP, ASLR->non-ASLR module/leak, tiny->egghunter.
10. Generate shellcode with SAME badchars. EXITFUNC=thread.
11. Fire. Catch shell. SCREENSHOT proof (whoami, ipconfig).
12. Save the final exploit script + note every address/offset used.
```

## Screenshot discipline (you WILL forget — automate the habit)
For each target capture:
- [ ] the crash (EIP=your bytes / SEH chain)
- [ ] mona findmsp output (offset proof)
- [ ] badchar comparison result
- [ ] the jump/gadget address chosen
- [ ] final exploit code
- [ ] proof of exec: `whoami`, `hostname`, `ipconfig` in the shell
- [ ] the local.txt / proof file if applicable

## When you're stuck (>30 min on one step)
- [ ] Re-run `!py mona findmsp` — did the offset/space actually change?
- [ ] Re-verify badchars — a missed one silently truncates. This is the #1 time sink.
- [ ] Re-check `mona mod` — is your address in an ASLR/rebased module?
- [ ] Single-step (`t`) from the jump — where exactly does it die?
- [ ] Reduce complexity: get a `int3`/breakpoint or calc PoC landing FIRST, then swap in
      the real shellcode. Prove code exec before perfecting the payload.
- [ ] Take a 10-min walk. Fatigue tunnel-vision is real. Come back and re-read the crash.

## Time management (48h)
- [ ] Don't sink >4–5h into one machine on the first pass. Bank points elsewhere, return.
- [ ] Sleep. A 4-hour sleep block beats hour 30 of hallucinated debugging.
- [ ] Leave ~6–8h at the end purely for the REPORT. No points without the report.

## Report reminders
- [ ] Every step reproducible by a stranger: exact commands, addresses, offsets.
- [ ] Include the final exploit code in full.
- [ ] Note the specific module + why it was chosen (non-ASLR/SafeSEH-off).
- [ ] Proof screenshots embedded and legible.

## The one rule that saves runs
**Prove code execution with a trivial payload (breakpoint / calc) BEFORE fighting with a
full reverse shell.** If `int3` breaks where you expect, control is confirmed and the
rest is just payload plumbing. Most "my exploit doesn't work" is actually "my shellcode
has a badchar" — separate the two problems.
