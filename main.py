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

        num_shards = 12
        shard_size = len(encrypted_data) // num_shards

        if not os.path.exists("shards"): os.makedirs("shards")

        for i in range(num_shards):
            start = i * shard_size

            end = (i + 1) * shard_size if i != num_shards - 1 else len(encrypted_data)
            with open(f"shards/shard_{i}.bin", "wb") as f:
                f.write(encrypted_data[start:end])

        print(f"[Success] 影像已完成加密並切割為 {num_shards} 個碎片。")

        os.startfile("evidence_shards.bin")
        os.startfile("shards")

    elif key_input == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()