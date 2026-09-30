import os
import json
import shutil

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

from src.ipfs_storage import (
    IPFSStorage
)

from src.key_share_storage import (
    KeyShareStorage
)


# ============================================================
# Erasure Coding
# ============================================================

DATA_SHARDS = 8
TOTAL_SHARDS = 12


# ============================================================
# Shamir Secret Sharing
# ============================================================

KEY_THRESHOLD = 3
TOTAL_KEY_SHARES = 5


# ============================================================
# Production Mode
# ============================================================

# False：
# IPFS 與 metadata 建立成功後，
# 不保留原始 incident.mp4
KEEP_PLAINTEXT = False


# False：
# IPFS 上傳成功後，
# 不保留完整 encrypted.bin
KEEP_ENCRYPTED_FILE = False


# False：
# IPFS 上傳成功後，
# 移除本機 shards/
KEEP_LOCAL_SHARDS = False


# ============================================================
# Incident Protection
# ============================================================

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
        ↓
    12 shards
        ↓
    IPFS
        ↓
    12 CIDs

    AES key
        ↓
    Shamir Secret Sharing
        ↓
    3-of-5

    Production Mode：
        IPFS 與 metadata 成功建立後，
        可刪除本機 plaintext、
        encrypted.bin 與 shards。
    """

    # ========================================================
    # IPFS
    # ========================================================

    ipfs = IPFSStorage()


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
    # 基本檢查
    # ========================================================

    if not os.path.exists(
        incident_path
    ):

        raise FileNotFoundError(
            f"找不到 incident video："
            f"{incident_path}"
        )


    os.makedirs(
        event_dir,
        exist_ok=True
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
        f"[1/7] Incident video loaded "
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
        f"[2/7] SHA-256: "
        f"{original_hash}"
    )


    # ========================================================
    # 3. 每個事件建立獨立 AES-256 Key
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
        "[3/7] AES-256-GCM 加密完成"
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


    # ========================================================
    # 5. Shards → IPFS
    # ========================================================

    ipfs_shards = []


    for i, shard in enumerate(
        shards
    ):

        shard_path = os.path.join(
            shards_dir,
            f"shard_{i}.bin"
        )


        # ----------------------------------------------------
        # 儲存本機 shard
        # ----------------------------------------------------

        with open(
            shard_path,
            "wb"
        ) as f:

            f.write(
                shard
            )


        # ----------------------------------------------------
        # 上傳 IPFS
        # ----------------------------------------------------

        try:

            cid = ipfs.add_file(
                shard_path
            )


            ipfs_shards.append(
                {
                    "index": i,
                    "cid": cid
                }
            )


            print(
                f"[IPFS] shard_{i}.bin "
                f"→ {cid}"
            )


        except Exception as e:

            print(
                f"[ERROR] shard_{i}.bin "
                f"上傳 IPFS 失敗：{e}"
            )

            print(
                "[SAFETY] "
                "保留本機 incident、encrypted file "
                "與 shards，不執行 cleanup"
            )

            raise


    print(
        f"[4/7] "
        f"{DATA_SHARDS}-of-{TOTAL_SHARDS} "
        f"Erasure Coding 完成"
    )


    print(
        f"[5/7] "
        f"{len(ipfs_shards)} 個 shards "
        f"已加入 IPFS"
    )


    # ========================================================
    # 6. Shamir Secret Sharing
    # ========================================================

    key_shares = split_secret(
        key,
        threshold=KEY_THRESHOLD,
        num_shares=TOTAL_KEY_SHARES
    )

    key_storage = KeyShareStorage(
        base_dir="key_nodes",
        total_nodes=TOTAL_KEY_SHARES
    )


    event_id = os.path.basename(
        os.path.normpath(
            event_dir
        )
    )


    key_share_locations = []


    for x, y in key_shares:

        share_path = (
            key_storage.save_share(
                event_id=event_id,
                share_index=x,
                share_value=y
            )
        )


        key_share_locations.append(
            {
                "share_index": x,
                "node": f"node_{x}"
            }
        )


        print(
            f"[KEY NODE] "
            f"share_{x} "
            f"→ node_{x}"
        )


    print(
        f"[6/7] AES key 已切割成 "
        f"{TOTAL_KEY_SHARES} 份，"
        f"任意 {KEY_THRESHOLD} 份可恢復"
    )


    # ========================================================
    # 7. Metadata
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
            TOTAL_KEY_SHARES,

        "key_share_storage":
            "distributed_nodes",

        "key_share_nodes":
            key_share_locations,

        "storage_mode":
            "ipfs",

        "keep_plaintext":
            KEEP_PLAINTEXT,

        "keep_encrypted_file":
            KEEP_ENCRYPTED_FILE,

        "keep_local_shards":
            KEEP_LOCAL_SHARDS,

        "ipfs_shards":
            ipfs_shards
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
        "[7/7] Metadata 已建立"
    )


    # ========================================================
    # Production Safety Check
    # ========================================================

    ipfs_complete = (
        len(ipfs_shards)
        == TOTAL_SHARDS
    )


    metadata_ready = os.path.exists(
        metadata_path
    )


    nonce_ready = os.path.exists(
        nonce_path
    )


    hash_ready = os.path.exists(
        hash_path
    )


    stored_key_shares = (
        key_storage.load_available_shares(
            event_id
        )
    )


    key_shares_complete = (
        len(stored_key_shares)
        == TOTAL_KEY_SHARES
    )


    cleanup_allowed = (
        ipfs_complete
        and metadata_ready
        and nonce_ready
        and hash_ready
        and key_shares_complete
    )


    # ========================================================
    # Production Cleanup
    # ========================================================

    print(
        "\n[CLEANUP] "
        "開始檢查本機證據清理條件"
    )


    if not cleanup_allowed:

        print(
            "[WARN] Production cleanup 條件不足"
        )


        if not ipfs_complete:

            print(
                f"[WARN] IPFS shards："
                f"{len(ipfs_shards)}/"
                f"{TOTAL_SHARDS}"
            )


        if not metadata_ready:

            print(
                "[WARN] metadata.json 不存在"
            )


        if not nonce_ready:

            print(
                "[WARN] nonce.bin 不存在"
            )


        if not hash_ready:

            print(
                "[WARN] evidence.sha256 不存在"
            )


        if not key_shares_complete:

            print(
                "[WARN] Key shares 不完整"
            )


        print(
            "[SAFETY] "
            "取消 cleanup，保留所有本機證據"
        )


    else:

        print(
            "[CLEANUP] "
            "IPFS、metadata、nonce、hash "
            "與 key shares 驗證完成"
        )


        # ----------------------------------------------------
        # 1. Plaintext incident.mp4
        # ----------------------------------------------------

        if not KEEP_PLAINTEXT:

            if os.path.exists(
                incident_path
            ):

                os.remove(
                    incident_path
                )


                print(
                    "[CLEANUP] "
                    "已刪除 plaintext incident.mp4"
                )


        else:

            print(
                "[CLEANUP] "
                "KEEP_PLAINTEXT=True，"
                "保留 incident.mp4"
            )


        # ----------------------------------------------------
        # 2. encrypted.bin
        # ----------------------------------------------------

        if not KEEP_ENCRYPTED_FILE:

            if os.path.exists(
                encrypted_path
            ):

                os.remove(
                    encrypted_path
                )


                print(
                    "[CLEANUP] "
                    "已刪除本機 encrypted.bin"
                )


        else:

            print(
                "[CLEANUP] "
                "KEEP_ENCRYPTED_FILE=True，"
                "保留 encrypted.bin"
            )


        # ----------------------------------------------------
        # 3. shards/
        # ----------------------------------------------------

        if not KEEP_LOCAL_SHARDS:

            if os.path.exists(
                shards_dir
            ):

                shutil.rmtree(
                    shards_dir
                )


                print(
                    "[CLEANUP] "
                    "已刪除本機 shards/"
                )


        else:

            print(
                "[CLEANUP] "
                "KEEP_LOCAL_SHARDS=True，"
                "保留 shards/"
            )


    # ========================================================
    # Summary
    # ========================================================

    print(
        "\n--------------------------------------"
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
        "IPFS shards     :",
        len(ipfs_shards)
    )


    print(
        "Key shares      :",
        len(key_shares)
    )


    print(
        "Storage mode    :",
        metadata[
            "storage_mode"
        ]
    )


    print(
        "Keep plaintext  :",
        KEEP_PLAINTEXT
    )


    print(
        "Keep encrypted  :",
        KEEP_ENCRYPTED_FILE
    )


    print(
        "Keep shards     :",
        KEEP_LOCAL_SHARDS
    )


    # ========================================================
    # 最終狀態
    # ========================================================

    if cleanup_allowed:

        print(
            "[PASS] Incident video "
            "protection completed"
        )

        print(
            "[PASS] Production cleanup "
            "completed"
        )

    else:

        print(
            "[PASS] Incident video "
            "protection completed"
        )

        print(
            "[WARN] Local evidence retained "
            "for safety"
        )


    print(
        "======================================\n"
    )


    # ========================================================
    # 回傳 Protection Result
    # ========================================================

    return {
        "event_dir":
            event_dir,

        "metadata_path":
            metadata_path,

        "original_sha256":
            original_hash,

        "ipfs_shards":
            ipfs_shards,

        "cleanup_completed":
            cleanup_allowed
    }