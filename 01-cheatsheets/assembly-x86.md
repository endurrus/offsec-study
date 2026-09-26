# x86 Assembly + Architecture Cheatsheet (for OSED)

Just enough x86 to read gadgets, write shellcode, and understand crashes. 32-bit.

## Registers
| Reg | Role | Notes |
|---|---|---|
| EAX | accumulator | return values, syscall/API results |
| EBX | base | general |
| ECX | counter | loop counts, `rep` |
| EDX | data | I/O, mul/div high half |
| ESI | source index | string ops source |
| EDI | dest index | string ops dest |
| EBP | base pointer | stack frame base |
| ESP | stack pointer | **top of stack** — your shellcode often lands here |
| EIP | instruction ptr | **what you hijack** |
| EFLAGS | flags | ZF, CF, SF, etc. |
Sub-registers: EAX→AX(16)→AH/AL(8). Use AL to write a small value without null bytes.

## Segment registers (matter for shellcode)
- `FS` on Windows x86 points to the **TEB**. `fs:[0x30]` = PEB. `fs:[0x00]` = SEH list head.

## The stack (grows DOWN toward lower addresses)
```
higher addr   [ ... older frames ... ]
              [ arguments            ]
              [ return address       ]  <- overwrite target in stack BOF
              [ saved EBP            ]
              [ local buffer   AAAA  ]  <- your overflow starts here, writes UPWARD
ESP ------->  [ top of stack         ]
lower addr
```
`push` decrements ESP then writes; `pop` reads then increments ESP.
`call` pushes return addr then jumps; `ret` pops into EIP.

## Instructions you MUST recognize (gadgets & shellcode)
| Instr | Meaning | Opcode(s) |
|---|---|---|
| `jmp esp` | jump to stack top | `FF E4` |
| `call esp` | call stack top | `FF D4` |
| `push esp; ret` | pivot to stack | `54 C3` |
| `pop eax; ret` | load stack val into eax | `58 C3` |
| `pop pop ret` | SEH gadget | e.g. `5F 5E C3` |
| `ret` | return (pop EIP) | `C3` |
| `retn 0x8` | ret + adjust stack | `C2 08 00` |
| `nop` | do nothing (NOP sled) | `90` |
| `int3` | breakpoint | `CC` |
| `xor eax,eax` | zero without nulls | `31 C0` |
| `inc eax` / `dec eax` | +1 / -1 | `40` / `48` |
| `mov al, 5` | small load, no null | `B0 05` |
| `pushad` / `popad` | push/pop all GP regs | `60` / `61` |
| `jmp short +N` | EB xx | `EB <rel8>` |
| `jmp near` | E9 rel32 | `E9 <rel32>` |

## Short vs near jumps (crucial for SEH nSEH)
- **Short jump** `EB xx`: 2 bytes, range −128..+127. `\xeb\x06` = jump +6 (over SEH ptr).
- **Near jump** `E9 xx xx xx xx`: 5 bytes, ±2GB. Use when you must jump far/backward.
- Backward short jump: `\xeb\xf9` etc. (negative rel8, e.g. 0xF9 = −7).

## Avoiding null bytes (shellcode discipline)
| Want | Nulls | Instead |
|---|---|---|
| `mov eax, 0` | yes | `xor eax, eax` |
| `mov eax, 0x5` | yes | `xor eax,eax; mov al, 5` |
| `push 0` | yes | `xor eax,eax; push eax` |
| big constant | maybe | build via add/sub/xor, or neg trick |

## Calling convention (Windows stdcall — most Win32 APIs)
- Args pushed **right to left** onto the stack.
- **Callee** cleans the stack (`retn N`).
- Return value in **EAX**.
```
; VirtualProtect(addr, size, 0x40, &old):
push old_ptr          ; 4th arg
push 0x40             ; 3rd arg (PAGE_EXECUTE_READWRITE)
push size            ; 2nd
push addr            ; 1st
call VirtualProtect
```
This ordering is exactly what a ROP chain reproduces on the stack.

## Little-endian (bites everyone)
Address `0x625011af` is stored in memory as bytes `af 11 50 62`.
In Python: `struct.pack("<I", 0x625011af)` → `b"\xaf\x11\x50\x62"`. Always pack pointers
little-endian; **never** reverse raw opcode bytes (those go in the order written).

## Common flags/conditions in gadget hunting
- `ZF` set by `test`/`cmp`/`xor` when result is zero.
- Conditional jumps: `je/jz`, `jne/jnz`, `jg`, `jl`, `jbe`, etc. Rarely needed in gadgets
  but appear in RE.

## PEB walk offsets (x86, memorize for shellcode)
```
fs:[0x30]        -> PEB
PEB + 0x0C       -> PEB_LDR_DATA
LDR + 0x14       -> InMemoryOrderModuleList (first module entry)
entry + 0x10     -> module base (DllBase)   [within LDR_DATA_TABLE_ENTRY, order-list based]
base + PE parsing-> export directory -> function addresses
```
(Exact sub-offsets vary by list traversal — see `03-shellcode/` notes.)
