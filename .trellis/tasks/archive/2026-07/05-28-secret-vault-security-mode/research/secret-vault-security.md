# Secret Vault security research

## Sources

* Libsodium password hashing docs: https://doc.libsodium.org/password_hashing
* Libsodium secretstream docs: https://libsodium.gitbook.io/doc/secret-key_cryptography/secretstream
* Tor stream isolation specification: https://spec.torproject.org/path-spec/stream-isolation.html
* Tor Project oniux introduction: https://blog.torproject.org/introducing-oniux-tor-isolation-using-linux-namespaces/

## Findings

* Password-derived vault keys should use a memory-hard password hashing/KDF path. Libsodium supports Argon2id for this class of use.
* File or JSONL stream encryption should use authenticated encryption, preferably a secretstream API such as `crypto_secretstream_xchacha20poly1305`, so integrity failure is detected and plaintext is never accepted silently.
* Tor stream isolation matters because different logical sessions/accounts should not share circuits. Secret sessions should provide unique per-session isolation tokens when using SOCKS authentication.
* Application-level proxy settings are weaker than process or network-namespace isolation. Tor Project's oniux design is relevant because it routes an arbitrary Linux program through Tor using kernel namespaces and reduces direct-network leak risk.

## Design Implications

* Secret mode must be fail-closed when the proxy/Tor chain is not configured or unhealthy.
* Secret password entry must be UI-local only, never model-visible.
* Secret storage should be separated from normal history/harness storage so accidental normal history scans do not leak metadata or plaintext.
* Production-grade encryption should use an audited crypto dependency. If unavailable, the UI must report that strong encryption is unavailable rather than downgrade silently.
