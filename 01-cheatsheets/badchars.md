# Bad Characters — the reference + the ritual

Bad chars are byte values the target mangles/truncates before your payload reaches
memory. Missing one = a broken exploit that looks correct. **Never assume — verify.**

## The usual suspects (still verify every time)
| Byte | Name | Why it's often bad |
|---|---|---|
| `\x00` | NULL | string terminator — kills C string copies. Almost ALWAYS bad. |
| `\x0a` | LF `\n` | line terminator in text protocols |
| `\x0d` | CR `\r` | line terminator; HTTP/SMTP/etc. |
| `\x20` | space | delimiter in many parsers |
| `\x09` | TAB | delimiter |
| `\xff` | | occasional in length/terminator logic |
| `\x25` | `%` | format-string / URL contexts |
| `\x26` | `&` | param separators |
| `\x2f` `\x5c` | `/` `\` | path parsers |

Protocol hints:
- **HTTP:** `\x00 \x0a \x0d \x20` at least.
- **Text/line-based:** `\x00 \x0a \x0d`.
- **Unicode/UTF-16 apps:** everything gets `\x00`-interleaved → different game (venetian).

## The ritual (do this EXACTLY, every exploit)
```
1. Generate a clean bytearray excluding known-bad:
   !py mona bytearray -b "\x00"

2. Put the array in your buffer where it lands in controllable memory (usually ESP).
   The array is \x01\x02...\xff (minus excluded).

3. Crash, find where the array landed:
   dd esp   (or wherever mona findmsp said your buffer sits)

4. Compare:
   !py mona compare -f c:\mona\<proc>\bytearray.bin -a <landing_addr>

5. mona lists mangled/missing bytes. Add each to -b, regenerate, resend, recompare.

6. Repeat until: "possibly bad chars: none" / "unmodified".
```

## Reading mona compare output
- **"unmodified"** → clean, you're done.
- A byte listed as changed → it's bad OR it's the *start* of a truncation (everything
  after a truncating byte also looks wrong — fix the FIRST bad byte, recompare, the
  rest often clears up).
- **Corruption cascades:** one bad byte can shift/eat the rest. Always trust the FIRST
  reported bad byte, remove it, retest before removing more.

## Generate the test array yourself (no mona)
```python
badchars = b"\x00"
allbytes = bytes(b for b in range(1,256) if b not in badchars)
# len should be 255 - len(excluded)
print(''.join('\\x%02x'%b for b in allbytes))
```

## Once you know the badchars, thread them everywhere
- `msfvenom ... -b "\x00\x0a\x0d..."`
- `!py mona jmp -r esp -cpb "\x00\x0a\x0d..."`
- `!py mona seh -cpb "..."`
- `!py mona rop -cpb "..."`
Same set, every tool. A gadget/jump address containing a badchar is silently useless.

## Debugging "it worked in the debugger but not live"
- Attaching vs. running standalone can change addresses/heap → recheck.
- A badchar you missed truncated the payload → the tail (real shellcode) never arrived.
- Encoded payload contained a badchar the encoder couldn't avoid → widen `-b` or re-encode.
