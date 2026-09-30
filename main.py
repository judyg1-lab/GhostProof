import cv2
import os
import time

from src.detector import PersonDetector
from src.recorder import SegmentRecorder
from src.incident_recorder import IncidentRecorder
from src.evidence_protection import protect_incident_video


# ============================================================
# 基本設定
# ============================================================

CAMERA_INDEX = 0


# ============================================================
# Continuous Recording
# ============================================================

# 正式環境：
# 每 20 分鐘自動切一支監控影片
RECORDING_SEGMENT_MINUTES = 20

# 目前錄影模組使用的 FPS
RECORDING_FPS = 20.0

RECORDINGS_DIR = "recordings"


# ============================================================
# Incident Recording
# ============================================================

# 異常事件前保留 10 秒
PRE_EVENT_SECONDS = 10

# 異常事件發生後繼續錄 30 秒
POST_EVENT_SECONDS = 30

EVENTS_DIR = "events"


# ============================================================
# YOLO
# ============================================================

YOLO_CONFIDENCE = 0.7

# AI trigger 後多久才能再次觸發
TRIGGER_COOLDOWN = 10

# 不需要每一幀都跑 YOLO
# 每 5 個 Camera frames 做一次推論
YOLO_INFERENCE_INTERVAL = 5


# ============================================================
# AI 啟用延遲
# ============================================================

# 系統剛啟動時先讓 pre-event buffer 累積。
#
# 如果一開 Camera 就立刻偵測到 person，
# pre-buffer 根本還沒有 10 秒資料。
#
# 因此先錄滿 PRE_EVENT_SECONDS，
# 再允許 AI 自動觸發。
AI_WARMUP_SECONDS = PRE_EVENT_SECONDS


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


# ============================================================
# 初始化 YOLO Detector
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


# ============================================================
# 初始化 Incident Recorder
# ============================================================

incident_recorder = IncidentRecorder(
    output_dir=EVENTS_DIR,
    fps=RECORDING_FPS,
    pre_event_seconds=PRE_EVENT_SECONDS,
    post_event_seconds=POST_EVENT_SECONDS
)


# ============================================================
# 執行狀態
# ============================================================

frame_counter = 0

system_start_time = time.time()

# 上一次 YOLO 推論結果
confidence = 0.0
cooldown_remaining = 0.0

# 顯示用
last_annotated_frame = None


# ============================================================
# 系統資訊
# ============================================================

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
    f"YOLO Interval        : "
    f"每 {YOLO_INFERENCE_INTERVAL} frames 推論一次"
)

print(
    f"Incident Recording   : "
    f"前 {PRE_EVENT_SECONDS}s + "
    f"後 {POST_EVENT_SECONDS}s"
)

print(
    f"AI Warmup            : "
    f"{AI_WARMUP_SECONDS} seconds"
)

print(
    f"Cooldown             : "
    f"{TRIGGER_COOLDOWN} seconds"
)

print(
    "Manual               : "
    "按 's' 手動觸發事件"
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
    # 1. Camera Frame
    # --------------------------------------------------------

    ret, frame = cap.read()


    if not ret:

        print(
            "[ERROR] 無法讀取攝影機畫面"
        )

        break


    frame_counter += 1


    # ========================================================
    # 2. 一般監控持續錄影
    # ========================================================

    recorder.write(
        frame
    )


    # ========================================================
    # 3. Incident Recorder
    #
    # 平常：
    #   將 frame 放進 pre-event buffer
    #
    # Incident recording：
    #   持續寫入事件影片
    #
    # 事件完成：
    #   回傳 completed_event
    # ========================================================

    completed_event = (
        incident_recorder.add_frame(
            frame
        )
    )


    # ========================================================
    # 4. 如果 Incident 剛錄製完成
    #    執行 GhostProof Protection
    # ========================================================

    if completed_event is not None:

        print(
            "\n[EVENT] Incident recording completed"
        )

        try:

            protect_incident_video(
                incident_path=completed_event[
                    "incident_path"
                ],
                event_dir=completed_event[
                    "event_dir"
                ]
            )

        except Exception as e:

            print(
                "[ERROR] Incident protection failed:"
            )

            print(
                e
            )


    # ========================================================
    # 5. 判斷 AI 是否已完成 Warmup
    # ========================================================

    elapsed_since_start = (
        time.time()
        - system_start_time
    )


    ai_ready = (
        elapsed_since_start
        >= AI_WARMUP_SECONDS
    )


    # ========================================================
    # 6. YOLO 推論
    # ========================================================

    ai_triggered = False


    # 不需要每一幀都做 YOLO
    if (
        frame_counter
        % YOLO_INFERENCE_INTERVAL
        == 0
    ):

        (
            detected_trigger,
            annotated_frame,
            confidence,
            cooldown_remaining
        ) = detector.detect(
            frame
        )


        # 只有 Warmup 完成後
        # 才允許 AI trigger
        if ai_ready:

            ai_triggered = (
                detected_trigger
            )


        last_annotated_frame = (
            annotated_frame
        )


    # ========================================================
    # 7. 顯示畫面
    # ========================================================

    # 有 YOLO 畫框時用 YOLO frame，
    # 沒跑 YOLO 的 frame 就顯示原始影像。
    #
    # 不直接重複 last annotated frame，
    # 避免畫面看起來卡住。
    display_frame = frame.copy()


    # --------------------------------------------------------
    # 系統名稱
    # --------------------------------------------------------

    cv2.putText(
        display_frame,
        "GhostProof Monitoring",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )


    # --------------------------------------------------------
    # REC
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
    # AI Warmup
    # --------------------------------------------------------

    if not ai_ready:

        warmup_remaining = max(
            0.0,
            (
                AI_WARMUP_SECONDS
                - elapsed_since_start
            )
        )


        cv2.putText(
            display_frame,
            (
                f"AI Warmup: "
                f"{warmup_remaining:.1f}s"
            ),
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

    else:

        cv2.putText(
            display_frame,
            "AI READY",
            (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


    # --------------------------------------------------------
    # Person Confidence
    # --------------------------------------------------------

    if confidence > 0:

        cv2.putText(
            display_frame,
            (
                f"Person confidence: "
                f"{confidence:.2f}"
            ),
            (10, 135),
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
            (
                f"Cooldown: "
                f"{cooldown_remaining:.1f}s"
            ),
            (10, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )


    # --------------------------------------------------------
    # Incident Recording
    # --------------------------------------------------------

    if incident_recorder.recording:

        cv2.putText(
            display_frame,
            "INCIDENT RECORDING",
            (10, 210),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )


    # --------------------------------------------------------
    # AI Trigger
    # --------------------------------------------------------

    if ai_triggered:

        cv2.putText(
            display_frame,
            "GHOSTPROOF TRIGGER",
            (10, 250),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            2
        )


    # ========================================================
    # 8. 顯示 Camera
    # ========================================================

    cv2.imshow(
        "GhostProof Edge AI Node",
        display_frame
    )


    # ========================================================
    # 9. Keyboard Input
    # ========================================================

    key_input = (
        cv2.waitKey(1)
        & 0xFF
    )


    manual_triggered = (
        key_input
        == ord("s")
    )


    # ========================================================
    # 10. Incident Trigger
    # ========================================================

    # --------------------------------------------------------
    # AI Trigger
    # --------------------------------------------------------

    if ai_triggered:

        print(
            "\n[AI TRIGGER] "
            f"person detected "
            f"confidence={confidence:.2f}"
        )


        incident_recorder.trigger(
            frame=frame,
            trigger_source="AI",
            trigger_confidence=confidence
        )


    # --------------------------------------------------------
    # Manual Trigger
    #
    # Manual 不受 warmup 限制，
    # 方便測試。
    # --------------------------------------------------------

    elif manual_triggered:

        print(
            "\n[MANUAL TRIGGER] "
            "使用者手動啟動 Incident"
        )


        incident_recorder.trigger(
            frame=frame,
            trigger_source="MANUAL"
        )


    # ========================================================
    # 11. Exit
    # ========================================================

    if key_input == ord("q"):

        break


# ============================================================
# 程式關閉
# ============================================================

print(
    "\n[SHUTDOWN] GhostProof 正在關閉..."
)


# ============================================================
# 如果 Incident 還沒錄完
# 先安全完成它
# ============================================================

completed_event = (
    incident_recorder.close()
)


if completed_event is not None:

    print(
        "[SHUTDOWN] "
        "偵測到尚未完成保護的事件"
    )


    try:

        protect_incident_video(
            incident_path=completed_event[
                "incident_path"
            ],
            event_dir=completed_event[
                "event_dir"
            ]
        )

    except Exception as e:

        print(
            "[ERROR] Shutdown incident "
            "protection failed:"
        )

        print(
            e
        )


# ============================================================
# 關閉 Continuous Recorder
# ============================================================

recorder.close()


# ============================================================
# Camera Cleanup
# ============================================================

cap.release()

cv2.destroyAllWindows()


print(
    "\nGhostProof 已安全關閉"
)