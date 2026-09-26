# Playbook: Egghunter (beating space restrictions)

**Signature:** You control EIP (or SEH) but the space right after it is too small for
real shellcode (~30–80 bytes max). Your full payload lands *somewhere else* in memory
(a different buffer, a heap allocation, an earlier field).

## The idea
Plant a small (~32-byte) "hunter" stub at your controlled EIP. It scans process memory
for a unique 8-byte **egg** tag (`w00tw00t` = the tag repeated twice), and when it
finds it, jumps to the bytes right after. Your real shellcode is `egg + shellcode`,
sprayed into the larger buffer.

```
[ tiny space ] → EGGHUNTER (32 bytes)  ──scans──►  [ w00t w00t | REAL SHELLCODE ]
```

## Steps

### 1. Generate the egghunter
```
!py mona egg -t w00t          ; mona builds the hunter using tag "w00t" (-> w00tw00t)
```
Or use the classic NtDisplayString / NtAccessCheckAndAuditAlarm hunter. mona's is
Windows-tested and handles access violations via SEH or the syscall check.

### 2. Tag your real shellcode
Prefix the actual payload with the egg **twice** (the hunter searches for two
consecutive copies to avoid matching itself):
```python
egg       = b"w00tw00t"
shellcode = b"..."                     # msfvenom, badchars excluded
payload   = egg + shellcode            # goes into the LARGE buffer
```

### 3. Place hunter at the controlled pointer
```python
hunter = b"..."                        # 32 bytes from mona egg (badchar-clean!)
# stack BOF: buf = A*offset + JMP_ESP + nops + hunter
# SEH:       buf = A*offset + nseh + seh + hunter
```

### 4. Get the tagged shellcode into memory
Deliver it in whatever field/buffer has room. Common exam pattern: one small field
overflows EIP (hunter fits), a *separate* larger field (username, filename, second
packet) holds `egg + shellcode`. The hunter finds it wherever it is.

## Key facts to memorize
- Egg is the tag **doubled**: tag `w00t` → search target `w00tw00t` (8 bytes).
- Hunter is ~32 bytes — verify it fits your tiny space.
- Hunter itself must be **badchar-clean** — run it through mona compare too.
- Scanning is slow-ish but reliable; the app may appear to hang for a second. Normal.
- If the hunter can't find the egg: the tagged shellcode never made it to memory, OR
  a badchar mangled the egg/hunter, OR the shellcode landed but got truncated before
  the second tag copy.

## When to reach for this
- Stack BOF with only a few dozen bytes before the buffer ends.
- SEH where the post-SEH space is tiny.
- Any "I control the pointer but there's no room" situation.

## Gotchas
- The egg tag bytes must not be in your badchar set.
- If DEP is on, the hunter AND the found shellcode both need executable memory — pair
  with ROP (`dep-rop-playbook.md`).
- Two copies of the tag: don't forget — a single tag can match the hunter's own code.

→ (No dedicated template — bolt the hunter into `stack_bof.py` or `seh_overflow.py`;
  see the `EGGHUNTER` block in `02-templates/egghunter.py`.)
