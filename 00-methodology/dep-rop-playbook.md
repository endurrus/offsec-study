# Playbook: DEP Bypass with ROP

**Signature:** You control EIP, shellcode is in memory, but it won't execute — the
stack/heap is non-executable (DEP / NX). `mona mod` shows `NXCompat = True`.

## The idea
You can't execute your bytes as code, but you CAN chain existing executable code
(gadgets ending in `ret`) to call a Windows API that makes memory executable, then
jump into your shellcode. The classic target is **VirtualProtect** (mark existing
region RWX) or **VirtualAlloc** (allocate new RWX + copy). mona builds most of it.

## The fast path (let mona do the heavy lifting)

### 1. Generate a ROP chain automatically
```
!py mona rop -m *.dll -cpb "\x00\x0a\x0d"
```
This produces `rop_chains.txt` with ready chains for VirtualProtect / VirtualAlloc /
etc., plus a `rop.txt` of all usable gadgets. mona writes them as Python already.
**Read the top of the file — it tells you which chain is complete vs. needs a gadget.**

### 2. Use the generated chain
mona gives you a `create_rop_chain()` function. Paste it, call it:
```python
rop = create_rop_chain()               # from mona's rop_chains.txt (Python format)
```
Prefer chains built only from **non-ASLR, non-rebase** modules (recheck `mona mod`).

### 3. Position the ROP chain
The chain must sit where ESP points at the moment of `ret` after EIP. Layout:
```python
offset = 2003
# EIP overwrite must return into the ROP chain. Use a "ret" or "stack pivot" so
# execution flows into your chain sitting on the stack:
buf  = b"A"*offset
buf += struct.pack("<I", 0x<addr of RET or PUSH ESP;RET>)   # pivot / return-to-stack
buf += rop                              # the ROP chain
buf += b"\x90"*16 + shellcode           # chain ends by jumping here (mona sets this up)
```
Often the EIP overwrite itself is just a `RET` (or the chain starts right at ESP so
you place the first gadget address directly at the EIP position).

## What the VirtualProtect chain actually does (know this cold)
It sets up the stack so `ret` "calls" VirtualProtect with these args:
```
VirtualProtect(lpAddress, dwSize, flNewProtect=0x40 (PAGE_EXECUTE_READWRITE), lpflOldProtect)
```
Then returns into `lpAddress` (your shellcode, now executable). The gadgets:
- load each argument into the right register (`pop reg; ret`)
- neutralize junk (`pop; ret` to skip)
- place the API pointer (from IAT) and a return address = shellcode location

## Building a chain by hand (when mona's is incomplete)
1. `!py mona rop -m <module> -cpb "..."` → get gadget list.
2. Find `pop eax; ret`, `pop ecx; ret`, `mov [reg], reg; ret`, `pushad; ret`, etc.
3. Resolve `VirtualProtect` address from the IAT (`!py mona ropfunc -m <module>`).
4. Lay out: put API ptr into a register, args on stack, `pushad` to dump regs as the
   call frame, `ret` into it. This is the tedious part — mona usually avoids it.

## Gotchas
- **Badchars in gadget addresses:** always pass `-cpb`. A single null byte kills the address.
- **ASLR + DEP together:** the ROP gadgets must come from non-ASLR modules, or you must
  leak a base first (`aslr-bypass-playbook.md`).
- **Chain uses a rebased module:** addresses change per boot → unreliable. Recheck mona mod.
- **Stack alignment:** if the chain dies mid-way, single-step it in WinDbg (`t`), watch
  which gadget breaks. Usually a wrong gadget or a badchar-substituted address.
- **VirtualAlloc vs VirtualProtect:** VirtualProtect is simpler (in-place); use it first.

→ Template: `02-templates/dep_rop.py`
