# Playbook: ASLR Bypass

**Signature:** Your exploit works once, then fails after a reboot / restart. Addresses
you hardcoded (JMP ESP, ROP gadgets, POP POP RET) point somewhere else now.
`mona mod` shows `ASLR = True` / `Rebase = True` on the modules you were using.

## The two winning strategies

### Strategy A — Find a non-ASLR module (easiest, do this first)
Not every module opts into ASLR. If even ONE loaded module has `ASLR = False`, use its
addresses for your JMP / gadgets / POP POP RET. They're fixed across reboots.
```
!py mona mod                 ; scan the ASLR column for a False
!py mona jmp -r esp -cm aslr=false -cpb "\x00\x0a\x0d"   ; only from non-ASLR modules
!py mona rop  -cm aslr=false -cpb "\x00\x0a\x0d"
```
`-cm aslr=false` = "criteria: modules where ASLR is false." This alone beats ASLR in
most exam scenarios. **Always check for this before doing anything fancier.**

### Strategy B — Leak an address, compute the base
If every module is ASLR'd, you need an **information leak**: some bug that prints or
returns a pointer into a known module. Then:
```
module_base = leaked_addr - known_offset_of_that_symbol
gadget      = module_base + gadget_rva
```
Steps:
1. Find a primitive that discloses memory (format string `%p`, an over-read, an echo of
   a stack value, a returned pointer in a response).
2. Identify WHICH symbol/return-address you leaked (match it in the debugger: the RVA is
   constant even when the base moves).
3. Compute base = leaked − RVA.
4. Rebuild every address at runtime: `base + rva`. Now the exploit self-adjusts.

Format strings are a classic leak source → pair with `format-string-playbook.md`.

## Doing the math in your exploit
```python
# Suppose you leaked a return address that is always base + 0x1234 in module X:
leaked      = 0x00a51234            # read from the leak at runtime
rva         = 0x1234
base        = leaked - rva          # -> module X base for THIS run
jmp_esp     = base + 0x000110af     # gadget RVA within module X
rop_gadget  = base + 0x00023abc
```
Everything downstream (`struct.pack("<I", ...)`) uses these computed values.

## Finding RVAs (offsets that stay constant)
```
!py mona mod                       ; note the module's current base
; gadget_rva = gadget_address - module_base
!py mona jmp -r esp -o             ; -o prints offsets/RVAs where helpful
```
RVA = absolute address − module base. It does NOT change with ASLR — only the base does.

## Gotchas
- **Partial overwrite trick:** the low 12 bits (a page) don't randomize under ASLR — you
  can sometimes overwrite only the low 2 bytes of a pointer and keep the high (rebased)
  bytes intact. Situational, but powerful when you can't fully leak.
- **64-bit vs 32-bit ASLR entropy:** OSED is 32-bit (x86); entropy is low enough that
  brute force is *sometimes* viable, but leak/non-ASLR module is the intended path.
- **Leaked value freshness:** you must leak in the SAME process run you exploit — the
  base changes each launch.
- Combine freely: ASLR bypass gives you correct addresses; DEP bypass (ROP) still needed
  separately if NX is on. They're orthogonal mitigations.

→ Related templates: `02-templates/aslr_bypass.py`, `02-templates/format_string.py`
