# mona.py Cheatsheet

mona is the exploit-dev swiss army knife (Corelan). Runs inside WinDbg via pykd:
`!py mona <command>`. Output goes to the working folder.

## Setup (once per lab)
```
!py mona config -set workingfolder c:\mona\%p     ; %p = per-process subfolder
```

## The command you run FIRST after every crash
```
!py mona findmsp
```
Reports, all at once:
- offset from buffer start to **EIP**
- offset to **SEH** record (nSEH) if it's an SEH crash
- which **registers** point into your buffer (and their offsets)
- whether **ESP** points into your buffer and **how much space** you have
It reads the cyclic (Metasploit) pattern already in memory, so send a pattern buffer
first. This one command replaces a dozen manual steps.

## Cyclic pattern (offset finding)
```
!py mona pc 3000          ; pattern_create length 3000 (alias: pattern_create)
!py mona po 42306142      ; pattern_offset for a value found in EIP/SEH
```
(Or use Kali `msf-pattern_create -l 3000` / `msf-pattern_offset -l 3000 -q <val>`.)

## Bad characters
```
!py mona bytearray -b "\x00"                       ; make array excluding \x00
; send array in buffer, crash, find where it landed (e.g. ESP), then:
!py mona compare -f c:\mona\<proc>\bytearray.bin -a <addr>
```
`compare` prints "unmodified" when clean, or lists mangled bytes. Remove each mangled
byte from `-b`, regenerate, resend, recompare. Repeat until clean.

## Finding jumps / gadgets
```
!py mona jmp -r esp -cpb "\x00\x0a\x0d"            ; JMP/CALL ESP, badchar-clean
!py mona jmp -r esp -cm aslr=false                 ; only from non-ASLR modules
!py mona seh -cpb "\x00\x0a\x0d"                   ; POP POP RET (SafeSEH-off modules)
!py mona find -s "\xff\xe4" -m <module>            ; raw opcode search (FF E4 = jmp esp)
```
Criteria flags (`-cm`): `aslr=false`, `rebase=false`, `safeseh=false`, `os=false`.
Combine them: `-cm aslr=false,rebase=false`.

## Modules & mitigations
```
!py mona mod                       ; table: Rebase / SafeSEH / ASLR / NXCompat / OS Dll
```
Hunt for the row with the most `False` — that's your target module.

## ROP (DEP bypass)
```
!py mona rop -m *.dll -cpb "\x00\x0a\x0d"          ; full auto: builds rop_chains.txt
!py mona rop -m mod1.dll,mod2.dll -cpb "..."       ; restrict to specific modules
!py mona ropfunc -m <module>                        ; resolve VirtualProtect/Alloc ptrs
!py mona stackpivot -distance 800                   ; find pivots to reach your chain
```
Read `rop_chains.txt` — it emits a ready `create_rop_chain()` in Python. Prefer the
VirtualProtect chain; check it isn't missing gadgets (mona flags gaps at the top).

## Egghunter
```
!py mona egg -t w00t                ; hunter searching for tag "w00t" (-> w00tw00t)
!py mona egg -t w00t -c             ; also encode/clean if needed
```

## Handy extras
```
!py mona nosafeseh                  ; list modules WITHOUT SafeSEH
!py mona noaslr                     ; list modules WITHOUT ASLR
!py mona findwild -s "jmp esp"      ; search with wildcards/mnemonics
!py mona skeleton                   ; generate an exploit skeleton (PoC scaffold)
```

## The typical mona-driven session
```
1. !py mona config -set workingfolder c:\mona\%p
2. (send cyclic pattern, crash)
3. !py mona findmsp                      → offsets + space
4. !py mona mod                          → pick target module
5. (send bytearray)  !py mona bytearray -b "\x00"
6. !py mona compare -f ... -a <addr>     → badchars
7. !py mona jmp -r esp -cpb "<badchars>" → jump address   (or seh / rop)
8. build exploit, done
```
