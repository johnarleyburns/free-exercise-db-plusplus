# Language capabilities

| Language | v1.10 capability |
| --- | --- |
| Python | Full reference implementation |
| Swift | Legacy/partial |
| Kotlin | Partial |
| R | Research/partial |

Cross-language intent fixtures are parity inputs for later work; this release does not claim implementation parity.

The fixture oracle is `fixtures/cross-language/intent/`. Each case contains
structured inputs, canonical expected resolution (and flagship generation),
and metadata recording policy and artifact versions. v1.11 may consume these
fixtures; it does not begin that parity implementation here.
