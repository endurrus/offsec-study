# Practice Progression — the order that builds reflexes fastest

Don't practice randomly. Each rung adds ONE new skill on top of the last. Move up only
when you can do the current rung **without notes**. Tick the boxes.

## Rung 1 — Stack BOF muscle memory (do this until boring)
- [ ] VulnServer **TRUN**: full exploit from scratch, following the walkthrough once.
- [ ] TRUN again with NO notes — time yourself. Goal: working shell in <20 min.
- [ ] TRUN with `\xcc` breakpoint payload → understand the "prove control first" split.
- [ ] Redo the offset + badchar + JMP-ESP steps until each is automatic.
> Skill gained: the 8-step loop, mona findmsp, badchar ritual, JMP ESP, msfvenom.

## Rung 2 — SEH overflow
- [ ] VulnServer **GMON**: identify it's SEH (EIP intact, `!exchain` = your bytes).
- [ ] Find offset to nSEH, POP POP RET via `mona seh`, short-jmp nSEH.
- [ ] Get a shell. Then redo without notes.
- [ ] Try War-FTP or crossfire (well-documented SEH) to see a real-app variant.
> Skill gained: SEH mechanics, POP POP RET, SafeSEH awareness, short jumps.

## Rung 3 — Space constraints & egghunters
- [ ] VulnServer **GTER / KSTET**: limited space after the pointer.
- [ ] Generate an egghunter (`mona egg`), tag shellcode, land it from a second buffer.
- [ ] Confirm the hunter finds the egg (watch it in WinDbg, `s -a ... "w00tw00t"`).
> Skill gained: egghunters, two-buffer staging, thinking about memory layout.

## Rung 4 — DEP bypass with ROP
- [ ] Turn DEP **ON** for a target you already exploited. Watch it break.
- [ ] `mona rop -m *.dll -cpb` → VirtualProtect chain. Get the shell back.
- [ ] Single-step the chain (`t`) once, fully, so you understand each gadget.
- [ ] Bonus: hand-verify what VirtualProtect args the chain sets up.
> Skill gained: ROP, DEP model, reading gadgets, stack layout of a call.

## Rung 5 — ASLR bypass
- [ ] Use a target where your gadget module is ASLR'd. Watch addresses drift.
- [ ] Find a non-ASLR module (`mona mod`, `-cm aslr=false`) and re-stabilize.
- [ ] If you have a leak primitive: compute base = leaked − RVA at runtime.
> Skill gained: ASLR model, RVAs, non-ASLR module hunting, leak math.

## Rung 6 — Custom shellcode
- [ ] Hand-write WinExec("calc") shellcode: PEB walk + resolve + call. Assemble, run.
- [ ] Make it 100% null-free.
- [ ] Level up to a hand-rolled reverse shell (`03-shellcode/reverse_shell.asm`).
> Skill gained: the resolver, null-avoidance, the API call chain, size discipline.

## Rung 7 — Format strings
- [ ] Find a `printf(user)` target (or a deliberately-vulnerable practice binary).
- [ ] Leak the stack with `%N$x`; find your offset.
- [ ] Overwrite a value with `%hhn`; verify in the debugger.
> Skill gained: format-string read/write, %n arithmetic, redirecting flow.

## Rung 8 — Reverse engineering for bugs
- [ ] Load a target binary in IDA (`01-cheatsheets/ida-re.md`).
- [ ] Find dangerous calls (strcpy/memcpy/sprintf, recv into fixed buffer).
- [ ] Trace user input to the overflow, statically, before ever fuzzing.
> Skill gained: static bug-finding, reading disassembly, connecting RE to exploitation.

## The graduation test
Pick a target you've **never seen**, DEP on, and go end-to-end under a 4-hour clock with
only the cheatsheets — no walkthroughs. If you can, you're exam-ready. If you stall,
your weakness log (`04-drills/spaced-repetition.md`) just wrote itself.
