# GhostProof

## 專案簡介

GhostProof 是一套以「**監控證據不應因單一設備遭破壞而消失**」為核心概念的邊緣端影像取證系統。

系統透過攝影機持續錄影，並使用 YOLO 進行邊緣端物件偵測。當符合事件觸發條件時，GhostProof 會自動保留事件發生前後的影像，接著以 **AES-256-GCM** 進行加密，再利用 **8-of-12 Erasure Coding** 將密文轉換為具容錯能力的 evidence shards，並將 shards 加入 **IPFS**。

同時，AES 金鑰透過 **Shamir's Secret Sharing 3-of-5** 拆分成五份，使證據內容與解密金鑰分離保存。

目前專案已完成 End-to-End PoC，可在本機原始事件影片、完整密文及 evidence shards 均不存在，且五個模擬金鑰節點中有兩個失效的情況下，透過 **IPFS 取得任意 8 個 evidence shards**，搭配剩餘 **3 份 Shamir key shares** 還原 AES 金鑰，最終重建事件影片並以 SHA-256 驗證資料完整性。

> 目前 YOLO 模組使用預訓練模型進行 `person` 偵測，主要作為事件觸發 PoC，尚未實作暴力行為或異常行為辨識模型。

---

## 系統架構

```text
Camera
│
├─────────────────────────────────────────────┐
│                                             │
▼                                             ▼
Continuous Recording                    YOLO Detection
│                                             │
20-minute Segments                       Person Trigger
│                                             │
▼                                             ▼
recordings/                         Pre-event 10 seconds
                                              +
                                    Post-event 30 seconds
                                              │
                                              ▼
                                         incident.mp4
                                              │
                       ┌──────────────────────┴──────────────────────┐
                       │                                             │
                       ▼                                             ▼
                    SHA-256                                    AES-256-GCM
                                                                     │
                                                                     ▼
                                                          8-of-12 Erasure Coding
                                                                     │
                                                               12 Shards
                                                                     │
                                                                     ▼
                                                                    IPFS
                                                                     │
                                                                  12 CIDs
                                                                     │
                                                                     ▼
                                                              metadata.json


                             AES-256 Key
                                  │
                                  ▼
                       Shamir Secret Sharing
                                  │
                               3-of-5
                                  │
              ┌───────────┬───────────┬───────────┬───────────┬───────────┐
              ▼           ▼           ▼           ▼           ▼
           node_1      node_2      node_3      node_4      node_5
```

---

## Recovery 流程

GhostProof 的證據與金鑰採用兩套不同的容錯機制：

```text
metadata.json
│
│ 讀取 IPFS CID
▼
IPFS
│
│ 取得任意 8 / 12 evidence shards
▼
Erasure Recovery
│
▼
Encrypted Incident
```

以及：

```text
Key Nodes
│
│ 取得任意 3 / 5 Shamir Shares
▼
Shamir Recovery
│
▼
AES-256 Key
```

最後：

```text
Encrypted Incident
        +
   AES-256 Key
        +
      Nonce
        │
        ▼
 AES-256-GCM Decryption
        │
        ▼
recovered_incident.mp4
        │
        ▼
 SHA-256 Verification
        │
        ▼
      PASS
```

---

## 專案結構

```text
GhostProof/
│
├─ main.py
│  └─ GhostProof 主要監控與事件觸發流程
│
├─ recover.py
│  └─ IPFS + Shamir Evidence Recovery
│
├─ requirements.txt
│  └─ Python 相依套件
│
├─ README.md
│
├─ src/
│  ├─ crypto.py
│  │  └─ AES-256-GCM 加解密
│  ├─ detector.py
│  │  └─ YOLO person detection 與 trigger cooldown
│  ├─ recorder.py
│  │  └─ 一般監控影片分段錄製
│  ├─ incident_recorder.py
│  │  └─ Pre-event / Post-event 事件影片錄製
│  ├─ integrity.py
│  │  └─ SHA-256 完整性驗證
│  ├─ erasure.py
│  │  └─ zfec 8-of-12 Erasure Coding
│  ├─ secret_sharing.py
│  │  └─ Shamir's Secret Sharing 3-of-5
│  ├─ ipfs_storage.py
│  │  └─ Kubo IPFS add / get 封裝
│  ├─ key_share_storage.py
│  │  └─ 模擬分散式 Key Share Nodes
│  └─ evidence_protection.py
│     └─ Evidence Protection Pipeline
│
├─ tests/
│  └─ 各核心模組功能測試
│
├─ recordings/
│  └─ 一般監控錄影，Runtime 產生，不納入 Git
│
├─ events/
│  └─ Event metadata / nonce / recovery files，Runtime 產生
│
└─ key_nodes/
   └─ Shamir key shares，Runtime 產生，不納入 Git
```

---

## 技術棧

### 核心開發
- Python 3
- OpenCV

### Edge AI
- Ultralytics YOLO
- 目前使用預訓練 YOLO 模型進行 `person` detection
- Confidence Threshold：`0.7`
- Trigger Cooldown：`10 seconds`

### Event Recording
- Continuous Surveillance Recording
- 20 分鐘自動分段
- Pre-event Buffer：`10 seconds`
- Post-event Recording：`30 seconds`

### 資料加密
- AES-256-GCM
- 每個事件使用獨立 AES-256 Key
- 12-byte Nonce
- Authenticated Encryption

### 資料完整性
- SHA-256

### Evidence Redundancy
- `zfec`
- 8-of-12 Erasure Coding
- 12 個 evidence shards 中任意 8 個即可恢復 encrypted evidence

### 分散式儲存
- IPFS
- Kubo
- 每個 evidence shard 上傳後取得 Content Identifier（CID）
- CID 儲存於 `metadata.json`

### 金鑰管理
- Shamir's Secret Sharing
- 3-of-5 Threshold
- AES key 拆分為 5 份
- 任意 3 份即可重建 AES key

---

## 開發環境配置

### 1. Clone Repository

```bash
git clone https://github.com/judyg1-lab/GhostProof.git
cd GhostProof
```

### 2. 建立 Python Virtual Environment

Windows：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. 安裝 Python Dependencies

```powershell
pip install -r requirements.txt
```

`requirements.txt`：

```text
opencv-python
cryptography
zfec
ultralytics
```

---

## IPFS / Kubo

GhostProof 使用 Kubo 作為 IPFS Node。

Kubo 並不是 Python Package，因此不包含於 `requirements.txt` 中，需要另外安裝。

初始化：

```powershell
ipfs init
```

啟動 IPFS daemon：

```powershell
ipfs daemon
```

GhostProof 執行期間必須保持 IPFS daemon 運作，才能進行 evidence shard 上傳與 recovery。

> 目前 PoC 使用單一 Kubo Node 驗證 IPFS Content-Addressed Storage 與 CID Recovery。真正的多節點異地 IPFS 儲存仍屬後續開發項目。

---

## 使用方式

### 啟動 GhostProof

確保 IPFS daemon 已啟動後：

```powershell
python main.py
```

### Event Trigger

目前提供兩種 Trigger：

- AI Trigger：YOLO 偵測到符合 confidence threshold 的 person 時觸發
- Manual Trigger：按下 `s`
- Exit：按下 `q`

---

## Evidence Protection Pipeline

```text
incident.mp4
↓
SHA-256
↓
AES-256-GCM
↓
8-of-12 Erasure Coding
↓
12 Shards
↓
IPFS
↓
12 CIDs
↓
metadata.json
```

同時：

```text
AES Key
↓
Shamir 3-of-5
↓
5 Key Shares
↓
5 Simulated Key Nodes
```

---

## Production Mode

目前 Production Mode 設定為：

```python
KEEP_PLAINTEXT = False
KEEP_ENCRYPTED_FILE = False
KEEP_LOCAL_SHARDS = False
```

當系統確認以下資料均成功建立：

```text
12 / 12 IPFS shards
metadata.json
nonce.bin
evidence.sha256
5 / 5 Shamir key shares
```

才會執行本機清理：

```text
incident.mp4      → DELETE
encrypted.bin     → DELETE
shards/           → DELETE
```

---

## Evidence Recovery

恢復事件：

```powershell
python recover.py event_YYYYMMDD_HHMMSS
```

Recovery 程式會：

1. 讀取 `metadata.json`
2. 找尋本機 evidence shards
3. 若本機 shard 不存在，透過 CID 從 IPFS 取得
4. 取得任意 8 個 shards
5. 重建 encrypted incident
6. 從 key nodes 搜尋可用 Shamir shares
7. 取得任意 3 份 shares
8. 重建 AES-256 key
9. 使用 AES-256-GCM 解密事件影片
10. 計算 recovered video SHA-256
11. 與原始 SHA-256 比對
12. 輸出 `recovered_incident.mp4`

---

## 已完成技術驗證

- [x] USB Camera 即時影像擷取
- [x] Continuous Surveillance Recording
- [x] 每 20 分鐘自動切分監控影片
- [x] YOLO Person Detection
- [x] Confidence Threshold Trigger
- [x] Trigger Cooldown
- [x] 10 秒 AI Warmup
- [x] 10 秒 Pre-event Buffer
- [x] 30 秒 Post-event Recording
- [x] Event Directory 自動建立
- [x] 每事件獨立 AES-256-GCM Key
- [x] SHA-256 Integrity Verification
- [x] 8-of-12 Erasure Coding
- [x] Shamir's Secret Sharing 3-of-5
- [x] Kubo / IPFS 串接
- [x] 12 個 Evidence Shards 自動加入 IPFS
- [x] IPFS CID 寫入 Metadata
- [x] IPFS CID Recovery
- [x] Production Mode 本機明文清理
- [x] 模擬五個獨立 Key Share Nodes
- [x] 8-of-12 Evidence Fault Tolerance
- [x] 3-of-5 Key Share Fault Tolerance
- [x] IPFS + Shamir 雙重容錯 Recovery
- [x] Recovery 後 SHA-256 完整性驗證

---

## Fault-Tolerance Verification

目前已實際驗證以下情境：

```text
Local incident.mp4   : unavailable
Local encrypted.bin  : unavailable
Local shards         : unavailable

IPFS shards          : recover 8 / 12

Key Node 1           : available
Key Node 2           : unavailable
Key Node 3           : available
Key Node 4           : unavailable
Key Node 5           : available

Available Key Shares : 3 / 5
```

最終：

```text
8 IPFS Shards
↓
Encrypted Evidence Reconstructed

3 Shamir Shares
↓
AES Key Reconstructed

Encrypted Evidence + AES Key
↓
AES-256-GCM Decryption
↓
Recovered Incident Video
↓
SHA-256 Verification
↓
PASS
```

---

## 目前限制

### AI Detection
目前使用 YOLO 預訓練模型進行 `person` detection，尚未實作真正的暴力行為、異常行為或犯罪事件辨識。

### IPFS
目前使用單一 Kubo Node，尚未部署真正的多節點異地 IPFS 儲存。

### Key Nodes
目前 `node_1 ~ node_5` 為同一台電腦上的模擬節點，尚未部署至不同實體裝置。

### Metadata Integrity
目前 evidence SHA-256 與 metadata 仍保存在本機，未來可加入：
- Digital Signature
- Remote Metadata Replication
- Trusted Timestamp
- Blockchain / Permissioned Ledger Anchoring

---

## Roadmap

### Phase 1 — Core PoC
- [x] Camera Integration
- [x] Continuous Recording
- [x] Event Trigger
- [x] Pre-event / Post-event Recording
- [x] AES-256-GCM
- [x] SHA-256
- [x] 8-of-12 Erasure Coding
- [x] Shamir 3-of-5
- [x] IPFS Integration
- [x] Evidence Recovery

### Phase 2 — Fault-Tolerant Architecture
- [x] Production Mode
- [x] Local Evidence Cleanup
- [x] IPFS CID-based Recovery
- [x] Simulated Distributed Key Nodes
- [x] 8-of-12 + 3-of-5 Dual Fault-Tolerance Test
- [ ] Multi-device IPFS Nodes
- [ ] Remote Key Share Nodes
- [ ] Automated Node Health Monitoring

### Phase 3 — Edge AI Enhancement
- [ ] Violence / Anomaly Detection Model
- [ ] Asynchronous AI Inference Pipeline
- [ ] TensorRT Optimization
- [ ] NVIDIA Jetson Deployment
- [ ] Raspberry Pi Edge Deployment

### Phase 4 — Evidence Trust & Deployment
- [ ] Metadata Digital Signature
- [ ] Trusted Timestamp
- [ ] Blockchain / Permissioned Ledger Hash Anchoring
- [ ] Docker Deployment
- [ ] Multi-device GhostProof Collaboration

---

## Security Notes

GhostProof 目前主要驗證的是：

> Evidence redundancy + Key redundancy + Content integrity

目前 PoC 中的 Key Nodes 與 IPFS Node 尚未真正部署至不同實體設備，因此不應視為完整的 Production-grade Distributed Evidence System。

此外，目前 `secret_sharing.py` 為專案自行實作之 Shamir's Secret Sharing PoC，用於驗證門檻式金鑰恢復流程，尚未經過正式密碼學安全稽核。

---

## License

本專案目前以研究、教學與技術驗證為主要用途。