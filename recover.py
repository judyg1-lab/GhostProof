import os
import sys
import json

from src.crypto import decrypt_data
from src.erasure import decode_shards
from src.integrity import calculate_sha256
from src.secret_sharing import recover_secret
from src.ipfs_storage import IPFSStorage
from src.key_share_storage import KeyShareStorage


EVENTS_DIR = "events"
KEY_NODES_DIR = "key_nodes"


# ============================================================
# Metadata
# ============================================================

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


# ============================================================
# Evidence Shards
# ============================================================

def load_available_shards(
    event_dir,
    metadata
):
    """
    優先讀取本機 shard。

    如果本機 shard 不存在，
    則根據 metadata.json 裡的 CID
    從 IPFS 下載。

    只要取得 data_shards 數量即可停止。
    """

    total_shards = metadata[
        "total_shards"
    ]

    data_shards = metadata[
        "data_shards"
    ]


    shards_dir = os.path.join(
        event_dir,
        "shards"
    )


    os.makedirs(
        shards_dir,
        exist_ok=True
    )


    available_shards = []
    shard_indices = []


    # --------------------------------------------------------
    # 建立 index → CID 對照表
    # --------------------------------------------------------

    ipfs_entries = {
        int(item["index"]):
            item["cid"]

        for item in metadata.get(
            "ipfs_shards",
            []
        )
    }


    ipfs = IPFSStorage()


    # --------------------------------------------------------
    # 尋找 shards
    # --------------------------------------------------------

    for i in range(
        total_shards
    ):

        shard_path = os.path.join(
            shards_dir,
            f"shard_{i}.bin"
        )


        # ====================================================
        # Case 1：本機 shard 存在
        # ====================================================

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


            print(
                f"[LOCAL] shard_{i}.bin"
            )


        # ====================================================
        # Case 2：本機沒有 → 從 IPFS 下載
        # ====================================================

        elif i in ipfs_entries:

            cid = ipfs_entries[
                i
            ]


            print(
                f"[IPFS] Recovering "
                f"shard_{i}.bin"
            )

            print(
                f"       CID: {cid}"
            )


            try:

                ipfs.get_file(
                    cid,
                    shard_path
                )


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


                print(
                    f"[PASS] shard_{i}.bin "
                    f"retrieved from IPFS"
                )


            except Exception as e:

                print(
                    f"[WARN] shard_{i}.bin "
                    f"IPFS retrieval failed: {e}"
                )


        # ====================================================
        # 已取得足夠數量就停止
        # ====================================================

        if len(
            available_shards
        ) >= data_shards:

            break


    return (
        available_shards,
        shard_indices
    )


# ============================================================
# Key Shares
# ============================================================

def load_distributed_key_shares(
    event_name,
    total_key_shares
):
    """
    從 key_nodes/
    掃描目前可取得的 Shamir shares。
    """

    key_storage = KeyShareStorage(
        base_dir=KEY_NODES_DIR,
        total_nodes=total_key_shares
    )


    shares = (
        key_storage.load_available_shares(
            event_name
        )
    )


    return shares


# ============================================================
# Recovery
# ============================================================

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


    # ========================================================
    # Metadata fields
    # ========================================================

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
    # 2. 取得 Evidence Shards
    # ========================================================

    (
        available_shards,
        shard_indices
    ) = load_available_shards(
        event_dir,
        metadata
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
    # 3. 重建 Encrypted Incident
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
    # 4. 從 Key Nodes 尋找 Shamir Shares
    # ========================================================

    shares = (
        load_distributed_key_shares(
            event_name,
            total_key_shares
        )
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


    # ========================================================
    # 只需要 threshold 份
    # ========================================================

    selected_shares = shares[
        :key_threshold
    ]


    selected_indices = [
        x
        for x, _ in selected_shares
    ]


    print(
        f"Selected key shares  : "
        f"{selected_indices}"
    )


    # ========================================================
    # 5. Shamir → AES Key
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
    # 6. Nonce
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
    # 7. AES-256-GCM Decryption
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
    # 8. SHA-256 Integrity Verification
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
            "[FAIL] Evidence integrity "
            "verification failed"
        )

        return False


    print(
        "[PASS] Evidence integrity verified"
    )


    # ========================================================
    # 9. 儲存 Recovered Incident
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


    # ========================================================
    # Summary
    # ========================================================

    print(
        "\n--------------------------------------"
    )

    print(
        "Recovery source"
    )

    print(
        f"Evidence shards : "
        f"{len(available_shards)}/"
        f"{total_shards}"
    )

    print(
        f"Key shares      : "
        f"{len(shares)}/"
        f"{total_key_shares}"
    )

    print(
        f"Selected shares : "
        f"{selected_indices}"
    )

    print(
        "--------------------------------------"
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