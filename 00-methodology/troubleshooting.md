# Troubleshooting — "it should work but doesn't"

Symptom → most likely cause → fix. Ordered by how often it bites. When stuck >30 min,
read this top to bottom.

## EIP / control problems

**EIP is close to my value but not exactly 42424242**
→ Offset is off by a few bytes. Re-run `!py mona findmsp`; recount. A protocol prefix
(`TRUN /.:/ `) or length field may be shifting your buffer.

**EIP has some of my bytes but they look shifted/rotated**
→ You're landing across a boundary, or an earlier badchar truncated part of the buffer.
Re-verify badchars.

**I control EIP but the app doesn't even reach my jump**
→ Wrong crash / wrong exception. For SEH bugs you must `g` to pass the exception to the
handler. Check `!exchain` — maybe it's an SEH bug, not a straight EIP overwrite.

## The #1 time sink: bad characters

**Shellcode runs partially then dies / garbage in memory where shellcode should be**
→ A badchar mangled or truncated the payload. Re-run the full bytearray/compare ritual.
Trust the FIRST bad byte mona reports, remove it, recompare (corruption cascades).

**Works with a small test payload, fails with the real shellcode**
→ The real shellcode contains a badchar the small one didn't. Regenerate msfvenom with the
complete `-b` set. Verify: `python3 -c "sc=b'...'; print([hex(c) for c in sc if c in b'\x00\x0a\x0d'])"`

**Jump address never lands**
→ The address itself contains a badchar. Regenerate with `mona jmp ... -cpb "<all badchars>"`.

## Jump / module problems

**Exploit works once, fails after reboot/restart**
→ ASLR. Your module rebased. Use a non-ASLR module (`mona mod`, `-cm aslr=false`) or leak
a base. See `aslr-bypass-playbook.md`.

**`u <jmp_addr>` doesn't show `jmp esp`**
→ Wrong address, wrong endianness in the buffer, or you read the wrong module. Re-copy
from `mona jmp` output; pack little-endian (`struct.pack("<I", addr)`).

**POP POP RET returns to the wrong place (SEH)**
→ nSEH jump distance wrong, or SEH address has a badchar, or the module has SafeSEH on.
Recheck `mona seh` (SafeSEH-off only) and your `\xeb\x06`.

## Shellcode / DEP problems

**Land in shellcode, first few instructions run, then access violation**
→ DEP is on (stack not executable). Build a ROP chain. `mona mod` → NXCompat=True confirms.

**Encoded shellcode corrupts itself midway**
→ The shikata decoder writes near its own location. Add NOP padding, or `sub esp, 0x###`
before it, so the decode area doesn't overwrite live code.

**Shell connects but is dead / no output**
→ For custom shellcode: STARTUPINFO std handles not wired to the socket. For msfvenom:
wrong LHOST/LPORT, or EXITFUNC killed the thread. Try `EXITFUNC=thread`.

## ROP problems

**ROP chain dies mid-way**
→ Single-step (`t`) from the first gadget; watch which one breaks. Usually a badchar in a
gadget address or a gadget from a rebased/ASLR module. Regenerate with `-cpb` and check
`mona mod`.

**VirtualProtect "called" but memory still not executable**
→ Args on the stack are wrong (order/values). `bp kernel32!VirtualProtect`, inspect
`dd esp` when hit: expect `[ret][lpAddress][dwSize][0x40][lpflOldProtect]`.

## Environment problems

**`!py mona` errors / pykd won't load**
→ Arch mismatch (x86 pykd with x64 WinDbg or vice-versa). Match WinDbg arch to the target.

**Shellcode blocked / shell dies instantly on the victim**
→ Defender/AV eating it. Disable real-time protection in the isolated lab VM.

**Can't reach the service from Kali**
→ Victim firewall, wrong network mode (use host-only/NAT with both VMs on it), or the
service isn't running. `nc -vn <ip> <port>` to test.

**Works when WinDbg is attached, fails standalone**
→ Attaching changes timing/heap/addresses slightly, OR a badchar you only got away with
under the debugger. Re-verify badchars; test without attach.

## The meta-fix
When truly stuck: **shrink the problem.** Replace the shellcode with `\xcc\xcc\xcc\xcc`
(int3). If WinDbg breaks exactly at your expected landing address, control is proven and
the bug is 100% in the payload (badchars/encoding/space). If it does NOT break there, the
bug is upstream (offset/jump/mitigation). This single test tells you which half to debug.
