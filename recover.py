import os
import sys
import json

from src.crypto import decrypt_data
from src.erasure import decode_shards
from src.integrity import calculate_sha256
from src.secret_sharing import recover_secret


EVENTS_DIR = "events"


def load_metadata(
    event_dir
):
    metadata_path = os.path.join(
        event_dir,
        "metadata.json"
    )

    if not os.path.exists(
        metadata_path
    ):
        raise FileNotFoundError(
            f"找不到 metadata.json："
            f"{metadata_path}"
        )

    with open(
        metadata_path,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(
            f
        )


def load_available_shards(
    event_dir,
    total_shards
):
    shards_dir = os.path.join(
        event_dir,
        "shards"
    )

    available_shards = []
    shard_indices = []

    for i in range(
        total_shards
    ):

        shard_path = os.path.join(
            shards_dir,
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

            shard_indices.append(
                i
            )

    return (
        available_shards,
        shard_indices
    )


def load_available_key_shares(
    event_dir,
    total_key_shares
):
    key_shares_dir = os.path.join(
        event_dir,
        "key_shares"
    )

    shares = []

    for i in range(
        1,
        total_key_shares + 1
    ):

        share_path = os.path.join(
            key_shares_dir,
            f"share_{i}.json"
        )

        if not os.path.exists(
            share_path
        ):
            continue

        with open(
            share_path,
            "r",
            encoding="utf-8"
        ) as f:

            share_data = json.load(
                f
            )

        shares.append(
            (
                int(
                    share_data[
                        "x"
                    ]
                ),
                int(
                    share_data[
                        "y"
                    ]
                )
            )
        )

    return shares


def recover_event(
    event_name
):

    print(
        "======================================"
    )

    print(
        "GhostProof Incident Video Recovery"
    )

    print(
        "======================================"
    )


    # ========================================================
    # Event directory
    # ========================================================

    event_dir = os.path.join(
        EVENTS_DIR,
        event_name
    )


    if not os.path.isdir(
        event_dir
    ):

        print(
            f"[ERROR] 找不到事件資料夾："
            f"{event_dir}"
        )

        return False


    print(
        f"Event : {event_name}"
    )


    # ========================================================
    # 1. Metadata
    # ========================================================

    try:

        metadata = load_metadata(
            event_dir
        )

    except Exception as e:

        print(
            f"[ERROR] 無法讀取 metadata："
            f"{e}"
        )

        return False


    encrypted_size = metadata[
        "encrypted_size"
    ]

    expected_hash = metadata[
        "original_sha256"
    ]

    data_shards = metadata[
        "data_shards"
    ]

    total_shards = metadata[
        "total_shards"
    ]

    key_threshold = metadata[
        "key_threshold"
    ]

    total_key_shares = metadata[
        "total_key_shares"
    ]


    print(
        f"Erasure Coding : "
        f"{data_shards}-of-{total_shards}"
    )

    print(
        f"Key Sharing    : "
        f"{key_threshold}-of-{total_key_shares}"
    )


    # ========================================================
    # 2. 找出現有 evidence shards
    # ========================================================

    (
        available_shards,
        shard_indices
    ) = load_available_shards(
        event_dir,
        total_shards
    )


    print(
        f"Available shard indices: "
        f"{shard_indices}"
    )

    print(
        f"Available shard count  : "
        f"{len(available_shards)}"
    )


    if len(
        available_shards
    ) < data_shards:

        print(
            f"[FAIL] Shards 不足，"
            f"至少需要 {data_shards} 個"
        )

        return False


    # ========================================================
    # 3. 還原 encrypted incident
    # ========================================================

    try:

        recovered_encrypted_data = (
            decode_shards(
                available_shards,
                shard_indices,
                encrypted_size
            )
        )

    except Exception as e:

        print(
            f"[ERROR] Erasure recovery 失敗："
            f"{e}"
        )

        return False


    print(
        "[PASS] Encrypted incident "
        "recovered from available shards"
    )


    # ========================================================
    # 4. 找出現有 key shares
    # ========================================================

    shares = load_available_key_shares(
        event_dir,
        total_key_shares
    )


    share_indices = [
        x
        for x, _ in shares
    ]


    print(
        f"Available key shares : "
        f"{share_indices}"
    )

    print(
        f"Key share count      : "
        f"{len(shares)}"
    )


    if len(
        shares
    ) < key_threshold:

        print(
            f"[FAIL] Key shares 不足，"
            f"至少需要 {key_threshold} 份"
        )

        return False


    # 只取 threshold 份即可
    selected_shares = shares[
        :key_threshold
    ]


    print(
        "Selected key shares  : "
        f"{[x for x, _ in selected_shares]}"
    )


    # ========================================================
    # 5. 重建 AES Key
    # ========================================================

    try:

        key = recover_secret(
            selected_shares,
            threshold=key_threshold,
            secret_length=32
        )

    except Exception as e:

        print(
            f"[ERROR] AES key recovery 失敗："
            f"{e}"
        )

        return False


    print(
        f"[PASS] AES key recovered from "
        f"{key_threshold}-of-{total_key_shares} "
        f"Shamir shares"
    )


    # ========================================================
    # 6. 讀取 nonce
    # ========================================================

    nonce_path = os.path.join(
        event_dir,
        "nonce.bin"
    )


    if not os.path.exists(
        nonce_path
    ):

        print(
            "[ERROR] 找不到 nonce.bin"
        )

        return False


    with open(
        nonce_path,
        "rb"
    ) as f:

        nonce = f.read()


    # ========================================================
    # 7. AES-GCM 解密
    # ========================================================

    try:

        recovered_video = decrypt_data(
            recovered_encrypted_data,
            key,
            nonce
        )

    except Exception as e:

        print(
            f"[ERROR] AES-256-GCM 解密失敗："
            f"{e}"
        )

        return False


    print(
        "[PASS] AES-256-GCM decryption successful"
    )


    # ========================================================
    # 8. SHA-256
    # ========================================================

    recovered_hash = calculate_sha256(
        recovered_video
    )


    print(
        f"Expected SHA-256 : "
        f"{expected_hash}"
    )

    print(
        f"Recovered SHA-256: "
        f"{recovered_hash}"
    )


    if recovered_hash != expected_hash:

        print(
            "[FAIL] Evidence integrity verification failed"
        )

        return False


    print(
        "[PASS] Evidence integrity verified"
    )


    # ========================================================
    # 9. 儲存 recovered incident
    # ========================================================

    recovered_path = os.path.join(
        event_dir,
        "recovered_incident.mp4"
    )


    with open(
        recovered_path,
        "wb"
    ) as f:

        f.write(
            recovered_video
        )


    print(
        f"[PASS] Recovered incident saved: "
        f"{recovered_path}"
    )


    print(
        "======================================"
    )

    print(
        "GhostProof recovery completed successfully"
    )

    print(
        "======================================"
    )


    return True


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    if len(
        sys.argv
    ) != 2:

        print(
            "Usage:"
        )

        print(
            "python recover.py "
            "event_YYYYMMDD_HHMMSS"
        )

        raise SystemExit(1)


    event_name = sys.argv[
        1
    ]


    success = recover_event(
        event_name
    )


    if not success:

        raise SystemExit(1)