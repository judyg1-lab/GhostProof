import os
import json

from src.crypto import (
    generate_key,
    encrypt_data
)

from src.integrity import (
    calculate_sha256
)

from src.erasure import (
    encode_shards
)

from src.secret_sharing import (
    split_secret
)


DATA_SHARDS = 8
TOTAL_SHARDS = 12

KEY_THRESHOLD = 3
TOTAL_KEY_SHARES = 5


def protect_incident_video(
    incident_path,
    event_dir
):
    """
    對已完成的 incident.mp4 執行 GhostProof 保護流程。

    incident.mp4
        ↓
    SHA-256
        ↓
    AES-256-GCM
        ↓
    8-of-12 Erasure Coding

    AES key
        ↓
    Shamir 3-of-5
    """

    print(
        "\n======================================"
    )

    print(
        "[PROTECT] 開始保護事件影片"
    )

    print(
        f"[PROTECT] Input: "
        f"{incident_path}"
    )


    # ========================================================
    # 1. 讀取 incident.mp4
    # ========================================================

    with open(
        incident_path,
        "rb"
    ) as f:

        video_bytes = f.read()


    print(
        f"[1/6] Incident video loaded "
        f"({len(video_bytes)} bytes)"
    )


    # ========================================================
    # 2. SHA-256
    # ========================================================

    original_hash = calculate_sha256(
        video_bytes
    )


    hash_path = os.path.join(
        event_dir,
        "evidence.sha256"
    )


    with open(
        hash_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            original_hash
        )


    print(
        f"[2/6] SHA-256: "
        f"{original_hash}"
    )


    # ========================================================
    # 3. 每個事件建立獨立 AES-256 key
    # ========================================================

    key = generate_key()


    nonce, encrypted_data = encrypt_data(
        video_bytes,
        key
    )


    encrypted_path = os.path.join(
        event_dir,
        "encrypted.bin"
    )

    nonce_path = os.path.join(
        event_dir,
        "nonce.bin"
    )


    with open(
        encrypted_path,
        "wb"
    ) as f:

        f.write(
            encrypted_data
        )


    with open(
        nonce_path,
        "wb"
    ) as f:

        f.write(
            nonce
        )


    print(
        "[3/6] AES-256-GCM 加密完成"
    )


    # ========================================================
    # 4. 8-of-12 Erasure Coding
    # ========================================================

    shards, encrypted_size = encode_shards(
        encrypted_data
    )


    shards_dir = os.path.join(
        event_dir,
        "shards"
    )


    os.makedirs(
        shards_dir,
        exist_ok=True
    )


    for i, shard in enumerate(
        shards
    ):

        shard_path = os.path.join(
            shards_dir,
            f"shard_{i}.bin"
        )


        with open(
            shard_path,
            "wb"
        ) as f:

            f.write(
                shard
            )


    print(
        f"[4/6] "
        f"{DATA_SHARDS}-of-{TOTAL_SHARDS} "
        f"Erasure Coding 完成"
    )


    # ========================================================
    # 5. Shamir Secret Sharing
    # ========================================================

    key_shares = split_secret(
        key,
        threshold=KEY_THRESHOLD,
        num_shares=TOTAL_KEY_SHARES
    )


    key_shares_dir = os.path.join(
        event_dir,
        "key_shares"
    )


    os.makedirs(
        key_shares_dir,
        exist_ok=True
    )


    for x, y in key_shares:

        share_path = os.path.join(
            key_shares_dir,
            f"share_{x}.json"
        )


        share_data = {
            "x": x,
            "y": str(y)
        }


        with open(
            share_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                share_data,
                f,
                indent=4
            )


    print(
        f"[5/6] AES key 已切割成 "
        f"{TOTAL_KEY_SHARES} 份，"
        f"任意 {KEY_THRESHOLD} 份可恢復"
    )


    # ========================================================
    # 6. Metadata
    # ========================================================

    metadata = {
        "evidence_type":
            "incident_video",

        "incident_filename":
            os.path.basename(
                incident_path
            ),

        "original_size":
            len(video_bytes),

        "encrypted_size":
            encrypted_size,

        "original_sha256":
            original_hash,

        "data_shards":
            DATA_SHARDS,

        "total_shards":
            TOTAL_SHARDS,

        "key_threshold":
            KEY_THRESHOLD,

        "total_key_shares":
            TOTAL_KEY_SHARES
    }


    metadata_path = os.path.join(
        event_dir,
        "metadata.json"
    )


    with open(
        metadata_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=4
        )


    print(
        "[6/6] Metadata 已建立"
    )


    print(
        "--------------------------------------"
    )

    print(
        "Incident size   :",
        len(video_bytes),
        "bytes"
    )

    print(
        "Encrypted size  :",
        len(encrypted_data),
        "bytes"
    )

    print(
        "Evidence shards :",
        len(shards)
    )

    print(
        "Key shares      :",
        len(key_shares)
    )

    print(
        "[PASS] Incident video protection completed"
    )

    print(
        "======================================\n"
    )