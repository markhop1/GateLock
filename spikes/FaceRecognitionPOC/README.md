# Gatelock – Facial Recognition POC on Raspberry Pi 5

This project implements a real‑time facial recognition Proof of Concept (POC) using pre‑trained InsightFace models on a Raspberry Pi 5.  
The goal is to demonstrate that a small edge device can detect faces, extract facial embeddings, and recognize known individuals without training models from scratch.

## Main Features

- Real‑time face detection and recognition.
- Lightweight InsightFace model package `buffalo_s`, ideal for Raspberry Pi.
- Automatic generation of a facial embeddings database.
- Cosine similarity–based face matching.
- Live visualization using OpenCV.
- Modular and easily extendable architecture.

## Project Structure

```
Gatelock/
└── Spikes/
    ├── build_db.py                 # Build facial embeddings database
    ├── realtime_recognizer.py      # Real-time recognition
    ├── known_faces/                # User-provided training photos
    │   └── name1/
    │       ├── photo1.jpg
    │       └── ...
    │   └── name2/
    │   └── ...
    ├── face_embeddings.npy         # Auto-generated embeddings
    └── face_labels.npy             # Auto-generated labels
```

## Requirements

- Raspberry Pi 5 running Raspberry Pi OS (64‑bit).
- USB webcam or official Raspberry Pi camera.
- Python 3.10 or later.
- Internet connection (only required on first run to download InsightFace model package).

## Installation

### 1. Install system dependencies

```bash
sudo apt update
sudo apt install python3-venv python3-full python3-opencv -y
```

### 2. Create and activate a Python virtual environment

```bash
cd ~/Gatelock/Spikes
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install insightface onnxruntime onnx numpy opencv-python
```

## Preparing Face Images

Place photos of each person you want to recognize inside:

```
known_faces/<person_name>/
```

Example:

```
known_faces/mark/
    photo1.jpg
    photo2.jpg
```

Recommendations:

- Use several photos per person.
- Use different angles.
- Ensure good lighting.
- Face centered and unobstructed.

## 1. Generate the Facial Database

Run:

```bash
python build_db.py
```

This script:

- Detects faces in your provided photos.
- Extracts normalized embeddings using InsightFace.
- Creates two files:

  - `face_embeddings.npy`  
  - `face_labels.npy`

## 2. Run Real‑Time Recognition

```bash
python realtime_recognizer.py
```

The script will:

- Open the camera feed.
- Detect faces in each frame.
- Extract embeddings.
- Compare them against your database.
- Draw bounding boxes and names in the live window.

To exit, press **Q** while the OpenCV window is focused.

## How It Works

1. Face detection via InsightFace’s `buffalo_s` detector.
2. Embedding extraction using MobileFaceNet (included in buffalo_s).
3. L2 normalization of embeddings.
4. Cosine similarity matching with stored user embeddings.
5. Recognition if similarity exceeds threshold (default 0.5).

## Debug Information

- If no faces are detected, the text “No faces detected” appears.
- Every 30 frames, debug info is printed in the terminal.
- During recognition, the display shows:
  ```
  person_name (0.78)
  ```
  where 0.78 is the cosine similarity score.

## Limitations

- Sensitive to poor lighting conditions.
- CPU-only inference on Raspberry Pi results in moderate performance.
- Recognition works only for people stored in `known_faces`.
- `buffalo_s` pre-trained models are licensed for non-commercial/research use only.

## Licenses

- InsightFace library: MIT License.
- InsightFace `buffalo_s` model package: non-commercial / research‑only license.
