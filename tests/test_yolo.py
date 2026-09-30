import cv2

from ultralytics import YOLO


CAMERA_INDEX = 0

model = YOLO("yolo26n.pt")

cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print("[ERROR] 無法開啟攝影機")
    raise SystemExit(1)


print(
    "YOLO Camera Test 啟動，按 q 離開"
)


while True:

    ret, frame = cap.read()

    if not ret:
        break

    results = model.predict(
        source=frame,
        conf=0.5,
        verbose=False
    )

    result = results[0]

    annotated_frame = result.plot()

    cv2.imshow(
        "GhostProof YOLO Test",
        annotated_frame
    )

    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()