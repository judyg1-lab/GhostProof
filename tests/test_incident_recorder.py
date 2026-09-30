import cv2

from src.incident_recorder import (
    IncidentRecorder
)


CAMERA_INDEX = 0
FPS = 20.0


cap = cv2.VideoCapture(
    CAMERA_INDEX
)


if not cap.isOpened():

    print(
        "[ERROR] 無法開啟攝影機"
    )

    raise SystemExit(1)


incident_recorder = IncidentRecorder(
    output_dir="events_test",
    fps=FPS,
    pre_event_seconds=3,
    post_event_seconds=5
)


print(
    "Incident Recorder Test"
)

print(
    "按 s 模擬事件"
)

print(
    "會保存事件前約 3 秒 + 後 5 秒"
)

print(
    "按 q 離開"
)


while True:

    ret, frame = cap.read()

    if not ret:
        break


    # 每一幀都給 incident recorder
    incident_recorder.add_frame(
        frame
    )


    cv2.putText(
        frame,
        "Press S to Trigger Incident",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )


    if incident_recorder.recording:

        cv2.putText(
            frame,
            "INCIDENT RECORDING",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )


    cv2.imshow(
        "Incident Recorder Test",
        frame
    )


    key = (
        cv2.waitKey(1)
        & 0xFF
    )


    if key == ord("s"):

        incident_recorder.trigger(
            frame,
            trigger_source="MANUAL"
        )


    if key == ord("q"):

        break


incident_recorder.close()

cap.release()

cv2.destroyAllWindows()