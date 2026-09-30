import cv2
import os
import json

from src.crypto import generate_key, encrypt_data, decrypt_data
from src.integrity import calculate_sha256, verify_integrity
from src.erasure import encode_shards


# =========================
# 基本設定
# =========================

CAMERA_INDEX = 0
NUM_SHARDS = 12

EVIDENCE_DIR = "evidence"
SHARDS_DIR = "shards"

os.makedirs(EVIDENCE_DIR, exist_ok=True)
os.makedirs(SHARDS_DIR, exist_ok=True)


# =========================
# 初始化 Camera
# =========================

cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print("[ERROR] 無法開啟攝影機")
    exit()

print(
    "GhostProof 即時監測系統啟動，"
    "按下 'q' 鍵退出，"
    "按下 's' 鍵模擬偵測到事件並啟動取證"
)


# =========================
# 產生 AES-256 Key
# =========================

key = generate_key()


# =========================
# 主監控迴圈
# =========================

while True:

    ret, frame = cap.read()

    if not ret:
        print("[ERROR] 無法讀取攝影機畫面")
        break

    cv2.putText(
        frame,
        "GhostProof Monitoring",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )

    cv2.imshow("GhostProof Edge AI Node", frame)

    key_input = cv2.waitKey(1) & 0xFF


    # =========================
    # 模擬異常事件
    # =========================

    if key_input == ord("s"):

        print("\n[! ALERT] 偵測到異常事件，啟動瞬間取證")


        # -------------------------
        # 1. 將目前 frame 編碼成 JPEG
        # -------------------------

        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            print("[ERROR] JPEG 編碼失敗")
            continue

        frame_bytes = buffer.tobytes()


        # -------------------------
        # 2. 儲存原始證據圖片
        # -------------------------

        original_path = os.path.join(
            EVIDENCE_DIR,
            "original.jpg"
        )

        with open(original_path, "wb") as f:
            f.write(frame_bytes)

        print(
            f"[1/6] 原始證據已儲存：{original_path}"
        )


        # -------------------------
        # 3. AES-256-GCM 加密
        # -------------------------

        nonce, encrypted_data = encrypt_data(
            frame_bytes,
            key
        )

        encrypted_path = os.path.join(
            EVIDENCE_DIR,
            "encrypted.bin"
        )

        nonce_path = os.path.join(
            EVIDENCE_DIR,
            "nonce.bin"
        )

        key_path = os.path.join(
            EVIDENCE_DIR,
            "key.bin"
        )


        with open(encrypted_path, "wb") as f:
            f.write(encrypted_data)

        with open(nonce_path, "wb") as f:
            f.write(nonce)

        with open(key_path, "wb") as f:
            f.write(key)

        print(
            "[2/6] AES-256-GCM 加密完成"
        )


        # -------------------------
        # 4. 8-of-12 Erasure Coding
        # -------------------------

        shards, original_encrypted_size = encode_shards(
            encrypted_data
        )

        metadata = {
            "encrypted_size": original_encrypted_size,
            "original_sha256": calculate_sha256(frame_bytes),
            "data_shards": 8,
            "total_shards": 12
        }

        metadata_path = os.path.join(
            EVIDENCE_DIR,
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

        for i, shard in enumerate(shards):

            shard_path = os.path.join(
                SHARDS_DIR,
                f"shard_{i}.bin"
            )

            with open(shard_path, "wb") as f:
                f.write(shard)

        print(
            f"[3/6] 已完成 8-of-12 Erasure Coding，"
            f"產生 {len(shards)} 個 shards"
        )


        # -------------------------
        # 5. AES 解密
        # -------------------------

        try:

            recovered_bytes = decrypt_data(
                encrypted_data,
                key,
                nonce
            )

        except Exception as e:

            print(
                f"[ERROR] 解密失敗：{e}"
            )

            continue


        # -------------------------
        # 6. 儲存還原影像
        # -------------------------

        recovered_path = os.path.join(
            EVIDENCE_DIR,
            "recovered.jpg"
        )

        with open(recovered_path, "wb") as f:
            f.write(recovered_bytes)

        print(
            f"[4/6] 解密完成：{recovered_path}"
        )


        # -------------------------
        # 7. SHA-256 完整性驗證
        # -------------------------

        original_hash = calculate_sha256(
            frame_bytes
        )

        recovered_hash = calculate_sha256(
            recovered_bytes
        )

        hash_path = os.path.join(
            EVIDENCE_DIR,
            "evidence.sha256"
        )

        with open(hash_path, "w") as f:
            f.write(original_hash)


        print(
            f"[5/6] Original SHA-256 : {original_hash}"
        )

        print(
            f"      Recovered SHA-256: {recovered_hash}"
        )


        if verify_integrity(
            frame_bytes,
            recovered_bytes
        ):

            print(
                "[PASS] 證據完整性驗證成功，資料未遭竄改"
            )

        else:

            print(
                "[FAIL] 證據完整性驗證失敗"
            )


        # -------------------------
        # 完成
        # -------------------------

        print(
            "[6/6] GhostProof 基礎取證流程完成"
        )

        print(
            "\n======================================"
        )

        print(
            "Original size :",
            len(frame_bytes),
            "bytes"
        )

        print(
            "Encrypted size:",
            len(encrypted_data),
            "bytes"
        )

        print(
            "Nonce size    :",
            len(nonce),
            "bytes"
        )

        print(
            "Key size      :",
            len(key),
            "bytes"
        )

        print(
            "======================================\n"
        )


    elif key_input == ord("q"):

        break


# =========================
# 結束程式
# =========================

cap.release()

cv2.destroyAllWindows()