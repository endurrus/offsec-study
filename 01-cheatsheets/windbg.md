# WinDbg Cheatsheet (x86 user-mode, exploit dev)

> Goal: never break flow looking up a command. Drill these until they're reflex.

## Attach / launch / run
| Command | Does |
|---|---|
| `File > Attach to Process` (F6) | attach to a running target |
| `File > Open Executable` | launch under debugger |
| `g` | go / continue execution |
| `gN` | go and pass exception to app (needed for SEH crashes) |
| `Ctrl+Break` | break into the running target |
| `.restart` | restart the debugged process |
| `q` | quit |
| `.cls` | clear screen |

## Registers & flow
| Command | Does |
|---|---|
| `r` | show all registers |
| `r eip` | show one register |
| `r eax=0x41414141` | set a register |
| `t` | trace (step INTO, one instruction) |
| `p` | step OVER |
| `pt` | step to next return |
| `u eip` | disassemble at EIP |
| `u <addr> L20` | disassemble 0x20 instructions at addr |
| `uf <addr>` | disassemble whole function |

## Memory: display
| Command | Does |
|---|---|
| `dd <addr>` | dump DWORDs |
| `dds <addr>` | dump DWORDs + symbol resolution (great for stacks/ROP) |
| `dc <addr>` | dump DWORDs + ASCII |
| `db <addr>` | dump bytes + ASCII |
| `da <addr>` | dump as ASCII string |
| `du <addr>` | dump as Unicode string |
| `dd esp L40` | dump 0x40 dwords from ESP (your landing zone) |
| `d` | repeat last dump, next chunk |

## Memory: write / search
| Command | Does |
|---|---|
| `eb <addr> 90 90 90` | edit bytes |
| `ed <addr> 41414141` | edit dword |
| `s -b <start> <end> 90 90` | search memory for byte pattern |
| `s -a <start> L?80000000 "w00tw00t"` | search for a string (find your egg!) |
| `.writemem C:\dump.bin <start> <end>` | dump memory region to file |

## Breakpoints
| Command | Does |
|---|---|
| `bp <addr>` | set breakpoint |
| `bp kernel32!VirtualProtect` | break on an API (verify your ROP call) |
| `ba w4 <addr>` | break on WRITE of 4 bytes at addr (find who overwrites SEH) |
| `ba r4 <addr>` | break on READ |
| `bl` | list breakpoints |
| `bc *` / `bc 0` | clear all / clear #0 |
| `bd 0` / `be 0` | disable / enable |

## Exceptions & SEH (the crash triage core)
| Command | Does |
|---|---|
| `!exchain` | show the SEH chain (is the handler your bytes?) |
| `!teb` | thread env block: stack limits, SEH list head |
| `.exr -1` | last exception record |
| `.ecxr` | switch context to the exception |
| `!analyze -v` | verbose crash analysis (slow but thorough) |

## Modules & symbols
| Command | Does |
|---|---|
| `lm` | list loaded modules |
| `lm m <name>` | info on one module (base, range) |
| `!address <addr>` | what region is this? (stack/heap/image, protections) |
| `x <mod>!*Virtual*` | search symbols |
| `.reload /f` | force reload symbols |

## The mona workflow (needs pykd + mona.py installed)
| Command | Does |
|---|---|
| `!py mona config -set workingfolder c:\mona\%p` | set output folder per-process |
| `!py mona findmsp` | **the triage command** — maps cyclic pattern to EIP/SEH/regs/space |
| `!py mona mod` | module mitigation table (ASLR/DEP/SafeSEH/Rebase) |
| `!py mona bytearray -b "\x00"` | generate badchar test array (excluding listed) |
| `!py mona compare -f <bytearray.bin> -a <addr>` | diff memory vs array → find badchars |
| `!py mona jmp -r esp -cpb "\x00\x0a\x0d"` | find JMP ESP (badchar-clean) |
| `!py mona seh -cpb "\x00\x0a\x0d"` | find POP POP RET (SafeSEH-off) |
| `!py mona rop -m *.dll -cpb "..."` | build ROP chain(s) for DEP bypass |
| `!py mona egg -t w00t` | generate an egghunter |
| `!py mona ropfunc -m <mod>` | resolve API pointers (VirtualProtect etc.) |

## Quick recipes
```
; After a crash — the 4-command triage:
r
!exchain
!py mona findmsp
!py mona mod

; Watch what overwrites SEH:
ba w4 <seh_address>       ; then g, catch the write, look at the call stack

; Verify your JMP ESP lands right:
bp <jmp_esp_addr>         ; g, when hit, single-step (t) into your shellcode

; Confirm VirtualProtect gets called with RWX (0x40):
bp kernel32!VirtualProtect ; g, inspect args on the stack (dd esp)
```

## Setup one-liner (in your lab, once)
```
; pykd + mona:
.load pykd.pyd
!py mona config -set workingfolder c:\mona\%p
```
