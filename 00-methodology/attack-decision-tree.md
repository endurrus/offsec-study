# Attack Decision Tree — "I have a crash, now what?"

Read top to bottom. Stop at the first branch that matches. Each leaf points to a playbook.

```
CRASH CONFIRMED
│
├─ Did EIP get overwritten with my pattern bytes (41414141 / cyclic)?
│   │
│   ├─ YES → classic STACK BUFFER OVERFLOW
│   │        → 00-methodology/stack-bof-playbook.md
│   │
│   └─ NO, EIP is intact but I crashed on an ACCESS VIOLATION handling an exception
│            → look at the SEH chain (!exchain / mona seh)
│            → is nSEH / SEH overwritten with my bytes?
│                ├─ YES → SEH OVERFLOW  → 00-methodology/seh-playbook.md
│                └─ NO  → keep digging: is it a write-what-where? read AV? → RE the crash (IDA)
│
├─ I control EIP but have TINY space after it (< ~80 bytes for shellcode)
│   → EGGHUNTER  → 00-methodology/egghunter-playbook.md
│   (stage the real shellcode elsewhere in memory; hunt for the egg tag)
│
├─ Shellcode won't execute — I land in my bytes but it dies immediately / DEP
│   → check module protections (mona: !py mona mod   — look at NX/DEP column)
│   → DEP is ON → build a ROP chain to VirtualProtect/VirtualAlloc/etc.
│   → 00-methodology/dep-rop-playbook.md
│
├─ My jump address changes every run / modules rebase
│   → ASLR is ON  → 00-methodology/aslr-bypass-playbook.md
│   (find a non-ASLR module, or leak an address to compute base)
│
└─ The bug is a printf-family call using MY string as the format
    → FORMAT STRING  → 00-methodology/format-string-playbook.md
    (%x to leak, %n to write; compute offsets)
```

## Fast triage commands (paste these first, every time)

```
# In WinDbg after the crash:
r                      ; registers — is EIP = 41414141?
!exchain               ; SEH chain — is the handler your bytes?
!py mona findmsp       ; mona maps EVERY register/pointer to your cyclic pattern at once
!py mona mod           ; module protections table: ASLR / DEP / Rebase / SafeSEH
```

`!py mona findmsp` is the single biggest time-saver: it tells you the offset to
EIP, to SEH, whether ESP points into your buffer, and how much space you have —
all in one shot. **Run it before you think.**

## "Which mitigation is on?" quick read of `mona mod`

| Column shows `True`/`False` | Means | Your move |
|---|---|---|
| Rebase = False, ASLR = False | module loads at fixed base | use it for your jump / ROP gadgets |
| SafeSEH = False | SEH not protected | SEH overwrite viable, POP POP RET from this module OK |
| ASLR = True | address randomizes | avoid for hardcoded addrs, or leak base |
| NXCompat/DEP = True | stack not executable | need ROP to mark memory executable |
| OS Dll = False | app's own / 3rd-party dll | **prefer these** — usually no mitigations |

Rule of thumb: **hunt for the module with the most `False`s.** That's your friend.
