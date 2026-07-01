"""Low-level Secret Vault crypto, metadata, and encrypted storage helpers."""
from __future__ import annotations

import base64
import glob
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional

try:
    from .history_titles import suggested_session_title
    from .text_utils import compact_title
    from .ui_types import Message
except Exception:  # pragma: no cover - direct module execution compatibility
    from history_titles import suggested_session_title  # type: ignore
    from text_utils import compact_title  # type: ignore
    from ui_types import Message  # type: ignore

try:
    from nacl import pwhash as nacl_pwhash
    from nacl.bindings import (
        crypto_aead_xchacha20poly1305_ietf_ABYTES as NACL_XCHACHA_ABYTES,
        crypto_aead_xchacha20poly1305_ietf_KEYBYTES as NACL_XCHACHA_KEYBYTES,
        crypto_aead_xchacha20poly1305_ietf_NPUBBYTES as NACL_XCHACHA_NPUBBYTES,
        crypto_aead_xchacha20poly1305_ietf_decrypt as nacl_xchacha_decrypt,
        crypto_aead_xchacha20poly1305_ietf_encrypt as nacl_xchacha_encrypt,
    )
    from nacl.public import PrivateKey as NaclPrivateKey
    from nacl.public import PublicKey as NaclPublicKey
    from nacl.public import SealedBox as NaclSealedBox

    SECRET_CRYPTO_IMPORT_ERROR = ""
except Exception as exc:  # pragma: no cover - exercised only without PyNaCl/libsodium
    nacl_pwhash = None
    nacl_xchacha_encrypt = None
    nacl_xchacha_decrypt = None
    NaclPrivateKey = None
    NaclPublicKey = None
    NaclSealedBox = None
    NACL_XCHACHA_ABYTES = 16
    NACL_XCHACHA_KEYBYTES = 32
    NACL_XCHACHA_NPUBBYTES = 24
    SECRET_CRYPTO_IMPORT_ERROR = f"{type(exc).__name__}: {exc}"


SECRET_VAULT_SENTINEL = b"GenericAgent-TUI Secret Vault v1"
SECRET_IMPORT_KEY_AAD = b"secret-vault:sealed-import-key:v1"
SECRET_IMPORT_SEALED_SCHEMA = "secret.sealed_import.v1"
SECRET_IMPORT_DROPBOX_META_KEY = "sealed_import"
SECRET_SUBAGENT_SESSION_ID = "secret_subagents"
SECRET_SUBAGENT_META_KIND = "subagents"
SECRET_SUBAGENT_MEMORY_KIND = "subagent-memory"
SECRET_SUBAGENT_CHAT_KIND = "subagent-chat"
SECRET_VAULT_MIN_PASSWORD_CHARS = 8
SECRET_VAULT_PASSWORD_RULE_TEXT = (
    f"至少 {SECRET_VAULT_MIN_PASSWORD_CHARS} 个字符，并包含大写字母、小写字母、数字和特殊字符"
)
SECRET_NETWORK_CHAIN_ENV = "GA_TUI_SECRET_PROXY_CHAIN"
SECRET_TOR_SOCKS_ENV = "GA_TUI_SECRET_TOR_SOCKS"
SECRET_AUTO_TOR_ENV = "GA_TUI_SECRET_AUTO_TOR"
SECRET_DEFAULT_TOR_SOCKS = "socks5h://127.0.0.1:9050"
SECRET_IMPORT_SESSION_PREFIX = "secret_import:"
SECRET_NATIVE_SESSION_PREFIX = "secret_session:"
SECRET_IMPORT_DISPOSITION_ALIASES = {
    "delete": "delete",
    "del": "delete",
    "remove": "delete",
    "rm": "delete",
    "删除": "delete",
    "archive": "archive",
    "archived": "archive",
    "归档": "archive",
}


@dataclass(frozen=True)
class SecretVaultPaths:
    vault_dir: str
    meta_path: str
    data_dir: str
    sessions_dir: str


class SecretVaultError(RuntimeError):
    pass


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())


def short_uid(prefix: str) -> str:
    return f"{prefix}_{time.time_ns():x}_{os.getpid():x}"


def normalized_path(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path or "."))


def write_text_atomic(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def write_bytes_atomic(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)


def secret_crypto_available() -> bool:
    return bool(nacl_pwhash and nacl_xchacha_encrypt and nacl_xchacha_decrypt and NaclPrivateKey and NaclPublicKey and NaclSealedBox)


def secret_crypto_status_text() -> str:
    if secret_crypto_available():
        return "available:xchacha20-poly1305+argon2id"
    return f"unavailable:{SECRET_CRYPTO_IMPORT_ERROR or 'PyNaCl is not installed'}"


def ensure_secret_vault_dirs(paths: SecretVaultPaths) -> None:
    os.makedirs(paths.sessions_dir, mode=0o700, exist_ok=True)
    for path in (paths.vault_dir, paths.data_dir, paths.sessions_dir):
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass


def secret_b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def secret_unb64(text: str) -> bytes:
    return base64.b64decode((text or "").encode("ascii"), validate=True)


def secret_derive_key(password: str, salt: bytes) -> bytes:
    if not secret_crypto_available():
        raise SecretVaultError("Secret Vault 需要 PyNaCl/libsodium 才能启用强加密。")
    try:
        salt_bytes = int(getattr(nacl_pwhash.argon2id, "SALTBYTES", 16))
        opslimit = int(getattr(nacl_pwhash.argon2id, "OPSLIMIT_SENSITIVE"))
        memlimit = int(getattr(nacl_pwhash.argon2id, "MEMLIMIT_SENSITIVE"))
        if len(salt) != salt_bytes:
            raise SecretVaultError("Secret Vault salt 长度无效。")
        return nacl_pwhash.argon2id.kdf(
            NACL_XCHACHA_KEYBYTES,
            (password or "").encode("utf-8"),
            salt,
            opslimit=opslimit,
            memlimit=memlimit,
        )
    except SecretVaultError:
        raise
    except Exception as exc:
        raise SecretVaultError(f"Secret Vault 密钥派生失败: {type(exc).__name__}: {exc}") from exc


def secret_encrypt_bytes(key: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
    if not secret_crypto_available():
        raise SecretVaultError("Secret Vault 强加密不可用。")
    if not key or len(key) != NACL_XCHACHA_KEYBYTES:
        raise SecretVaultError("Secret Vault key 无效。")
    nonce = os.urandom(NACL_XCHACHA_NPUBBYTES)
    ciphertext = nacl_xchacha_encrypt(plaintext, aad, nonce, key)
    return nonce + ciphertext


def secret_decrypt_bytes(key: bytes, sealed: bytes, aad: bytes = b"") -> bytes:
    if not secret_crypto_available():
        raise SecretVaultError("Secret Vault 强加密不可用。")
    if len(sealed) < NACL_XCHACHA_NPUBBYTES + NACL_XCHACHA_ABYTES:
        raise SecretVaultError("Secret Vault 密文过短。")
    nonce = sealed[:NACL_XCHACHA_NPUBBYTES]
    ciphertext = sealed[NACL_XCHACHA_NPUBBYTES:]
    try:
        return nacl_xchacha_decrypt(ciphertext, aad, nonce, key)
    except Exception as exc:
        raise SecretVaultError("Secret Vault 密码错误或密文已损坏。") from exc


def secret_import_key_id(public_key: bytes) -> str:
    return hashlib.sha256(public_key).hexdigest()[:24]


def secret_import_key_record(meta: dict[str, Any]) -> dict[str, Any]:
    record = meta.get(SECRET_IMPORT_DROPBOX_META_KEY)
    return record if isinstance(record, dict) else {}


def secret_build_import_key_record(key: bytes) -> tuple[dict[str, Any], bytes]:
    if not secret_crypto_available() or NaclPrivateKey is None:
        raise SecretVaultError("Secret Vault 强加密不可用。")
    try:
        private_key = NaclPrivateKey.generate()
        private_bytes = bytes(private_key)
        public_bytes = bytes(private_key.public_key)
        encrypted_private = secret_encrypt_bytes(key, private_bytes, SECRET_IMPORT_KEY_AAD)
    except Exception as exc:
        raise SecretVaultError(f"Secret Vault 单向导入密钥创建失败：{type(exc).__name__}: {exc}") from exc
    return {
        "mode": "sealedbox.v1",
        "created_at": now_iso(),
        "public_key": secret_b64(public_bytes),
        "public_key_id": secret_import_key_id(public_bytes),
        "private_key_ciphertext": secret_b64(encrypted_private),
    }, private_bytes


def load_secret_vault_meta(paths: SecretVaultPaths) -> dict[str, Any]:
    try:
        with open(paths.meta_path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return {}
    return raw if isinstance(raw, dict) else {}


def write_secret_vault_meta(paths: SecretVaultPaths, meta: dict[str, Any]) -> None:
    ensure_secret_vault_dirs(paths)
    write_text_atomic(paths.meta_path, json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    try:
        os.chmod(paths.meta_path, 0o600)
    except OSError:
        pass


def secret_vault_exists(paths: SecretVaultPaths) -> bool:
    return bool(load_secret_vault_meta(paths).get("verifier_ciphertext"))


def secret_import_public_key_from_meta(
    meta: Optional[dict[str, Any]] = None,
    *,
    paths: Optional[SecretVaultPaths] = None,
) -> tuple[Optional[bytes], str, str]:
    if not secret_crypto_available() or NaclPublicKey is None:
        return None, "", f"Secret Vault 强加密不可用：{secret_crypto_status_text()}。请安装 PyNaCl 后再启用。"
    meta = meta if isinstance(meta, dict) else load_secret_vault_meta(paths) if paths is not None else {}
    if not meta.get("verifier_ciphertext"):
        return None, "", "Secret Vault 尚未初始化：首次创建仍需要输入密码以生成本地密钥。"
    record = secret_import_key_record(meta)
    public_text = str(record.get("public_key") or "")
    if not public_text:
        return None, "", "当前 Secret Vault 缺少单向导入公钥；请先 /Secret 解锁一次完成迁移，之后 /toSecret 不再需要密码。"
    try:
        public_bytes = secret_unb64(public_text)
        NaclPublicKey(public_bytes)
    except Exception as exc:
        return None, "", f"Secret Vault 单向导入公钥无效：{type(exc).__name__}: {exc}"
    key_id = str(record.get("public_key_id") or secret_import_key_id(public_bytes))
    return public_bytes, key_id, ""


def secret_import_private_key_from_meta(meta: dict[str, Any], key: bytes) -> tuple[Optional[bytes], str]:
    if not secret_crypto_available() or NaclPrivateKey is None:
        return None, f"Secret Vault 强加密不可用：{secret_crypto_status_text()}。"
    record = secret_import_key_record(meta)
    private_text = str(record.get("private_key_ciphertext") or "")
    if not private_text:
        return None, "Secret Vault 单向导入私钥缺失。"
    try:
        private_bytes = secret_decrypt_bytes(key, secret_unb64(private_text), SECRET_IMPORT_KEY_AAD)
        NaclPrivateKey(private_bytes)
    except Exception as exc:
        return None, f"Secret Vault 单向导入私钥不可用：{type(exc).__name__}: {exc}"
    return private_bytes, ""


def secret_load_or_create_import_private_key(paths: SecretVaultPaths, key: bytes) -> tuple[Optional[bytes], str]:
    meta = load_secret_vault_meta(paths)
    if not meta.get("verifier_ciphertext"):
        return None, "Secret Vault 尚未初始化。"
    if secret_import_key_record(meta):
        return secret_import_private_key_from_meta(meta, key)
    try:
        record, private_bytes = secret_build_import_key_record(key)
        meta[SECRET_IMPORT_DROPBOX_META_KEY] = record
        meta["updated_at"] = now_iso()
        write_secret_vault_meta(paths, meta)
        return private_bytes, "已为旧 Secret Vault 生成单向导入公钥。"
    except Exception as exc:
        return None, f"Secret Vault 单向导入公钥生成失败：{type(exc).__name__}: {exc}"


def secret_sealed_import_envelope(public_key: bytes, public_key_id: str, payload: dict[str, Any]) -> bytes:
    if not secret_crypto_available() or NaclPublicKey is None or NaclSealedBox is None:
        raise SecretVaultError("Secret Vault 强加密不可用。")
    try:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ciphertext = NaclSealedBox(NaclPublicKey(public_key)).encrypt(raw)
    except Exception as exc:
        raise SecretVaultError(f"Secret Vault 单向导入加密失败：{type(exc).__name__}: {exc}") from exc
    envelope = {
        "schema_version": SECRET_IMPORT_SEALED_SCHEMA,
        "encryption": "sealedbox.v1",
        "created_at": now_iso(),
        "public_key_id": public_key_id or secret_import_key_id(public_key),
        "ciphertext": secret_b64(ciphertext),
    }
    return json.dumps(envelope, ensure_ascii=False, sort_keys=True).encode("utf-8")


def secret_decrypt_sealed_import_envelope(private_key: Optional[bytes], sealed: bytes) -> dict[str, Any]:
    if not secret_crypto_available() or NaclPrivateKey is None or NaclSealedBox is None:
        raise SecretVaultError("Secret Vault 强加密不可用。")
    if not private_key:
        raise SecretVaultError("Secret Vault 单向导入私钥未载入；请重新 /Secret 解锁。")
    try:
        envelope = json.loads(sealed.decode("utf-8"))
    except Exception as exc:
        raise SecretVaultError("不是 Secret 单向导入封套。") from exc
    if not isinstance(envelope, dict) or envelope.get("schema_version") != SECRET_IMPORT_SEALED_SCHEMA:
        raise SecretVaultError("不是 Secret 单向导入封套。")
    try:
        ciphertext = secret_unb64(str(envelope.get("ciphertext") or ""))
        raw = NaclSealedBox(NaclPrivateKey(private_key)).decrypt(ciphertext)
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise SecretVaultError(f"Secret 单向导入密文解密失败：{type(exc).__name__}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SecretVaultError("Secret 单向导入 payload 格式无效。")
    return payload


def secret_password_policy_error(password: str) -> str:
    password = password or ""
    missing: list[str] = []
    if len(password) < SECRET_VAULT_MIN_PASSWORD_CHARS:
        missing.append(f"至少 {SECRET_VAULT_MIN_PASSWORD_CHARS} 个字符")
    if not re.search(r"[A-Z]", password):
        missing.append("大写字母")
    if not re.search(r"[a-z]", password):
        missing.append("小写字母")
    if not re.search(r"\d", password):
        missing.append("数字")
    if not re.search(r"[^A-Za-z0-9]", password):
        missing.append("特殊字符")
    if missing:
        return "Secret 密码需要" + "、".join(missing) + "。"
    return ""


def secret_create_vault(paths: SecretVaultPaths, password: str) -> tuple[bool, Optional[bytes], str]:
    password_error = secret_password_policy_error(password)
    if password_error:
        return False, None, password_error
    if not secret_crypto_available():
        return False, None, f"Secret Vault 强加密不可用：{secret_crypto_status_text()}。请安装 PyNaCl 后再启用。"
    salt_size = int(getattr(nacl_pwhash.argon2id, "SALTBYTES", 16))
    salt = os.urandom(salt_size)
    try:
        key = secret_derive_key(password, salt)
        verifier = secret_encrypt_bytes(key, SECRET_VAULT_SENTINEL, b"secret-vault-verifier")
        import_key_record, _import_private_key = secret_build_import_key_record(key)
    except SecretVaultError as exc:
        return False, None, str(exc)
    meta = {
        "schema_version": "secretvault.v1",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "kdf": "argon2id-sensitive",
        "aead": "xchacha20poly1305-ietf",
        "salt": secret_b64(salt),
        "verifier_ciphertext": secret_b64(verifier),
        SECRET_IMPORT_DROPBOX_META_KEY: import_key_record,
        "network_policy": {
            "mode": "fail_closed",
            "chain_env": SECRET_NETWORK_CHAIN_ENV,
            "tor_socks_env": SECRET_TOR_SOCKS_ENV,
            "direct_fallback": False,
        },
    }
    write_secret_vault_meta(paths, meta)
    return True, key, "Secret Vault 已创建并解锁。"


def secret_unlock_vault(paths: SecretVaultPaths, password: str) -> tuple[bool, Optional[bytes], str]:
    meta = load_secret_vault_meta(paths)
    if not meta:
        return False, None, "Secret Vault 尚未初始化。"
    if not secret_crypto_available():
        return False, None, f"Secret Vault 强加密不可用：{secret_crypto_status_text()}。"
    try:
        salt = secret_unb64(str(meta.get("salt") or ""))
        verifier = secret_unb64(str(meta.get("verifier_ciphertext") or ""))
        key = secret_derive_key(password, salt)
        plain = secret_decrypt_bytes(key, verifier, b"secret-vault-verifier")
    except Exception as exc:
        return False, None, f"Secret Vault 解锁失败：{exc}"
    if plain != SECRET_VAULT_SENTINEL:
        return False, None, "Secret Vault 解锁失败：verifier 不匹配。"
    return True, key, "Secret Vault 已解锁。"


def secret_new_session_id() -> str:
    return f"secret_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1_000_000_000:09d}"


def secret_safe_session_id(session_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", session_id or "session").strip("-") or "session"


def secret_storage_path_for_session(paths: SecretVaultPaths, session_id: str, kind: str, name: str) -> str:
    session_id = secret_safe_session_id(session_id)
    safe_kind = re.sub(r"[^A-Za-z0-9_.-]+", "-", kind or "data").strip("-") or "data"
    safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "-", name or short_uid("secret")).strip("-") or short_uid("secret")
    return os.path.join(paths.sessions_dir, session_id, safe_kind, safe_name + ".secret")


def secret_virtual_ref(kind: str, name: str) -> str:
    safe_kind = re.sub(r"[^A-Za-z0-9_.-]+", "-", kind or "data").strip("-") or "data"
    safe_name = re.sub(r"[^A-Za-z0-9_.:-]+", "-", name or short_uid("secret")).strip("-") or short_uid("secret")
    return f"secret://subagents/{safe_kind}/{safe_name}"


def secret_session_id_from_path(paths: SecretVaultPaths, path: str) -> str:
    try:
        rel = os.path.relpath(normalized_path(path), paths.sessions_dir)
    except Exception:
        return ""
    parts = rel.split(os.sep)
    return parts[0] if len(parts) >= 3 else ""


def secret_write_json_for_session(
    paths: SecretVaultPaths,
    *,
    unlocked: bool,
    key: Optional[bytes],
    current_session_id: str,
    session_id: str,
    kind: str,
    name: str,
    payload: dict[str, Any],
) -> tuple[bool, str, str]:
    if not unlocked or not key:
        return False, "Secret Vault 已锁定，拒绝写入。", ""
    session_id = secret_safe_session_id(session_id or current_session_id)
    try:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        aad = f"secret-vault:{kind}:{session_id}".encode("utf-8", errors="ignore")
        sealed = secret_encrypt_bytes(key, raw, aad)
        path = secret_storage_path_for_session(paths, session_id, kind, name)
        write_bytes_atomic(path, sealed)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return True, path, ""
    except Exception as exc:
        warning = f"{type(exc).__name__}: {exc}"
        return False, f"Secret Vault 加密写入失败：{warning}", warning


def secret_read_json_from_path(
    paths: SecretVaultPaths,
    *,
    unlocked: bool,
    key: Optional[bytes],
    import_private_key: Optional[bytes],
    kind: str,
    path: str,
    session_id: str = "",
    current_session_id: str = "",
) -> tuple[bool, Optional[dict[str, Any]], str]:
    if not unlocked or not key:
        return False, None, "Secret Vault 已锁定，拒绝读取。"
    secret_session_id = session_id or secret_session_id_from_path(paths, path) or current_session_id
    sealed = b""
    try:
        with open(path, "rb") as fh:
            sealed = fh.read()
        aad = f"secret-vault:{kind}:{secret_session_id}".encode("utf-8", errors="ignore")
        raw = secret_decrypt_bytes(key, sealed, aad)
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        if kind == "imported-sessions":
            try:
                payload = secret_decrypt_sealed_import_envelope(import_private_key, sealed)
            except Exception as sealed_exc:
                return False, None, f"{type(exc).__name__}: {exc}; sealed-import: {sealed_exc}"
        else:
            return False, None, f"{type(exc).__name__}: {exc}"
    if not isinstance(payload, dict):
        return False, None, "Secret payload 格式无效。"
    return True, payload, path


def secret_append_transcript_turn(
    paths: SecretVaultPaths,
    *,
    unlocked: bool,
    key: Optional[bytes],
    current_session_id: str,
    user_text: str,
    assistant_text: str,
    source: str = "",
    session_id: str = "",
) -> tuple[bool, str, str]:
    target_session_id = secret_safe_session_id(session_id or current_session_id)
    payload = {
        "schema_version": "secret.transcript.turn.v1",
        "session_id": target_session_id,
        "timestamp": now_iso(),
        "source": source,
        "messages": [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": assistant_text},
        ],
    }
    return secret_write_json_for_session(
        paths,
        unlocked=unlocked,
        key=key,
        current_session_id=current_session_id,
        session_id=target_session_id,
        kind="transcript-turns",
        name=short_uid("turn"),
        payload=payload,
    )


def secret_message_record(message: Message) -> dict[str, Any]:
    return {
        "role": str(message.role or ""),
        "content": str(message.content or ""),
        "done": bool(message.done),
    }


def secret_message_from_record(record: Any) -> Optional[Message]:
    if not isinstance(record, dict):
        return None
    role = str(record.get("role") or "")
    if role not in {"system", "user", "assistant"}:
        return None
    return Message(role, str(record.get("content") or ""), bool(record.get("done", True)))


def secret_session_sidebar_key(session_id: str) -> str:
    session_id = secret_safe_session_id(session_id)
    return f"{SECRET_NATIVE_SESSION_PREFIX}{session_id}" if session_id else ""


def secret_session_id_from_sidebar_key(key: Any) -> str:
    text = str(key or "").strip()
    if text.startswith(SECRET_NATIVE_SESSION_PREFIX):
        return text[len(SECRET_NATIVE_SESSION_PREFIX):]
    return text


def secret_import_sidebar_key(entry: dict[str, Any]) -> str:
    basename = os.path.basename(str(entry.get("path") or ""))
    return f"{SECRET_IMPORT_SESSION_PREFIX}{basename}" if basename else ""


def secret_import_target_from_sidebar_key(key: Any) -> str:
    text = str(key or "").strip()
    if text.startswith(SECRET_IMPORT_SESSION_PREFIX):
        return text[len(SECRET_IMPORT_SESSION_PREFIX):]
    return text


def secret_session_title_for_messages(title: str, messages: list[Message]) -> str:
    title = compact_title(str(title or ""), 80)
    if title.startswith("Secret: "):
        title = compact_title(title.removeprefix("Secret: "), 80)
    if title and title not in {"main", "Secret Vault", "运行中会话", "空闲会话"}:
        return title
    return compact_title(suggested_session_title(messages) or title or "Secret 会话", 80)


def secret_messages_to_backend_history(messages: list[Message]) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for msg in messages:
        if msg.role == "system":
            continue
        if msg.role == "user":
            history.append({"role": "user", "content": [{"type": "text", "text": msg.content}]})
        elif msg.role == "assistant":
            history.append({"role": "assistant", "content": [{"type": "text", "text": msg.content}]})
    return history


def secret_session_state_payload(
    session_id: str,
    title: str,
    messages: list[Message],
    *,
    source: str = "",
    origin: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    payload = {
        "schema_version": "secret.session_state.v1",
        "session_id": secret_safe_session_id(session_id),
        "title": secret_session_title_for_messages(title, messages),
        "updated_at": now_iso(),
        "source": source,
        "messages": [secret_message_record(msg) for msg in messages],
    }
    if isinstance(origin, dict) and origin:
        payload["origin"] = dict(origin)
    return payload


def messages_from_secret_session_payload(payload: dict[str, Any]) -> list[Message]:
    raw_messages = payload.get("messages")
    records = raw_messages if isinstance(raw_messages, list) else []
    messages = [msg for msg in (secret_message_from_record(item) for item in records) if msg is not None]
    if messages:
        return messages
    return [Message("system", "Secret 会话为空。")]


def parse_secret_import_args(raw: str) -> tuple[str, str]:
    text = (raw or "").strip()
    disposition = "delete"
    target = "current"
    if not text:
        return disposition, target
    first, _, rest = text.partition(" ")
    parsed = SECRET_IMPORT_DISPOSITION_ALIASES.get(first.lower())
    if parsed:
        disposition = parsed
        target = rest.strip() or "current"
    else:
        target = text
    return disposition, target


def parse_secret_proxy_chain(raw: str) -> list[str]:
    text = (raw or "").strip()
    if not text:
        return []
    text = text.replace("->", ",").replace(";", ",")
    return [item.strip() for item in re.split(r"[,\s]+", text) if item.strip()]


def normalize_secret_proxy_endpoint(endpoint: str) -> str:
    value = (endpoint or "").strip()
    if value.lower() == "tor":
        return SECRET_DEFAULT_TOR_SOCKS
    if value and "://" not in value:
        value = f"socks5h://{value}"
    return value


def resolve_secret_imported_session_entry(
    entries: list[dict[str, Any]],
    target: str,
) -> tuple[Optional[dict[str, Any]], str]:
    candidates = [entry for entry in entries if not entry.get("error")]
    if not candidates:
        return None, "Secret Vault 里没有可打开的已导入会话。"
    raw = secret_import_target_from_sidebar_key(target)
    if not raw:
        return None, "Usage: /Secret open <编号|id|文件名>"
    match = re.fullmatch(r"[sS]?(\d+)", raw)
    if match:
        idx = int(match.group(1)) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx], ""
        return None, f"索引越界: 1-{len(candidates)}"
    normalized = re.sub(r"^(?:id:|#)", "", raw, flags=re.I)
    matches: list[dict[str, Any]] = []
    for entry in candidates:
        entry_path = str(entry.get("path") or "")
        basename = os.path.basename(entry_path)
        entry_candidates = {
            entry_path,
            normalized_path(entry_path),
            basename,
            basename.removesuffix(".secret"),
            str(entry.get("stable_id") or ""),
            str(entry.get("basename") or ""),
        }
        if raw in entry_candidates or normalized in entry_candidates:
            matches.append(entry)
    if len(matches) == 1:
        return matches[0], ""
    if len(matches) > 1:
        return None, f"匹配到多个 Secret 导入会话：{raw}"
    return None, "找不到 Secret 导入会话，请先 /Secret sessions 查看编号。"


def resolve_secret_native_session_entry(
    entries: list[dict[str, Any]],
    target: str,
) -> tuple[Optional[dict[str, Any]], str]:
    candidates = [entry for entry in entries if not entry.get("error")]
    if not candidates:
        return None, "Secret Vault 里没有可打开的加密会话。"
    raw = secret_session_id_from_sidebar_key(target)
    if not raw:
        return None, "Usage: /Secret open-session <编号|session_id>"
    match = re.fullmatch(r"[sS]?(\d+)", raw)
    if match:
        idx = int(match.group(1)) - 1
        if 0 <= idx < len(candidates):
            return candidates[idx], ""
        return None, f"索引越界: 1-{len(candidates)}"
    matches: list[dict[str, Any]] = []
    for entry in candidates:
        session_id = str(entry.get("session_id") or "")
        title = str(entry.get("title") or "")
        if raw in {session_id, title, secret_session_sidebar_key(session_id)}:
            matches.append(entry)
    if len(matches) == 1:
        return matches[0], ""
    if len(matches) > 1:
        return None, f"匹配到多个 Secret 会话：{raw}"
    return None, "找不到 Secret 会话。"


def secret_import_represented_by_native(import_entry: dict[str, Any], native_entries: list[dict[str, Any]]) -> bool:
    raw_import_path = str(import_entry.get("path") or "")
    import_path = normalized_path(raw_import_path) if raw_import_path else ""
    stable_id = str(import_entry.get("stable_id") or "")
    title = str(import_entry.get("title") or "")
    for native in native_entries:
        raw_native_import_path = str(native.get("origin_import_path") or "")
        native_import_path = normalized_path(raw_native_import_path) if raw_native_import_path else ""
        if import_path and native_import_path == import_path:
            return True
        if stable_id and str(native.get("origin_stable_id") or "") == stable_id:
            return True
        if title and str(native.get("title") or "") == title:
            return True
    return False


def secret_write_sealed_import(
    paths: SecretVaultPaths,
    public_key: bytes,
    public_key_id: str,
    session_id: str,
    name: str,
    payload: dict[str, Any],
) -> tuple[bool, str]:
    try:
        envelope = secret_sealed_import_envelope(public_key, public_key_id, payload)
        path = secret_storage_path_for_session(paths, session_id, "imported-sessions", name)
        write_bytes_atomic(path, envelope)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
        return True, path
    except Exception as exc:
        return False, f"Secret Vault 单向加密写入失败：{type(exc).__name__}: {exc}"


def secret_file_signature(paths: SecretVaultPaths, kind: str, name: str = "*.secret") -> tuple[tuple[str, float, int], ...]:
    pattern = os.path.join(paths.sessions_dir, "*", kind, name)
    signature: list[tuple[str, float, int]] = []
    for path in sorted(glob.glob(pattern)):
        try:
            stat = os.stat(path)
        except OSError:
            continue
        signature.append((normalized_path(path), float(stat.st_mtime), int(stat.st_size)))
    return tuple(signature)


def secret_import_file_signature(paths: SecretVaultPaths) -> tuple[tuple[str, float, int], ...]:
    return secret_file_signature(paths, "imported-sessions", "*.secret")


def secret_native_session_file_signature(paths: SecretVaultPaths) -> tuple[tuple[str, float, int], ...]:
    return secret_file_signature(paths, "session-state", "state.secret")


def secret_imported_session_entries(
    paths: SecretVaultPaths,
    *,
    unlocked: bool,
    key: Optional[bytes],
    import_private_key: Optional[bytes],
    compact_title: Callable[[str, int], str],
    include_payload: bool = True,
) -> list[dict[str, Any]]:
    if not unlocked or not key:
        return []
    pattern = os.path.join(paths.sessions_dir, "*", "imported-sessions", "*.secret")
    entries: list[dict[str, Any]] = []
    for path in sorted(glob.glob(pattern)):
        session_id = secret_session_id_from_path(paths, path)
        ok, payload, detail = secret_read_json_from_path(
            paths,
            unlocked=unlocked,
            key=key,
            import_private_key=import_private_key,
            kind="imported-sessions",
            path=path,
            session_id=session_id,
        )
        if not ok or not payload:
            entries.append({
                "path": path,
                "session_id": session_id,
                "error": detail,
                "imported_at": "",
                "title": os.path.basename(path),
                "stable_id": "",
            })
            continue
        source = payload.get("source") if isinstance(payload.get("source"), dict) else {}
        entry = {
            "path": path,
            "session_id": session_id,
            "imported_at": str(payload.get("imported_at") or ""),
            "title": compact_title(str(source.get("title") or source.get("basename") or os.path.basename(path)), 80),
            "stable_id": str(source.get("stable_id") or ""),
            "basename": str(source.get("basename") or ""),
            "size": int(source.get("size") or 0),
            "sha256": str(source.get("sha256") or ""),
        }
        if include_payload:
            entry["payload"] = payload
        entries.append(entry)
    entries.sort(key=lambda item: (str(item.get("imported_at") or ""), os.path.basename(str(item.get("path") or ""))), reverse=True)
    return entries


def secret_native_session_entries(
    paths: SecretVaultPaths,
    *,
    unlocked: bool,
    key: Optional[bytes],
    import_private_key: Optional[bytes],
    compact_title: Callable[[str, int], str],
    include_payload: bool = False,
) -> list[dict[str, Any]]:
    if not unlocked or not key:
        return []
    pattern = os.path.join(paths.sessions_dir, "*", "session-state", "state.secret")
    entries: list[dict[str, Any]] = []
    for path in sorted(glob.glob(pattern)):
        session_id = secret_session_id_from_path(paths, path)
        ok, payload, detail = secret_read_json_from_path(
            paths,
            unlocked=unlocked,
            key=key,
            import_private_key=import_private_key,
            kind="session-state",
            path=path,
            session_id=session_id,
        )
        if not ok or not payload:
            entries.append({
                "path": path,
                "session_id": session_id,
                "error": detail,
                "updated_at": "",
                "title": session_id or os.path.basename(path),
            })
            continue
        messages = payload.get("messages")
        message_count = len(messages) if isinstance(messages, list) else 0
        origin = payload.get("origin") if isinstance(payload.get("origin"), dict) else {}
        entry = {
            "path": path,
            "session_id": str(payload.get("session_id") or session_id),
            "updated_at": str(payload.get("updated_at") or ""),
            "title": compact_title(str(payload.get("title") or session_id or "Secret 会话"), 80),
            "message_count": message_count,
            "origin_kind": str(origin.get("kind") or ""),
            "origin_import_path": str(origin.get("import_path") or ""),
            "origin_stable_id": str(origin.get("stable_id") or ""),
        }
        if include_payload:
            entry["payload"] = payload
        entries.append(entry)
    entries.sort(key=lambda item: (str(item.get("updated_at") or ""), str(item.get("session_id") or "")), reverse=True)
    return entries
