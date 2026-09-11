# AI-Powered Number Plate Recognition & IoT Vision System (Software Edition)

A high-performance, 100% software-based **Automatic Number Plate Recognition (ANPR / ALPR)** and **IoT Smart Barrier Access Control** system. This solution requires **no physical hardware** and operates seamlessly using PC/Laptop webcams, simulated virtual IoT camera video feeds, or image/video uploads.

---

## 🛠️ Technology Stack Used

| Layer | Technology | Purpose & Implementation Details |
|---|---|---|
| **AI Computer Vision** | **OpenCV (`cv2`)** | Image preprocessing, CLAHE contrast enhancement, bilateral noise filtering, edge detection (Canny/Sobel), morphological gradient transformations, contour detection, and perspective deskewing. |
| **Deep Learning & OCR** | **EasyOCR (PyTorch / CRNN)** | Deep learning optical character recognition engine that reads alphanumeric characters from localized license plates. |
| **OCR Error Post-Correction** | **Python Regex & Heuristics** | Normalizes characters, resolves optical character confusion (`0` vs `O`, `1` vs `I`, `8` vs `B`, `5` vs `S`), and matches international/state license plate patterns. |
| **Backend Web Server** | **Python FastAPI & Uvicorn** | Asynchronous, high-throughput REST API serving endpoints for recognition, vehicle management, audit logs, and barrier control. |
| **Database & ORM** | **SQLite & SQLAlchemy** | Embedded relational database managing vehicle whitelist/blacklist registries, historical scan logs, confidence metrics, and snapshot paths. |
| **Virtual IoT Camera Simulator** | **Python Stream Simulator** | Generates real-time virtual IoT camera events and feeds synthetic vehicle samples without needing physical microcontrollers or external cameras. |
| **Frontend UI / Dashboard** | **HTML5, TailwindCSS, Vanilla JS, Chart.js, Lucide Icons** | Dark-mode glassmorphic control room dashboard with live webcam view, real-time detection cards, visual smart barrier arm animation, and traffic analytics. |

---

## 📐 System Architecture

```
[ Input Sources ]
 ├── PC / Laptop Webcam
 ├── Virtual IoT Camera Simulator (Auto-feed)
 └── Image / Video File Uploads (Drag & Drop)
        │
        ▼
[ FastAPI Backend Ingestion ]
        │
        ▼
[ OpenCV Image Preprocessor ] ──► (Bilateral Filter + CLAHE + Edge Gradients)
        │
        ▼
[ License Plate ROI Detector ] ──► (Contour Analysis & Aspect Ratio Filtering)
        │
        ▼
[ Deep Learning OCR Engine ] ──► (EasyOCR Character Recognition)
        │
        ▼
[ Regex Formatter & Disambiguator ]
        │
        ▼
[ Access Control Rule Engine ]
 ├── Whitelisted ──► [ Open Smart Barrier Gate Relay ]
 ├── Blacklisted ──► [ Trigger Security Alert & Lock Gate ]
 └── Unregistered ──► [ Access Denied & Logged ]
        │
        ▼
[ SQLite Database & Live Web Dashboard ]
```

---

## 🌟 Key Features

1. **Zero Hardware Requirement**:
   - Built-in **Virtual IoT Camera Simulator** with pre-generated sample vehicle plates (Whitelisted VIPs, Blacklisted alerts, Guest vehicles, and Unknown visitors).
   - Live **Webcam Support** via browser MediaDevices API with single-click capture & scan.
   - **Drag-and-Drop Image Uploader** for instant photo testing.

2. **Accurate Plate Recognition**:
   - Advanced multi-stage OpenCV image preprocessing ensures robust detection across varying contrast, lighting, and angles.
   - Character disambiguation corrects common OCR optical confusions.

3. **Smart Access Control**:
   - **Whitelist**: Authorized vehicles automatically trigger simulated smart barrier gate opening.
   - **Blacklist**: Security alerts triggered and gate locked.
   - **Guest / Vendor**: Temporary permitted access.
   - **Manual Operator Override**: One-click manual open/close controls.

4. **Analytics & Audit Logs**:
   - Live traffic volume charts and access ratio doughnut breakdown.
   - Searchable, filterable access log table with one-click **CSV Export**.

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
Run the one-click launcher script:
```bash
python run.py
```
This will:
1. Generate test vehicle plates in `backend/sample_plates/`.
2. Start the FastAPI backend server on `http://127.0.0.1:8000`.
3. Automatically open your browser to the live dashboard.

---

## 📡 API Endpoints

- `POST /api/recognize/upload` — Upload an image file for license plate detection and logging.
- `POST /api/recognize/frame` — Ingest a base64 webcam frame or camera snapshot.
- `GET /api/vehicles/` — List registered vehicles with search and tier filters.
- `POST /api/vehicles/` — Register a new vehicle (`WHITELIST`, `BLACKLIST`, `GUEST`).
- `GET /api/logs/` — Fetch paginated recognition logs.
- `GET /api/logs/export/csv` — Download access logs in CSV format.
- `GET /api/logs/stats` — Real-time KPI summary and barrier status.
- `POST /api/simulator/trigger` — Trigger a virtual IoT camera recognition scan.
- `POST /api/simulator/barrier/control` — Manual barrier gate open/close override.
- `GET /docs` — Interactive Swagger API documentation.
