import cv2

from src.recorder import SegmentRecorder


CAMERA_INDEX = 0


cap = cv2.VideoCapture(
    CAMERA_INDEX
)


if not cap.isOpened():

    print(
        "[ERROR] 無法開啟攝影機"
    )

    raise SystemExit(1)


# 測試時：
# 10 秒 = 10 / 60 分鐘
recorder = SegmentRecorder(
    output_dir="recordings_test",
    segment_minutes=10 / 60,
    fps=20.0
)


print(
    "Recorder Test 啟動"
)

print(
    "每 10 秒自動切一支影片"
)

print(
    "按 q 離開"
)


while True:

    ret, frame = cap.read()

    if not ret:
        break


    recorder.write(
        frame
    )


    cv2.putText(
        frame,
        "Recording Test",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2
    )


    cv2.imshow(
        "Recorder Test",
        frame
    )


    key = (
        cv2.waitKey(1)
        & 0xFF
    )


    if key == ord("q"):
        break


recorder.close()

cap.release()

cv2.destroyAllWindows()