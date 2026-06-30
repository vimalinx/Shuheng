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
    ensure_secret_vault_dirs,
    load_secret_vault_meta,
    secret_b64,
    secret_create_vault,
    secret_crypto_available,
    secret_decrypt_bytes,
    secret_derive_key,
    secret_encrypt_bytes,
    secret_import_key_id,
    secret_read_json_from_path,
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
