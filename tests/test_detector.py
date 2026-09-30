import cv2

from src.detector import PersonDetector
from datetime import datetime


CAMERA_INDEX = 0


detector = PersonDetector(
    confidence_threshold=0.7,
    cooldown_seconds=10
)


cap = cv2.VideoCapture(
    CAMERA_INDEX
)


if not cap.isOpened():

    print(
        "[ERROR] 無法開啟攝影機"
    )

    raise SystemExit(1)


print(
    "GhostProof Detector Test"
)

print(
    "person >= 0.7 時觸發"
)

print(
    "Trigger 後進入 10 秒 cooldown"
)

print(
    "按 q 離開"
)


while True:

    ret, frame = cap.read()

    if not ret:
        break


    (
        triggered,
        annotated_frame,
        confidence,
        cooldown_remaining
    ) = detector.detect(
        frame
    )


    if triggered:

        print(
            f"[TRIGGER] "
            f"{datetime.now().strftime('%H:%M:%S')} "
            f"person detected "
            f"confidence={confidence:.2f}"
        )


    if cooldown_remaining > 0:

        cv2.putText(
            annotated_frame,
            f"Cooldown: {cooldown_remaining:.1f}s",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )


    if triggered:

        cv2.putText(
            annotated_frame,
            "GHOSTPROOF TRIGGER",
            (10, 110),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )


    cv2.imshow(
        "GhostProof Detector",
        annotated_frame
    )


    key = (
        cv2.waitKey(1)
        & 0xFF
    )


    if key == ord("q"):
        break


cap.release()

cv2.destroyAllWindows()