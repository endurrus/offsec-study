# Lab Setup — build once, practice forever

You need two machines on the same host-only / NAT network:
- **Windows victim** (where the vulnerable app + WinDbg run)
- **Kali attacker** (where your exploit `.py`, msfvenom, listeners run)

## Windows victim VM
- Windows 10 x64 (or Win7 x86 for the simplest, mitigation-light practice).
- **Disable Defender / real-time protection** in the lab (it eats shellcode). This VM is
  isolated — keep it off the internet.
- Install:
  - **WinDbg** — get "Debugging Tools for Windows" (part of the Windows SDK). The classic
    WinDbg is fine; WinDbg Preview works too.
  - **Python** (to run local helpers if you test on-box).
  - **mona.py** → drop into WinDbg's script path; needs **pykd**.

### Install mona + pykd (the ritual)
```
1. Get pykd.dll/pykd.pyd matching your WinDbg arch (x86 for 32-bit targets).
2. Place mona.py where WinDbg can load it (e.g. C:\mona\mona.py or the pykd ext dir).
3. In WinDbg:
   .load pykd.pyd
   !py mona
   !py mona config -set workingfolder c:\mona\%p
```
If `!py mona` errors, pykd/WinDbg arch mismatch is the usual cause (x86 vs x64).

### Toggle mitigations for graded practice
Practice each mitigation ON and OFF so you feel the difference:
- **DEP:** System Properties → Advanced → Performance → Data Execution Prevention.
- **ASLR:** per-app via EMET/Windows Exploit Protection, or use apps compiled without
  `/DYNAMICBASE`. `mona mod` tells you what's actually on.

## Kali attacker VM
Already has what you need:
```bash
which msfvenom msfconsole nc
msf-pattern_create -l 100     # confirm the msf pattern tools exist
```
Optional niceties: `rlwrap` (better shells), `python3`.

## Network sanity check
```bash
# From Kali, confirm you can reach the victim's service port:
nc -vn <victim_ip> 9999
```
If refused: firewall on victim, wrong network mode, or service not running.

## Snapshot discipline
Take a **clean snapshot** of the victim after setup. Every time you crash the service
into a weird state, roll back. You'll do this dozens of times — make it one click.

## Recommended first target: VulnServer
Small, purpose-built vulnerable TCP server. Classic OSCP/OSED practice.
```
Runs on port 9999. Commands like TRUN, GMON, GTER, KSTET each hide a different bug.
Start it on the victim: vulnserver.exe   (listens on 9999)
```
Full worked exploit: `05-labs/vulnserver-trun-walkthrough.md`.
Ordered practice path: `05-labs/practice-progression.md`.

## Other free practice targets
- **Brainpan** (VulnHub) — classic BOF box, end-to-end.
- **Freefloat FTP**, **Minishare**, **SLMail**, **Easy File Sharing Web Server** —
  well-documented real-app overflows (many on exploit-db with writeups to check yourself).
- **crossfire**, **War-FTP** — SEH practice.
Practice on apps **you are authorized to test** (your own lab copies). Never point these
at anything you don't own.
