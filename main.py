import cv2
import os

from src.detector import PersonDetector
from src.recorder import SegmentRecorder
from src.incident_recorder import IncidentRecorder
from src.evidence_protection import protect_incident_video


# ============================================================
# 基本設定
# ============================================================

CAMERA_INDEX = 0


# Continuous Recording
RECORDING_SEGMENT_MINUTES = 20
RECORDING_FPS = 20.0

RECORDINGS_DIR = "recordings"


# Incident Recording
PRE_EVENT_SECONDS = 10
POST_EVENT_SECONDS = 30

EVENTS_DIR = "events"


# YOLO
YOLO_CONFIDENCE = 0.7
TRIGGER_COOLDOWN = 10


# Erasure Coding
DATA_SHARDS = 8
TOTAL_SHARDS = 12


# Shamir Secret Sharing
KEY_THRESHOLD = 3
TOTAL_KEY_SHARES = 5


# Output directories
EVIDENCE_DIR = "evidence"
SHARDS_DIR = "shards"
KEY_SHARES_DIR = "key_shares"


# ============================================================
# 建立輸出資料夾
# ============================================================

os.makedirs(
    RECORDINGS_DIR,
    exist_ok=True
)

os.makedirs(
    EVENTS_DIR,
    exist_ok=True
)

os.makedirs(
    EVIDENCE_DIR,
    exist_ok=True
)

os.makedirs(
    SHARDS_DIR,
    exist_ok=True
)

os.makedirs(
    KEY_SHARES_DIR,
    exist_ok=True
)


# ============================================================
# GhostProof 取證函式
# ============================================================

def capture_evidence(
    frame,
    trigger_source,
    trigger_confidence=None
):

    print(
        "\n======================================"
    )


    if trigger_source == "AI":

        print(
            f"[AI TRIGGER] "
            f"YOLO 偵測到 person，"
            f"confidence={trigger_confidence:.2f}"
        )

    else:

        print(
            "[MANUAL TRIGGER] "
            "使用者手動啟動取證"
        )


    print(
        "[! ALERT] GhostProof 啟動瞬間取證"
    )


    # --------------------------------------------------------
    # 1. Frame → JPEG
    # --------------------------------------------------------

    success, buffer = cv2.imencode(
        ".jpg",
        frame
    )

    if not success:

        print(
            "[ERROR] JPEG 編碼失敗"
        )

        return


    frame_bytes = buffer.tobytes()


    # --------------------------------------------------------
    # 2. 儲存原始證據
    # --------------------------------------------------------

    original_path = os.path.join(
        EVIDENCE_DIR,
        "original.jpg"
    )


    with open(
        original_path,
        "wb"
    ) as f:

        f.write(
            frame_bytes
        )


    print(
        f"[1/6] 原始證據已儲存："
        f"{original_path}"
    )


    # --------------------------------------------------------
    # 3. AES-256-GCM
    # --------------------------------------------------------

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
        "[2/6] AES-256-GCM 加密完成"
    )


    # --------------------------------------------------------
    # 4. 8-of-12 Erasure Coding
    # --------------------------------------------------------

    shards, original_encrypted_size = (
        encode_shards(
            encrypted_data
        )
    )


    original_hash = calculate_sha256(
        frame_bytes
    )


    # --------------------------------------------------------
    # Metadata
    # --------------------------------------------------------

    metadata = {
        "trigger_source":
            trigger_source,

        "trigger_confidence":
            trigger_confidence,

        "encrypted_size":
            original_encrypted_size,

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


    # --------------------------------------------------------
    # 儲存 12 個 evidence shards
    # --------------------------------------------------------

    for i, shard in enumerate(
        shards
    ):

        shard_path = os.path.join(
            SHARDS_DIR,
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
        f"[3/6] 已完成 "
        f"{DATA_SHARDS}-of-{TOTAL_SHARDS} "
        f"Erasure Coding，"
        f"產生 {len(shards)} 個 shards"
    )


    # --------------------------------------------------------
    # 5. 本地 AES 解密測試
    # --------------------------------------------------------

    try:

        recovered_bytes = decrypt_data(
            encrypted_data,
            key,
            nonce
        )

    except Exception as e:

        print(
            f"[ERROR] AES 解密失敗：{e}"
        )

        return


    # --------------------------------------------------------
    # 6. 儲存本地還原影像
    # --------------------------------------------------------

    recovered_path = os.path.join(
        EVIDENCE_DIR,
        "recovered.jpg"
    )


    with open(
        recovered_path,
        "wb"
    ) as f:

        f.write(
            recovered_bytes
        )


    print(
        f"[4/6] 解密完成："
        f"{recovered_path}"
    )


    # --------------------------------------------------------
    # 7. SHA-256
    # --------------------------------------------------------

    recovered_hash = calculate_sha256(
        recovered_bytes
    )


    hash_path = os.path.join(
        EVIDENCE_DIR,
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
        f"[5/6] Original SHA-256 : "
        f"{original_hash}"
    )

    print(
        f"      Recovered SHA-256: "
        f"{recovered_hash}"
    )


    if verify_integrity(
        frame_bytes,
        recovered_bytes
    ):

        print(
            "[PASS] 證據完整性驗證成功，"
            "資料未遭竄改"
        )

    else:

        print(
            "[FAIL] 證據完整性驗證失敗"
        )


    print(
        "[6/6] GhostProof 完整取證流程完成"
    )


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print(
        "\n------------- Summary --------------"
    )

    print(
        "Trigger source   :",
        trigger_source
    )


    if trigger_confidence is not None:

        print(
            "AI confidence   :",
            f"{trigger_confidence:.2f}"
        )


    print(
        "Original size    :",
        len(frame_bytes),
        "bytes"
    )

    print(
        "Encrypted size   :",
        len(encrypted_data),
        "bytes"
    )

    print(
        "Nonce size       :",
        len(nonce),
        "bytes"
    )

    print(
        "AES key size     :",
        len(key),
        "bytes"
    )

    print(
        "Evidence shards  :",
        len(shards)
    )

    print(
        "Key shares       :",
        len(key_shares)
    )

    print(
        "------------------------------------"
    )

    print(
        "======================================\n"
    )


# ============================================================
# 初始化 YOLO
# ============================================================

print(
    "[AI] 正在初始化 YOLO 模型..."
)


detector = PersonDetector(
    confidence_threshold=YOLO_CONFIDENCE,
    cooldown_seconds=TRIGGER_COOLDOWN
)


print(
    f"[AI] YOLO 初始化完成，"
    f"person confidence threshold="
    f"{YOLO_CONFIDENCE}"
)


# ============================================================
# 初始化 Camera
# ============================================================

cap = cv2.VideoCapture(
    CAMERA_INDEX
)


if not cap.isOpened():

    print(
        "[ERROR] 無法開啟攝影機"
    )

    raise SystemExit(1)


# ============================================================
# 初始化 Continuous Recorder
# ============================================================

recorder = SegmentRecorder(
    output_dir=RECORDINGS_DIR,
    segment_minutes=RECORDING_SEGMENT_MINUTES,
    fps=RECORDING_FPS
)

incident_recorder = IncidentRecorder(
    output_dir=EVENTS_DIR,
    fps=RECORDING_FPS,
    pre_event_seconds=PRE_EVENT_SECONDS,
    post_event_seconds=POST_EVENT_SECONDS
)


print(
    "\nGhostProof Edge AI 監測系統啟動"
)

print(
    f"Continuous Recording : "
    f"每 {RECORDING_SEGMENT_MINUTES} 分鐘自動分段"
)

print(
    f"AI Trigger           : "
    f"person >= {YOLO_CONFIDENCE}"
)

print(
    f"Incident Recording   : "
    f"前 {PRE_EVENT_SECONDS}s + "
    f"後 {POST_EVENT_SECONDS}s"
)

print(
    f"Cooldown             : "
    f"{TRIGGER_COOLDOWN} seconds"
)

print(
    "Manual               : "
    "按 's' 手動取證"
)

print(
    "Exit                 : "
    "按 'q' 離開"
)


# ============================================================
# 主監控迴圈
# ============================================================

while True:

    # --------------------------------------------------------
    # Camera Frame
    # --------------------------------------------------------

    ret, frame = cap.read()


    if not ret:

        print(
            "[ERROR] 無法讀取攝影機畫面"
        )

        break


    # ========================================================
    # Continuous Recording
    # ========================================================

    recorder.write(
        frame
    )


    # ========================================================
    # Incident Pre-event Buffer / Event Recording
    # ========================================================

    completed_event = (
        incident_recorder.add_frame(
            frame
        )
    )

    if completed_event is not None:

        protect_incident_video(
            incident_path=completed_event[
                "incident_path"
            ],
            event_dir=completed_event[
                "event_dir"
            ]
        )


    # ========================================================
    # YOLO 推論
    # ========================================================

    (
        ai_triggered,
        annotated_frame,
        confidence,
        cooldown_remaining
    ) = detector.detect(
        frame
    )


    # ========================================================
    # 顯示畫面
    # ========================================================

    display_frame = annotated_frame


    cv2.putText(
        display_frame,
        "GhostProof Monitoring",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2
    )


    # --------------------------------------------------------
    # Continuous Recording 狀態
    # --------------------------------------------------------

    cv2.putText(
        display_frame,
        "REC",
        (10, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 0, 255),
        2
    )


    # --------------------------------------------------------
    # Person Confidence
    # --------------------------------------------------------

    if confidence > 0:

        cv2.putText(
            display_frame,
            f"Person confidence: {confidence:.2f}",
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )


    # --------------------------------------------------------
    # Cooldown
    # --------------------------------------------------------

    if cooldown_remaining > 0:

        cv2.putText(
            display_frame,
            f"Cooldown: {cooldown_remaining:.1f}s",
            (10, 135),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )


    # --------------------------------------------------------
    # AI Trigger
    # --------------------------------------------------------

    if ai_triggered:

        cv2.putText(
            display_frame,
            "GHOSTPROOF TRIGGER",
            (10, 175),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )


    cv2.imshow(
        "GhostProof Edge AI Node",
        display_frame
    )


    # ========================================================
    # Keyboard Input
    # ========================================================

    key_input = (
        cv2.waitKey(1)
        & 0xFF
    )


    manual_triggered = (
        key_input == ord("s")
    )


    # ========================================================
    # GhostProof Trigger
    # ========================================================

    if ai_triggered:

        incident_recorder.trigger(
            frame=frame,
            trigger_source="AI",
            trigger_confidence=confidence
        )


    elif manual_triggered:

        incident_recorder.trigger(
            frame=frame,
            trigger_source="MANUAL"
        )


    # ========================================================
    # Exit
    # ========================================================

    if key_input == ord("q"):

        break


# ============================================================
# 清理
# ============================================================

completed_event = (
    incident_recorder.close()
)


# 如果關閉程式時，
# 剛好還有 Incident 正在錄製，
# 仍然要完成保護流程
if completed_event is not None:

    print(
        "\n[SHUTDOWN] "
        "偵測到尚未完成保護的事件"
    )

    protect_incident_video(
        incident_path=completed_event[
            "incident_path"
        ],
        event_dir=completed_event[
            "event_dir"
        ]
    )


recorder.close()

cap.release()

cv2.destroyAllWindows()


print(
    "\nGhostProof 已安全關閉"
)