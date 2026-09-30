import os

from src.ipfs_storage import (
    IPFSStorage
)

from src.integrity import (
    calculate_sha256
)


TEST_FILE = (
    "events/"
    "event_20260930_152658/"
    "shards/"
    "shard_0.bin"
)


OUTPUT_FILE = (
    "ipfs_test_recovered.bin"
)


ipfs = IPFSStorage()


print(
    "======================================"
)

print(
    "GhostProof IPFS Storage Test"
)

print(
    "======================================"
)


# ============================================================
# 1. 上傳
# ============================================================

cid = ipfs.add_file(
    TEST_FILE
)


print(
    "[PASS] File added to IPFS"
)

print(
    f"CID: {cid}"
)


# ============================================================
# 2. 下載
# ============================================================

if os.path.exists(
    OUTPUT_FILE
):
    os.remove(
        OUTPUT_FILE
    )


ipfs.get_file(
    cid,
    OUTPUT_FILE
)


print(
    "[PASS] File retrieved from IPFS"
)


# ============================================================
# 3. SHA-256 驗證
# ============================================================

with open(
    TEST_FILE,
    "rb"
) as f:

    original_data = f.read()


with open(
    OUTPUT_FILE,
    "rb"
) as f:

    recovered_data = f.read()


original_hash = calculate_sha256(
    original_data
)

recovered_hash = calculate_sha256(
    recovered_data
)


print(
    f"Original SHA-256 : "
    f"{original_hash}"
)

print(
    f"Recovered SHA-256: "
    f"{recovered_hash}"
)


if original_hash == recovered_hash:

    print(
        "[PASS] IPFS retrieved file integrity verified"
    )

else:

    print(
        "[FAIL] IPFS file integrity verification failed"
    )


print(
    "======================================"
)