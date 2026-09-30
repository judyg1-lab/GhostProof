import os
import json

from src.crypto import decrypt_data
from src.erasure import (
    decode_shards,
    DATA_SHARDS
)
from src.integrity import calculate_sha256
from src.secret_sharing import recover_secret


# =========================
# 基本設定
# =========================

EVIDENCE_DIR = "evidence"
SHARDS_DIR = "shards"
KEY_SHARES_DIR = "key_shares"

TOTAL_SHARDS = 12
KEY_THRESHOLD = 3


# =========================
# 1. 讀取 metadata
# =========================

metadata_path = os.path.join(
    EVIDENCE_DIR,
    "metadata.json"
)

if not os.path.exists(metadata_path):

    print(
        "[FAIL] 找不到 metadata.json"
    )

    raise SystemExit(1)


with open(
    metadata_path,
    "r",
    encoding="utf-8"
) as f:

    metadata = json.load(f)


encrypted_size = metadata[
    "encrypted_size"
]

expected_hash = metadata[
    "original_sha256"
]


print(
    "===================================="
)

print(
    "GhostProof Evidence Recovery"
)

print(
    "===================================="
)


# =========================
# 2. 找出目前存在的 evidence shards
# =========================

available_shards = []
available_indices = []


for i in range(TOTAL_SHARDS):

    shard_path = os.path.join(
        SHARDS_DIR,
        f"shard_{i}.bin"
    )

    if os.path.exists(
        shard_path
    ):

        with open(
            shard_path,
            "rb"
        ) as f:

            shard_data = f.read()

        available_shards.append(
            shard_data
        )

        available_indices.append(
            i
        )


print(
    "Available shard indices:",
    available_indices
)

print(
    "Available shard count  :",
    len(available_shards)
)


# =========================
# 3. 檢查 evidence shards 數量
# =========================

if len(available_shards) < DATA_SHARDS:

    print(
        f"[FAIL] 目前只有 "
        f"{len(available_shards)} 個 evidence shards，"
        f"至少需要 {DATA_SHARDS} 個"
    )

    raise SystemExit(1)


# =========================
# 4. Erasure Coding Recovery
# =========================

try:

    encrypted_data = decode_shards(
        available_shards,
        available_indices,
        encrypted_size
    )

except Exception as e:

    print(
        f"[FAIL] Evidence shard recovery failed: {e}"
    )

    raise SystemExit(1)


print(
    "[PASS] Encrypted evidence recovered "
    "from available shards"
)


# =========================
# 5. 讀取 nonce
# =========================

nonce_path = os.path.join(
    EVIDENCE_DIR,
    "nonce.bin"
)


if not os.path.exists(
    nonce_path
):

    print(
        "[FAIL] 找不到 nonce.bin"
    )

    raise SystemExit(1)


with open(
    nonce_path,
    "rb"
) as f:

    nonce = f.read()


# =========================
# 6. 讀取 Shamir Key Shares
# =========================

selected_share_files = [
    "share_1.json",
    "share_3.json",
    "share_5.json"
]

shares = []


for filename in selected_share_files:

    share_path = os.path.join(
        KEY_SHARES_DIR,
        filename
    )

    if not os.path.exists(
        share_path
    ):

        print(
            f"[FAIL] 找不到 key share："
            f"{share_path}"
        )

        raise SystemExit(1)


    with open(
        share_path,
        "r",
        encoding="utf-8"
    ) as f:

        share_data = json.load(f)


    shares.append(
        (
            int(
                share_data["x"]
            ),
            int(
                share_data["y"]
            )
        )
    )


print(
    "Selected key shares:",
    [
        x
        for x, _ in shares
    ]
)


# =========================
# 7. Shamir Secret Recovery
# =========================

try:

    key = recover_secret(
        shares,
        threshold=KEY_THRESHOLD,
        secret_length=32
    )

except Exception as e:

    print(
        f"[FAIL] AES key recovery failed: {e}"
    )

    raise SystemExit(1)


print(
    "[PASS] AES key recovered from "
    "3-of-5 Shamir shares"
)


# =========================
# 8. AES-256-GCM 解密
# =========================

try:

    recovered_bytes = decrypt_data(
        encrypted_data,
        key,
        nonce
    )

except Exception as e:

    print(
        f"[FAIL] AES decryption failed: {e}"
    )

    raise SystemExit(1)


print(
    "[PASS] AES-256-GCM decryption successful"
)


# =========================
# 9. SHA-256 完整性驗證
# =========================

recovered_hash = calculate_sha256(
    recovered_bytes
)


print(
    "Expected SHA-256 :",
    expected_hash
)

print(
    "Recovered SHA-256:",
    recovered_hash
)


if recovered_hash != expected_hash:

    print(
        "[FAIL] Evidence integrity verification failed"
    )

    raise SystemExit(1)


print(
    "[PASS] Evidence integrity verified"
)


# =========================
# 10. 儲存 recovered image
# =========================

recovered_path = os.path.join(
    EVIDENCE_DIR,
    "recovered_from_shards.jpg"
)


with open(
    recovered_path,
    "wb"
) as f:

    f.write(
        recovered_bytes
    )


print(
    f"[PASS] Recovered image saved: "
    f"{recovered_path}"
)


# =========================
# 完成
# =========================

print(
    "===================================="
)

print(
    "GhostProof recovery completed successfully"
)

print(
    "===================================="
)