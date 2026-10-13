# RandomX execution components

Accepted hardware includes the [v2 AES mixer](aes/README.md),
[ordered iteration stores](iteration/README.md) and [iteration memory engine](engine/README.md).
The new [native integer executor](execute/README.md) connects actual bounded bytecode
arithmetic; task54's independent new-work review remains pending. Complete core/FP,
branch/multiply, physical-memory, full-hash and calibrated-PPA gates remain open.

Earlier planning entry (retained verbatim):

```text
# Future RTL work

No processor RTL implemented. Advance after M3/M4 gates; isolate core, cache and SoC changes and document verification interfaces.
```
