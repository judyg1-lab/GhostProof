import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def generate_key() -> bytes:
    """
    產生 256-bit AES key。
    """
    return AESGCM.generate_key(bit_length=256)


def encrypt_data(data: bytes, key: bytes) -> tuple[bytes, bytes]:
    """
    使用 AES-256-GCM 加密資料。

    Returns:
        nonce: 12-byte 隨機 nonce
        encrypted_data: 加密後的資料
    """
    aesgcm = AESGCM(key)

    nonce = os.urandom(12)

    encrypted_data = aesgcm.encrypt(
        nonce,
        data,
        None
    )

    return nonce, encrypted_data


def decrypt_data(
    encrypted_data: bytes,
    key: bytes,
    nonce: bytes
) -> bytes:
    """
    使用 AES-256-GCM 解密資料。
    """
    aesgcm = AESGCM(key)

    decrypted_data = aesgcm.decrypt(
        nonce,
        encrypted_data,
        None
    )

    return decrypted_data