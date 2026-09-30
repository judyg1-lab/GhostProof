import os
import json

from src.crypto import decrypt_data
from src.erasure import (
    decode_shards,
    DATA_SHARDS
)
from src.integrity import calculate_sha256


EVIDENCE_DIR = "evidence"
SHARDS_DIR = "shards"


# =========================
# 1. 讀取 metadata
# =========================

metadata_path = os.path.join(
    EVIDENCE_DIR,
    "metadata.json"
)

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


print("====================================")
print("GhostProof Evidence Recovery")
print("====================================")


# =========================
# 2. 找出目前存在的 shards
# =========================

available_shards = []
available_indices = []


for i in range(12):

    shard_path = os.path.join(
        SHARDS_DIR,
        f"shard_{i}.bin"
    )

    if os.path.exists(shard_path):

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
# 3. 檢查是否至少有 8 個
# =========================

if len(available_shards) < DATA_SHARDS:

    print(
        f"[FAIL] 只有 {len(available_shards)} 個 shards，"
        f"至少需要 {DATA_SHARDS} 個"
    )

    raise SystemExit(1)


# =========================
# 4. Erasure Coding Recovery
# =========================

encrypted_data = decode_shards(
    available_shards,
    available_indices,
    encrypted_size
)

print(
    "[PASS] Encrypted evidence recovered "
    "from available shards"
)


# =========================
# 5. 讀取 key 與 nonce
# =========================

key_path = os.path.join(
    EVIDENCE_DIR,
    "key.bin"
)

nonce_path = os.path.join(
    EVIDENCE_DIR,
    "nonce.bin"
)


with open(key_path, "rb") as f:
    key = f.read()


with open(nonce_path, "rb") as f:
    nonce = f.read()


# =========================
# 6. AES 解密
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
# 7. SHA-256 驗證
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
# 8. 儲存 recovered image
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

print(
    "===================================="
)

print(
    "GhostProof recovery completed successfully"
)

print(
    "===================================="
)