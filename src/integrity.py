import hashlib


def calculate_sha256(data: bytes) -> str:
    """
    計算資料的 SHA-256 雜湊值。

    Returns:
        64 字元十六進位 SHA-256 hash
    """
    return hashlib.sha256(data).hexdigest()


def verify_integrity(
    original_data: bytes,
    recovered_data: bytes
) -> bool:
    """
    比較兩份資料的 SHA-256 是否相同。
    """

    original_hash = calculate_sha256(original_data)
    recovered_hash = calculate_sha256(recovered_data)

    return original_hash == recovered_hash