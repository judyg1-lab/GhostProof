# GhostProof

## 專案簡介
GhostProof 旨在解決監控影像易因人為破壞或單點設備故障而遺失的痛點。結合 Edge AI、盲儲存與門檻密碼學，確保影像證據能如同「幽靈」般即時噴射至去中心化網路，捍衛司法真相 [cite: 240]。

## 專案結構
- `/src`: 核心演算法驗證代碼
- `.gitignore`: 告訴 Git 哪些檔案「不需要」傳到 GitHub
- `README.md`: 專案導覽
- `main.py`:初步程式撰寫

## 打包與分發
- Python Package (Whl): 提供加密與碎片化核心模組 SDK。
- Docker Image: 封裝推論環境，解決邊緣端相依性版本衝突。

## 技術棧 (Tech Stack)
* **核心開發:** Python 3.9+
* **影像處理:** OpenCV
* **邊緣推論:** YOLOv8 + NVIDIA TensorRT (FP16 Quantization)
* **資料加密:** AES-256-GCM (Authenticated Encryption)
* **容錯編碼:** Reed-Solomon Erasure Coding
* **分佈式儲存:** IPFS (InterPlanetary File System)
* **金鑰管理:** Shamir's Secret Sharing (SSS)

## 開發環境配置
1. 虛擬環境配置:
    ```
    - python -m venv ghostproof_env
    - .\ghostproof_env\Scripts\activate
    ```
2. 相依套件安裝: <code>pip install opencv-python ultralytics cryptography reedsolo web3</code>


## 核心技術驗證
- 本專案已完成端到端 (End-to-End) 之技術可行性驗證：

    1. 硬體介接: 成功整合外部 USB Camera 進行即時視訊串流採集。
    2. 應急防護: 實作事件觸發機制，於偵測異常時 0.1s (希望)內完成影像鎖定與加密。
    3. 核心邏輯 (main.py):
    ```
    if cv2.waitKey(1) & 0xFF == ord('s'):
        _, buffer = cv2.imencode('.jpg', frame)
        encrypted_data = AESGCM(key).encrypt(os.urandom(12),buffer.tobytes(), None)
        print(f"[Success] Evidence Shard Generated: {len(encrypted_data)} bytes")
    elif cv2.waitKey(1) & 0xFF == ord('q'):
        break
    ```

## 開發規劃 (Roadmap)
#### 第一階段：概念驗證 (Current Stage)
- [x] 系統需求分析與技術選型
- [x] PoC 概念驗證環境架設
- [x] 基礎影像擷取、AES-256-GCM 加密與 Reed-Solomon 碎片化功能驗證
- [x] 介接實體 USB Camera 進行端到端串流測試

#### 第二階段：核心模組強化 (Short-term)
- [ ] AI 推論優化：串接 YOLOv8 並使用 NVIDIA TensorRT 進行 FP16 量化，提升邊緣端偵測速度。
- [ ] 動態碎片分發：實作將影像碎片異地儲存至複數 IPFS 節點之機制。
- [ ] 門檻密碼學實作：開發 Shamir's Secret Sharing (SSS) 金鑰分拆模組，確保調閱權限去中心化。

#### 第三階段：系統整合與商用化 (Long-term)
- [ ] 司法聯盟鏈介接：開發符合司法鑑定規範之電子證據雜湊值 (Hash) 上鏈機制。
[ ] 跨平台打包部署：建構 Docker 映像檔，支援樹莓派 (Raspberry Pi 5) 與 NVIDIA Jetson 快速部署。
- [ ] 多裝置聯合防護：實作多台 GhostProof 節點協作機制，達成監控區域無死角之噴射備份。


