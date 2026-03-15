import cv2
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

cap = cv2.VideoCapture(1)

print("GhostProof 即時監測系統啟動，按下 'q' 鍵退出，按下 's' 鍵模擬偵測到破壞並噴射證據")

key = AESGCM.generate_key(bit_length=256)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.putText(frame, "GhostProof Monitoring", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow('GhostProof Edge AI Node', frame)

    key_input = cv2.waitKey(1) & 0xFF

    if key_input == ord('s'):
        print("\n[! ALERT] AI 偵測到暴力事件！啟動瞬間取證")

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        encrypted_data = aesgcm.encrypt(nonce, frame_bytes, None)

        with open("evidence_shards.bin", "wb") as f:
            f.write(encrypted_data)

        print(f"[Success] 影像已完成盲儲存加密。加密長度: {len(encrypted_data)} bytes")

        os.startfile("evidence_shards.bin")

    elif key_input == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()