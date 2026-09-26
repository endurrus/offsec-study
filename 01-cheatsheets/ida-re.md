# IDA Pro / Reverse Engineering Cheatsheet (for finding bugs)

OSED includes "Reverse Engineering for Bugs" — reading a disassembly to find the
vulnerable call *before* fuzzing. This is the minimum IDA fluency for that.

## Navigation (learn these first)
| Key | Action |
|---|---|
| `Space` | toggle graph view ↔ text view |
| `G` | jump to address |
| `X` | cross-references TO this (who calls/uses it) — **the bug-hunting key** |
| `Enter` | follow / jump into |
| `Esc` | go back |
| `N` | rename a variable/function |
| `;` | add a repeatable comment |
| `A` | mark bytes as an ASCII string |
| `U` | undefine |
| `C` / `D` | make code / make data |
| `Tab` | switch between disassembly and pseudocode (Hex-Rays decompiler) |

## Windows worth opening
- **Functions** (Shift+F3): the function list; search for interesting names.
- **Imports**: see which API calls the binary uses — jump straight to the dangerous ones.
- **Strings** (Shift+F12): find format strings, prompts, command names, paths.
- **Xrefs graph**: visualize who reaches a function.

## The bug-hunting workflow
1. **Open Imports**, look for classic unsafe sinks:
   - `strcpy`, `strcat`, `sprintf`, `gets`, `memcpy`, `lstrcpy`, `wcscpy`
   - `recv` / `ReadFile` into a fixed-size stack buffer
   - `sscanf`, `scanf` with `%s`
   - `printf`/`sprintf` where the format is a variable (format string!)
2. **X (xref)** on each sink → every call site.
3. At each call site, read the args: is the **destination a fixed stack buffer** and the
   **source attacker-controlled** with no length check? That's your overflow.
4. **Trace input backward**: from `recv`/parameter to the sink. Where does user data enter,
   and what (if any) bounds check exists?
5. Note the **buffer size** (from the stack frame / `sub esp, N`) — that's your rough
   offset before you even fuzz.

## Reading a stack frame (offset intel for free)
```
push ebp
mov  ebp, esp
sub  esp, 0x800          ; local buffer space ~ 2048 bytes -> expect offset near here
...
lea  eax, [ebp-0x400]    ; a local buffer at ebp-0x400
push <src>
push eax
call strcpy              ; strcpy into a 0x400 buffer with no bound = overflow
```
The `sub esp, N` and `[ebp-offset]` tell you buffer sizes → predict the crash offset.

## Format-string smell in disasm
```
push eax                 ; <-- user-controlled string
call printf              ; only ONE arg = format IS the user string = vuln
```
vs safe:
```
push eax                 ; the data
push offset aFmt         ; "%s" constant format
call printf
```

## Hex-Rays decompiler (F5) — the shortcut
If you have the decompiler, `F5` on a function gives C-like pseudocode. Read that first;
drop to disasm only to confirm sizes/offsets. Look for:
- `char buf[256];` then `strcpy(buf, input);`
- `sprintf(buf, input);` (format string)
- loops copying without a bound check.

## Connecting RE to exploitation
Once you've statically found the sink and buffer size:
- You already know the approximate **offset** → skip/shorten fuzzing.
- You know the **bug class** → jump straight to the right playbook.
- You know which **buffer** to target if multiple inputs exist.
RE turns "spray and pray fuzzing" into "I know exactly where the bug is."

## Practice
- Load VulnServer's `essfunc.dll` / `vulnserver.exe` in IDA; find the vulnerable command
  handlers (look for the `recv` → buffer → no-check pattern per command string).
- Match what you find statically against what the debugger shows dynamically. When they
  agree, you understand the bug both ways.
