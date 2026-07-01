"""Tests for Secret Vault crypto primitives.

Verifies the argon2id key derivation + xchacha20-poly1305 AEAD round-trip,
error handling, and nonce/aad properties. Requires PyNaCl (a project dep).
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from ga_tui import app as app_module
from ga_tui.secret_vault import (
    NACL_XCHACHA_ABYTES,
    NACL_XCHACHA_KEYBYTES,
    NACL_XCHACHA_NPUBBYTES,
    SecretVaultPaths,
    SecretVaultError,
    SECRET_DEFAULT_TOR_SOCKS,
    ensure_secret_vault_dirs,
    load_secret_vault_meta,
    normalize_secret_proxy_endpoint,
    parse_secret_import_args,
    parse_secret_proxy_chain,
    resolve_secret_imported_session_entry,
    resolve_secret_native_session_entry,
    messages_from_secret_import_payload as secret_import_messages_from_payload,
    secret_b64,
    secret_create_vault,
    secret_crypto_available,
    secret_decrypt_bytes,
    secret_derive_key,
    secret_encrypt_bytes,
    secret_import_represented_by_native,
    secret_import_key_id,
    secret_native_entry_for_import_entry,
    secret_read_json_from_path,
    secret_session_state_payload,
    secret_session_title_for_messages,
    secret_session_id_from_path,
    secret_storage_path_for_session,
    secret_unb64,
    secret_unlock_vault,
    secret_write_json_for_session,
    write_secret_vault_meta,
)


pytestmark = pytest.mark.skipif(
    not secret_crypto_available(),
    reason="PyNaCl/libsodium not available",
)


@pytest.fixture()
def key() -> bytes:
    return secret_derive_key("correct horse battery staple", os.urandom(16))


class TestKeyDerivation:
    def test_key_length(self) -> None:
        key = secret_derive_key("password", os.urandom(16))
        assert len(key) == NACL_XCHACHA_KEYBYTES

    def test_same_password_different_salt_different_key(self) -> None:
        salt1 = os.urandom(16)
        salt2 = os.urandom(16)
        k1 = secret_derive_key("pw", salt1)
        k2 = secret_derive_key("pw", salt2)
        assert k1 != k2

    def test_wrong_salt_length_raises(self) -> None:
        with pytest.raises(SecretVaultError, match="salt"):
            secret_derive_key("pw", b"tooshort")

    def test_empty_password_still_derives(self) -> None:
        # Empty password is allowed by the KDF; the vault policy (min chars)
        # is enforced elsewhere.
        key = secret_derive_key("", os.urandom(16))
        assert len(key) == NACL_XCHACHA_KEYBYTES


class TestEncryptDecrypt:
    def test_roundtrip(self, key: bytes) -> None:
        plaintext = b"secret message"
        sealed = secret_encrypt_bytes(key, plaintext)
        assert secret_decrypt_bytes(key, sealed) == plaintext

    def test_ciphertext_includes_nonce(self, key: bytes) -> None:
        sealed = secret_encrypt_bytes(key, b"data")
        # nonce is prepended: total = nonce + ciphertext + tag
        assert len(sealed) == NACL_XCHACHA_NPUBBYTES + len(b"data") + NACL_XCHACHA_ABYTES

    def test_nonce_is_random(self, key: bytes) -> None:
        s1 = secret_encrypt_bytes(key, b"data")
        s2 = secret_encrypt_bytes(key, b"data")
        # Nonces (first NPUBBYTES) must differ.
        assert s1[:NACL_XCHACHA_NPUBBYTES] != s2[:NACL_XCHACHA_NPUBBYTES]

    def test_wrong_key_fails(self, key: bytes) -> None:
        sealed = secret_encrypt_bytes(key, b"data")
        other_key = secret_derive_key("other", os.urandom(16))
        with pytest.raises(SecretVaultError):
            secret_decrypt_bytes(other_key, sealed)

    def test_tampered_ciphertext_fails(self, key: bytes) -> None:
        sealed = bytearray(secret_encrypt_bytes(key, b"data"))
        # Flip a bit in the ciphertext body (after nonce).
        sealed[-1] ^= 0x01
        with pytest.raises(SecretVaultError):
            secret_decrypt_bytes(key, bytes(sealed))

    def test_aad_mismatch_fails(self, key: bytes) -> None:
        sealed = secret_encrypt_bytes(key, b"data", aad=b"context-a")
        with pytest.raises(SecretVaultError):
            secret_decrypt_bytes(key, sealed, aad=b"context-b")

    def test_aad_match_succeeds(self, key: bytes) -> None:
        sealed = secret_encrypt_bytes(key, b"data", aad=b"context-a")
        assert secret_decrypt_bytes(key, sealed, aad=b"context-a") == b"data"

    def test_empty_key_rejected(self) -> None:
        with pytest.raises(SecretVaultError, match="key"):
            secret_encrypt_bytes(b"", b"data")

    def test_wrong_key_length_rejected(self) -> None:
        with pytest.raises(SecretVaultError, match="key"):
            secret_encrypt_bytes(b"short", b"data")

    def test_too_short_ciphertext_rejected(self, key: bytes) -> None:
        with pytest.raises(SecretVaultError, match="过短"):
            secret_decrypt_bytes(key, b"short")

    def test_decrypt_empty_plaintext(self, key: bytes) -> None:
        sealed = secret_encrypt_bytes(key, b"")
        assert secret_decrypt_bytes(key, sealed) == b""


class TestBase64Helpers:
    def test_b64_roundtrip(self) -> None:
        data = os.urandom(32)
        assert secret_unb64(secret_b64(data)) == data

    def test_unb64_invalid_raises(self) -> None:
        with pytest.raises(Exception):
            secret_unb64("not!!!valid!!!base64!!!")


class TestImportKeyId:
    def test_stable(self) -> None:
        pk = os.urandom(32)
        assert secret_import_key_id(pk) == secret_import_key_id(pk)

    def test_different_keys_different_id(self) -> None:
        assert secret_import_key_id(os.urandom(32)) != secret_import_key_id(os.urandom(32))

    def test_truncated_to_24(self) -> None:
        pk = os.urandom(32)
        assert len(secret_import_key_id(pk)) == 24


class TestAppCompatibility:
    def test_app_reexports_crypto_helpers(self) -> None:
        assert app_module.SecretVaultError is SecretVaultError
        assert app_module.secret_crypto_available is secret_crypto_available
        assert app_module.secret_encrypt_bytes is secret_encrypt_bytes
        assert app_module.secret_decrypt_bytes is secret_decrypt_bytes
        assert app_module.NACL_XCHACHA_KEYBYTES == NACL_XCHACHA_KEYBYTES

    def test_app_reexports_secret_value_helpers(self) -> None:
        assert app_module.secret_session_title_for_messages is secret_session_title_for_messages
        assert app_module.secret_session_state_payload is secret_session_state_payload
        assert app_module.parse_secret_import_args is parse_secret_import_args
        assert app_module.parse_secret_proxy_chain is parse_secret_proxy_chain
        assert app_module.normalize_secret_proxy_endpoint is normalize_secret_proxy_endpoint
        assert app_module.resolve_secret_imported_session_entry is resolve_secret_imported_session_entry
        assert app_module.resolve_secret_native_session_entry is resolve_secret_native_session_entry
        assert app_module.secret_import_represented_by_native is secret_import_represented_by_native


class TestSecretValueHelpers:
    def test_secret_session_title_normalization(self) -> None:
        messages = [
            app_module.Message("system", "ignored"),
            app_module.Message("user", "  迁移普通会话到 Secret  "),
            app_module.Message("assistant", "done"),
        ]

        assert secret_session_title_for_messages("Secret: 手动标题", messages) == "手动标题"
        assert secret_session_title_for_messages("Secret Vault", messages) == "迁移普通会话到 Secret"
        assert secret_session_title_for_messages("", []) == "Secret 会话"

    def test_secret_session_state_payload_normalizes_title(self) -> None:
        messages = [app_module.Message("user", "保存这个 Secret 会话")]

        payload = secret_session_state_payload("../secret id", "Secret: main", messages, source="unit")

        assert payload["schema_version"] == "secret.session_state.v1"
        assert payload["session_id"] == "..-secret-id"
        assert payload["title"] == "保存这个 Secret 会话"
        assert payload["source"] == "unit"
        assert payload["messages"][0]["role"] == "user"

    def test_import_arg_and_proxy_value_helpers(self) -> None:
        assert parse_secret_import_args("") == ("delete", "current")
        assert parse_secret_import_args("archive 2") == ("archive", "2")
        assert parse_secret_import_args("删除 id:abc") == ("delete", "id:abc")
        assert parse_secret_import_args("target only") == ("delete", "target only")
        assert parse_secret_proxy_chain("tor -> 127.0.0.1:9051; https://proxy") == [
            "tor",
            "127.0.0.1:9051",
            "https://proxy",
        ]
        assert normalize_secret_proxy_endpoint("tor") == SECRET_DEFAULT_TOR_SOCKS
        assert normalize_secret_proxy_endpoint("127.0.0.1:9051") == "socks5h://127.0.0.1:9051"
        assert normalize_secret_proxy_endpoint("http://proxy:8080") == "http://proxy:8080"

    def test_imported_session_resolver_matches_current_candidates(self) -> None:
        entries = [
            {"path": "/vault/broken.secret", "error": "bad"},
            {
                "path": "/vault/session-a/imported-sessions/alpha.secret",
                "stable_id": "stable-alpha",
                "basename": "source-alpha.txt",
                "title": "Alpha Title",
            },
            {
                "path": "/vault/session-b/imported-sessions/beta.secret",
                "stable_id": "stable-beta",
                "basename": "source-beta.txt",
                "title": "Beta Title",
            },
        ]

        entry, error = resolve_secret_imported_session_entry(entries, "S2")
        assert entry is entries[2]
        assert error == ""

        entry, error = resolve_secret_imported_session_entry(entries, "id:stable-alpha")
        assert entry is entries[1]
        assert error == ""

        entry, error = resolve_secret_imported_session_entry(entries, "secret_import:beta.secret")
        assert entry is entries[2]
        assert error == ""

        entry, error = resolve_secret_imported_session_entry(entries, "Alpha Title")
        assert entry is None
        assert error == "找不到 Secret 导入会话，请先 /Secret sessions 查看编号。"

    def test_imported_session_resolver_errors(self) -> None:
        assert resolve_secret_imported_session_entry([], "1") == (
            None,
            "Secret Vault 里没有可打开的已导入会话。",
        )
        assert resolve_secret_imported_session_entry([{"error": "bad"}], "") == (
            None,
            "Secret Vault 里没有可打开的已导入会话。",
        )
        assert resolve_secret_imported_session_entry([{"path": "/vault/a.secret"}], "") == (
            None,
            "Usage: /Secret open <编号|id|文件名>",
        )
        assert resolve_secret_imported_session_entry([{"path": "/vault/a.secret"}], "2") == (
            None,
            "索引越界: 1-1",
        )
        duplicate_entries = [
            {"path": "/vault/a/dup.secret", "stable_id": "same"},
            {"path": "/vault/b/dup.secret", "stable_id": "same"},
        ]
        assert resolve_secret_imported_session_entry(duplicate_entries, "same") == (
            None,
            "匹配到多个 Secret 导入会话：same",
        )

    def test_native_session_resolver_matches_current_candidates(self) -> None:
        entries = [
            {"session_id": "broken", "error": "bad"},
            {"session_id": "alpha", "title": "Alpha Secret"},
            {"session_id": "beta", "title": "Beta Secret"},
        ]

        entry, error = resolve_secret_native_session_entry(entries, "2")
        assert entry is entries[2]
        assert error == ""

        entry, error = resolve_secret_native_session_entry(entries, "secret_session:beta")
        assert entry is entries[2]
        assert error == ""

        entry, error = resolve_secret_native_session_entry(entries, "Alpha Secret")
        assert entry is entries[1]
        assert error == ""

    def test_native_session_resolver_errors(self) -> None:
        assert resolve_secret_native_session_entry([], "1") == (
            None,
            "Secret Vault 里没有可打开的加密会话。",
        )
        assert resolve_secret_native_session_entry([{"error": "bad"}], "") == (
            None,
            "Secret Vault 里没有可打开的加密会话。",
        )
        assert resolve_secret_native_session_entry([{"session_id": "a"}], "") == (
            None,
            "Usage: /Secret open-session <编号|session_id>",
        )
        assert resolve_secret_native_session_entry([{"session_id": "a"}], "2") == (
            None,
            "索引越界: 1-1",
        )
        duplicate_entries = [
            {"session_id": "a", "title": "Same"},
            {"session_id": "b", "title": "Same"},
        ]
        assert resolve_secret_native_session_entry(duplicate_entries, "Same") == (
            None,
            "匹配到多个 Secret 会话：Same",
        )

    def test_app_resolver_wrappers_delegate_to_secret_vault_helpers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        imported_entries = [{"path": "/vault/a.secret"}, {"path": "/vault/b.secret"}]
        native_entries = [{"session_id": "a"}, {"session_id": "b"}]

        monkeypatch.setattr(app_module, "secret_imported_session_entries", lambda state: imported_entries)
        monkeypatch.setattr(
            app_module,
            "secret_native_session_entries",
            lambda state, *, include_payload=False: native_entries if include_payload else [],
        )

        imported_entry, imported_error = app_module.resolve_secret_imported_session(object(), "2")
        native_entry, native_error = app_module.resolve_secret_native_session(object(), "S2")

        assert imported_entry is imported_entries[1]
        assert imported_error == ""
        assert native_entry is native_entries[1]
        assert native_error == ""

    def test_imported_entry_native_link_matches_existing_fields(self) -> None:
        import_entry = {
            "path": "/vault/session/imported-sessions/alpha.secret",
            "stable_id": "stable-alpha",
            "title": "Alpha Import",
        }

        assert secret_import_represented_by_native(
            import_entry,
            [{"origin_import_path": "/vault/session/imported-sessions/alpha.secret"}],
        )
        assert secret_import_represented_by_native(
            import_entry,
            [{"origin_import_path": "/tmp/other.secret", "origin_stable_id": "stable-alpha"}],
        )
        assert secret_import_represented_by_native(
            import_entry,
            [{"origin_import_path": "/tmp/other.secret", "origin_stable_id": "other", "title": "Alpha Import"}],
        )
        assert not secret_import_represented_by_native(
            import_entry,
            [{"origin_import_path": "/tmp/other.secret", "origin_stable_id": "other", "title": "Other"}],
        )

    def test_imported_entry_native_link_ignores_empty_values(self) -> None:
        assert not secret_import_represented_by_native(
            {"path": "", "stable_id": "", "title": ""},
            [{"origin_import_path": "", "origin_stable_id": "", "title": ""}],
        )
        assert not secret_import_represented_by_native(
            {"path": "", "stable_id": "", "title": ""},
            [{"origin_import_path": "/tmp/other.secret", "origin_stable_id": "other", "title": "Other"}],
        )

    def test_native_entry_for_import_entry_returns_first_non_error_match(self) -> None:
        import_entry = {
            "path": "/vault/session/imported-sessions/alpha.secret",
            "stable_id": "stable-alpha",
            "title": "Alpha Import",
        }
        native_entries = [
            {"session_id": "bad", "origin_stable_id": "stable-alpha", "error": "cannot decrypt"},
            {"session_id": "native-alpha", "origin_stable_id": "stable-alpha", "title": "Other"},
            {"session_id": "native-title", "origin_stable_id": "other", "title": "Alpha Import"},
        ]

        assert secret_native_entry_for_import_entry(import_entry, native_entries) is native_entries[1]
        assert secret_native_entry_for_import_entry(
            {"path": "/vault/none.secret", "stable_id": "none", "title": "None"},
            native_entries,
        ) is None

    def test_app_native_entry_for_import_entry_wrapper_loads_state_entries(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        native_entries = [
            {"session_id": "native-alpha", "origin_stable_id": "stable-alpha"},
        ]

        def fake_secret_native_session_entries(state: object, *, include_payload: bool = False) -> list[dict[str, str]]:
            assert include_payload is False
            return native_entries

        monkeypatch.setattr(app_module, "secret_native_session_entries", fake_secret_native_session_entries)

        assert app_module.secret_native_entry_for_import_entry(
            object(),
            {"path": "", "stable_id": "stable-alpha", "title": ""},
        ) is native_entries[0]

    def test_secret_import_payload_message_helper_uses_parsed_pairs(self) -> None:
        pair_rows = [("user prompt", "assistant response")]

        def parse_pairs(raw_log: str) -> list[tuple[str, str]]:
            assert raw_log == "parsed log"
            return pair_rows

        def messages_from_pairs(
            pairs: list[tuple[str, str]],
            rounds: int,
        ) -> tuple[list[app_module.Message], int, int]:
            assert pairs is pair_rows
            assert rounds == 2
            return [app_module.Message("user", "parsed user"), app_module.Message("assistant", "parsed assistant")], 2, 5

        messages, loaded_rounds, total_rounds, message_count = secret_import_messages_from_payload(
            {"raw_log_text": "parsed log"},
            parse_pairs=parse_pairs,
            messages_from_pairs=messages_from_pairs,
            restore_display_rounds=2,
        )

        assert [(msg.role, msg.content) for msg in messages] == [
            ("user", "parsed user"),
            ("assistant", "parsed assistant"),
        ]
        assert loaded_rounds == 2
        assert total_rounds == 5
        assert message_count == 2

    def test_secret_import_payload_message_helper_fallbacks(self) -> None:
        def parse_pairs(raw_log: str) -> list[tuple[str, str]]:
            return []

        def messages_from_pairs(
            pairs: list[tuple[str, str]],
            rounds: int,
        ) -> tuple[list[app_module.Message], int, int]:
            return [], 0, 0

        messages, loaded_rounds, total_rounds, message_count = secret_import_messages_from_payload(
            {"raw_log_text": "  raw assistant only  "},
            parse_pairs=parse_pairs,
            messages_from_pairs=messages_from_pairs,
            restore_display_rounds=3,
        )
        assert [(msg.role, msg.content) for msg in messages] == [("assistant", "raw assistant only")]
        assert (loaded_rounds, total_rounds, message_count) == (1, 1, 1)

        messages, loaded_rounds, total_rounds, message_count = secret_import_messages_from_payload(
            {},
            parse_pairs=parse_pairs,
            messages_from_pairs=messages_from_pairs,
            restore_display_rounds=3,
        )
        assert [(msg.role, msg.content) for msg in messages] == [("system", "Secret 导入会话为空。")]
        assert (loaded_rounds, total_rounds, message_count) == (0, 0, 1)

    def test_app_import_payload_message_wrapper_injects_history_helpers(self, monkeypatch: pytest.MonkeyPatch) -> None:
        pair_rows = [("user prompt", "assistant response")]

        monkeypatch.setattr(app_module, "_pairs", lambda raw_log: pair_rows if raw_log == "parsed log" else [])
        monkeypatch.setattr(app_module, "RESTORE_DISPLAY_ROUNDS", 7)

        def fake_history_messages_from_pairs(
            pairs: list[tuple[str, str]],
            rounds: int,
        ) -> tuple[list[app_module.Message], int, int]:
            assert pairs is pair_rows
            assert rounds == 7
            return [app_module.Message("assistant", "from app wrapper")], 1, 1

        monkeypatch.setattr(app_module, "history_messages_from_pairs", fake_history_messages_from_pairs)

        messages, loaded_rounds, total_rounds, message_count = app_module.messages_from_secret_import_payload(
            {"raw_log_text": "parsed log"}
        )

        assert [(msg.role, msg.content) for msg in messages] == [("assistant", "from app wrapper")]
        assert (loaded_rounds, total_rounds, message_count) == (1, 1, 1)


class TestSecretVaultStorage:
    def paths(self, tmp_path: Path) -> SecretVaultPaths:
        root = tmp_path / "secret_vault"
        return SecretVaultPaths(
            vault_dir=str(root),
            meta_path=str(root / "vault.json"),
            data_dir=str(root / "data"),
            sessions_dir=str(root / "data" / "sessions"),
        )

    def test_meta_round_trip_uses_explicit_paths(self, tmp_path: Path) -> None:
        paths = self.paths(tmp_path)

        ensure_secret_vault_dirs(paths)
        write_secret_vault_meta(paths, {"schema_version": "secretvault.test", "value": 1})

        assert load_secret_vault_meta(paths)["value"] == 1
        assert (tmp_path / "secret_vault" / "vault.json").exists()

    def test_encrypted_json_round_trip(self, tmp_path: Path) -> None:
        paths = self.paths(tmp_path)
        ok, key, created = secret_create_vault(paths, "Aa1!aaaa")
        assert ok and key, created

        wrote, path, warning = secret_write_json_for_session(
            paths,
            unlocked=True,
            key=key,
            current_session_id="secret_session",
            session_id="secret_session",
            kind="checks",
            name="payload",
            payload={"secret": "plaintext-marker"},
        )

        assert wrote, path
        assert warning == ""
        raw = Path(path).read_bytes()
        assert b"plaintext-marker" not in raw
        ok, payload, detail = secret_read_json_from_path(
            paths,
            unlocked=True,
            key=key,
            import_private_key=None,
            kind="checks",
            path=path,
            session_id="secret_session",
        )
        assert ok, detail
        assert payload == {"secret": "plaintext-marker"}
        assert secret_session_id_from_path(paths, path) == "secret_session"

    def test_create_then_unlock_vault(self, tmp_path: Path) -> None:
        paths = self.paths(tmp_path)
        created, key, message = secret_create_vault(paths, "Aa1!aaaa")
        assert created and key, message

        unlocked, unlocked_key, unlocked_message = secret_unlock_vault(paths, "Aa1!aaaa")

        assert unlocked, unlocked_message
        assert unlocked_key == key

    def test_storage_path_sanitizes_components(self, tmp_path: Path) -> None:
        paths = self.paths(tmp_path)

        path = secret_storage_path_for_session(paths, "../session", "../kind", "../name")

        assert str(tmp_path / "secret_vault" / "data" / "sessions") in path
        assert path.endswith("..-name.secret")
