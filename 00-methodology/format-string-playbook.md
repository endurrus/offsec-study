# Playbook: Format String Specifier Attack

**Signature:** The app passes *your* input directly as the format argument to a
printf-family function: `printf(user_input)` instead of `printf("%s", user_input)`.
Symptom: you send `%x %x %x` and it prints stack values / hex garbage instead of
literal text. Send `%n` and it crashes (write).

## Two powers this gives you
1. **READ (leak):** `%x`, `%p`, `%s` dump stack/memory → defeat ASLR, leak canaries, spy.
2. **WRITE (`%n`):** `%n` writes the number of bytes printed so far into an address on
   the stack → overwrite a return address, GOT/IAT entry, or a function pointer.

## READ — leaking memory

### Dump the stack
```
AAAA %x %x %x %x %x %x %x %x        ; count how many %x until you see 41414141
```
When a `%x` prints `41414141`, that's YOUR "AAAA" — its position N is your **offset**.
```
AAAA %8$x            ; direct parameter access: read the 8th arg directly
```
Positional (`%N$x`) is far cleaner than counting — use it once you know N.

### Read an arbitrary string (leak a pointer's target)
Put a target address in your buffer, then `%s` it:
```
<4-byte target addr>%8$s        ; treats the 8th arg (your addr) as a char* and prints it
```
Great for dumping a module's memory to find/confirm a base for ASLR bypass.

## WRITE — the `%n` primitive

`%n` writes (as an int) the count of chars printed so far into the address pointed to by
the corresponding argument.
```
<target addr>%8$n              ; writes current_count into *arg8 (= your target addr)
```
Control the count with width padding: `%100x` prints 100 chars → `%n` writes 100.

### Writing a full 4-byte value (byte-by-byte)
Writing a big number all at once means printing billions of chars (impossible). Instead
write **one or two bytes at a time** using `%hhn` (1 byte) / `%hn` (2 bytes) at four
consecutive addresses, ordering the writes from smallest byte-count to largest:
```
addr+0, addr+1, addr+2, addr+3         ; four target addresses in the buffer
%<pad>c%N$hhn ... repeated, increasing the running count to the desired byte each time
```
This is the fiddly part. Steps:
1. Split target value into 4 bytes.
2. Sort by numeric value (ascending) — you can only increase the printed count.
3. Pad with `%<width>c` between each `%hhn` to reach each byte's value.
4. Point each `%hhn` at addr+0..3 respectively.

## Building it
1. Find offset N (`%N$x` prints your marker).
2. Decide read or write.
3. For write: pick the target (saved return addr / a GOT/IAT func ptr / SEH).
4. Compute paddings, assemble, test in WinDbg (watch the target address change).

## Gotchas
- **Offset counting includes stack junk** before your buffer — always confirm with the
  `41414141` marker.
- **Address bytes as data:** the target address you embed must dodge badchars; if the
  format function stops at `\x00`, split writes or reorder.
- **`%n` disabled:** some CRTs block `%n` by default (`_set_printf_count_output`). If it
  no-ops, you may be limited to reads.
- **Alignment:** your embedded addresses must sit exactly on a 4-byte arg boundary — pad
  the front of the buffer so `%N$` lands on them.
- **Use reads to beat ASLR, writes to redirect flow** — often you do BOTH: leak a base
  with `%p`, then `%n` a computed address.

→ Template: `02-templates/format_string.py`
