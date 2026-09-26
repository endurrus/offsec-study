#!/usr/bin/env python3
"""
send_helpers.py — shared delivery helpers for OSED exploit templates.

Import these so each exploit only has to build the buffer, not re-implement
sockets / offset math. Keep this next to the templates.
"""
import socket
import struct
import sys


def p32(addr: int) -> bytes:
    """Pack a 32-bit address little-endian. Use for ALL pointers (JMP ESP, ROP, SEH)."""
    return struct.pack("<I", addr)


def cyclic(length: int) -> bytes:
    """
    De Bruijn-ish cyclic pattern (Metasploit-compatible Aa0Aa1... style) for offset
    finding without leaving the box. For real work prefer msf-pattern_create / mona pc,
    but this is handy offline.
    """
    out = bytearray()
    ucase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lcase = "abcdefghijklmnopqrstuvwxyz"
    digit = "0123456789"
    for u in ucase:
        for l in lcase:
            for d in digit:
                if len(out) >= length:
                    return bytes(out[:length])
                out += f"{u}{l}{d}".encode()
    return bytes(out[:length])


def cyclic_find(value: int, length: int = 100000) -> int:
    """Find the offset of a 4-byte value (as seen in EIP) within cyclic(length)."""
    needle = struct.pack("<I", value)  # EIP is little-endian in memory
    hay = cyclic(length)
    idx = hay.find(needle)
    if idx == -1:
        # try the value as big-endian text (in case you read it already-ordered)
        needle = struct.pack(">I", value)
        idx = hay.find(needle)
    return idx


def send_tcp(host: str, port: int, payload: bytes, recv_first: bool = False,
             timeout: float = 5.0) -> None:
    """Fire a raw TCP payload. Set recv_first=True for banner-then-send protocols."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))
    if recv_first:
        try:
            banner = s.recv(1024)
            print(f"[<] banner: {banner!r}")
        except socket.timeout:
            print("[!] no banner")
    print(f"[>] sending {len(payload)} bytes")
    s.send(payload)
    try:
        resp = s.recv(1024)
        print(f"[<] response: {resp!r}")
    except socket.timeout:
        print("[i] no response (often normal on a successful crash)")
    s.close()


def send_http(host: str, port: int, path: str, body: bytes,
              method: str = "POST") -> None:
    """Minimal HTTP delivery — put your payload in `body` (or bake it into `path`)."""
    req = (
        f"{method} {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"Content-Length: {len(body)}\r\n"
        f"Connection: close\r\n\r\n"
    ).encode() + body
    send_tcp(host, port, req)


def badchar_array(exclude: bytes = b"\x00") -> bytes:
    """Generate \\x01..\\xff minus excluded bytes for badchar testing."""
    return bytes(b for b in range(1, 256) if b not in exclude)


if __name__ == "__main__":
    # quick self-test / offset lookup:  python3 send_helpers.py 0x42306142
    if len(sys.argv) == 2:
        val = int(sys.argv[1], 16)
        print("offset:", cyclic_find(val))
    else:
        print("badchar array:", "".join(f"\\x{b:02x}" for b in badchar_array()))
