# Bind Shell vs Reverse Shell — quick notes

## Reverse shell (default choice)
Target **connects out** to YOU. Beats inbound firewalls/NAT on the target side.
API chain: `LoadLibraryA(ws2_32) → WSAStartup → WSASocketA → connect → CreateProcessA(cmd)`.
Catch: `nc -lvnp <port>` on your box.

## Bind shell
Target **listens** and YOU connect in. Needs an inbound port open on the target.
API chain differs at the socket stage:
```
WSASocketA → bind(s, sockaddr_in{AF_INET, htons(PORT), INADDR_ANY}, 16)
           → listen(s, 0)
           → accept(s, 0, 0)   -> returns the CLIENT socket
           → CreateProcessA("cmd", ... std handles = accepted socket)
```
Connect in with: `nc <target> <port>`.

## When to pick which
| Situation | Use |
|---|---|
| target behind NAT / outbound allowed | **reverse** |
| you can't open a listener / egress filtered but ingress open | **bind** |
| exam default, most reliable | **reverse** |

## Byte-budget note
Bind is slightly larger (bind+listen+accept vs. connect). If space is tight, reverse is
usually shorter. Either way, if it doesn't fit → egghunter to a bigger buffer.

## Port/IP encoding gotcha
The port and IP become literal bytes in the shellcode. Pick values whose byte
representation avoids your badchars, OR xor-encode them and decode at runtime.
- Port 443 = `0x01BB` (network order) — often clean.
- Port 4444 = `0x115C` — check for badchars.
- IP `127.0.0.1` = `0x7f000001` → bytes `01 00 00 7f` contains `\x00` → encode it.
