<div align="center">

# 🧠 Zero-Touch – Multimodal Surgeon Assistant

![Zero-Touch](https://img.shields.io/badge/Zero--Touch-Surgical%20Intelligence-blueviolet?style=for-the-badge&logo=medical-cross&logoColor=white)

**🏥 Gesture + Gaze + Voice Controlled Surgical Assistant**

[![Privacy First](https://img.shields.io/badge/Privacy-Local%20First-green?style=flat-square)](#)
[![Multimodal](https://img.shields.io/badge/Multimodal-Gesture%20%2B%20Gaze%20%2B%20Voice-orange?style=flat-square)](#)
[![Hybrid AI](https://img.shields.io/badge/Hybrid-AI%20Cloud%20%2B%20Local-blue?style=flat-square)](#)
[![Real-Time](https://img.shields.io/badge/Real--Time-Low%20Latency-brightgreen?style=flat-square)](#)

*Enabling hands-free surgical image navigation through multimodal AI fusion*

</div>

---

## 🎯 Problem Statement

Surgeons need to interact with medical imaging **without breaking sterility or workflow**.

### 🔍 The Challenge

* Surgeons cannot touch screens or keyboards during sterile procedures
* Traditional voice-only systems lack precision for medical imaging
* Existing solutions don't combine gesture, gaze, and voice intelligently
* High latency and cloud dependency compromise real-time surgical workflows
* Lack of context-aware multimodal fusion reduces accuracy

---

## 🚀 Our Solution: Zero-Touch Multimodal Surgeon Assistant

Zero-Touch is a **real-time, multimodal surgical assistant** that fuses **gesture tracking, gaze estimation, and voice commands** to enable hands-free, sterile interaction with medical imaging systems.

It combines **MediaPipe vision models**, **Whisper ASR**, and **lightweight LLMs** with a custom **multimodal fusion engine** to achieve precise, context-aware surgical navigation.

<div align="center">

```mermaid
graph TD
    A[👋 Gesture Input] --> D[Multimodal Fusion Engine]
    B[👁️ Gaze Tracking] --> D
    C[🎙️ Voice Commands] --> D
    
    A --> A1[MediaPipe Hands]
    B --> B1[MediaPipe Face Mesh]
    C --> C1[Whisper ASR]
    
    A1 --> A2[Pinch/Swipe/Wave Detection]
    B1 --> B2[Eye Landmark Extraction]
    C1 --> C2[Command Parser LLM]
    
    A2 --> D
    B2 --> D
    C2 --> D
    
    D --> E[Timestamp Alignment]
    E --> F[Intent Classifier]
    F --> G[Action Dispatcher]
    
    G --> H1[Zoom Region]
    G --> H2[Scroll/Pan]
    G --> H3[Highlight Area]
    G --> H4[Load Image]
    
    H1 --> I[Visual Feedback Overlay]
    H2 --> I
    H3 --> I
    H4 --> I
```

</div>

---

## ⭐ Key Features

### � Real-Time Gesture Tracking

* **MediaPipe Hands** for precise hand landmark detection
* Pinch, swipe, wave, and custom gesture recognition
* Region-of-interest selection via hand pointing
* Adaptive gesture personalization per surgeon

---

### 👁️ Gaze Estimation & Screen Mapping

* **MediaPipe Face Mesh** for eye landmark extraction
* Real-time gaze direction estimation
* Calibrated screen coordinate mapping
* Visual feedback overlay showing gaze focus
* Tested under surgical lighting conditions

---

### 🎙️ Voice Command Intelligence

* **Whisper Tiny** for local, low-latency ASR
* Lightweight LLM (Phi-2) for flexible command parsing
* Error recovery with clarification prompts
* Memory state tracking (active image, mode, context)
* Medical terminology support

---

### 🧠 Multimodal Fusion Engine

* Timestamp-aligned fusion of gesture + gaze + voice
* Rule-based and transformer-based intent classification
* Context-aware action disambiguation
* Confidence scoring for each modality
* Fallback strategies for low-confidence inputs

---

### ⚡ Low-Latency Real-Time Processing

* **<200ms** end-to-end latency target
* Local-first processing (no cloud dependency)
* Optimized inference pipelines
* Parallel modality processing
* Hardware acceleration support

---

### 🎯 Surgical Workflow Integration

* Sterile, hands-free operation
* Medical image navigation (zoom, pan, scroll)
* **Gaze-Aware Visual Analysis**: Point at a region and ask "Analyze this"
* **Clinical Q&A**: Voice access to medical databases and scan interpretation
* **Automated Operative Notes**: Local AI-generated procedure summaries (PDF)
* Multi-image comparison support
* Customizable action mappings

---

## 🏗️ System Architecture

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Gesture Stream │  │   Gaze Stream   │  │   Voice Stream  │
│  MediaPipe Hands│  │ MediaPipe Face  │  │  Whisper ASR    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Gesture Parser  │  │  Gaze Calibrator│  │ Command Parser  │
│ (Pinch/Swipe)   │  │ (Screen Coords) │  │  (LLM/Rules)    │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Fusion Engine     │
                    │  Timestamp Align   │
                    │  Intent Classifier │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Action Dispatcher │
                    │  State Manager     │
                    └─────────┬──────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Image Control  │  │ Visual Feedback │  │ Audio Feedback  │
│  (Zoom/Pan)     │  │   Overlay       │  │   (TTS)         │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

---
## 🛠️ Technology Stack

<div align="center">

### Core

![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-ML%20Framework-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)

### Vision & Gesture

![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands%20%2B%20Face-00C853?style=for-the-badge)
![Gaze Tracking](https://img.shields.io/badge/Gaze-Estimation-4285F4?style=for-the-badge)

### Voice & Language

![Whisper](https://img.shields.io/badge/Whisper-Tiny%20ASR-412991?style=for-the-badge)
![TinyLlama](https://img.shields.io/badge/TinyLlama-Command%20Parser-FF6B6B?style=for-the-badge)
![Phi-2](https://img.shields.io/badge/Phi--2-Lightweight%20LLM-00A4EF?style=for-the-badge)

### Fusion & Integration

![Transformer](https://img.shields.io/badge/Transformer-Multimodal%20Fusion-FFA500?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)

</div>

---

## 🔐 Ethics & Safety

* Privacy-first architecture
* User-controlled data
* Non-prescriptive AI responses
* Transparent AI decisions
* Accessibility-focused design

---

## 🚀 Getting Started

### Prerequisites

```bash
Python 3.8+
pip
Ollama (optional, for local AI)
Webcam/Camera device
```

### Installation

```bash
git clone https://github.com/YeswanthRam28/Zero-Touch.git
cd Zero-Touch
pip install -r requirements.txt
python main_audio.py
```

---

## 📸 Project Components

## 🎯 Use Cases

* **Sterile Surgical Procedures**: Navigate medical imaging without breaking sterility
* **Operating Room Workflows**: Hands-free control during active surgery
* **Medical Image Review**: Zoom, pan, and annotate diagnostic images
* **Radiology Consultations**: Multi-image comparison and analysis
* **Training & Simulation**: Surgical education with multimodal interaction
* **Emergency Medicine**: Rapid image access in time-critical situations

---

## 🏆 Innovation Highlights

* **Multimodal Fusion**: First-of-its-kind gesture + gaze + voice integration for surgery
* **Real-Time Performance**: <200ms latency for surgical-grade responsiveness
* **Gaze-Aware Vision AI**: Uses `llava` for focused medical scan interpretation
* **Local-First Clinical Q&A**: Offline access to medical knowledge using `phi-2`/`llama3`
* **Autonomous Surgical Scribe**: Generates professional PDF reports from procedure logs
* **Zero-Cloud Dependency**: Maximum privacy and reliability in the OR

---

## 👨‍💻 Project Collaborators

<table align="center">
<tr>
<th>Role</th>
<th>Team Member</th>
<th>GitHub</th>
</tr>
<tr>
<td><b>🎯 Vision & Gaze Lead</b><br/><i>Gesture Tracking, Eye Tracking, Visual Feedback</i></td>
<td><b>Raghavan</b></td>
<td><a href="https://github.com/Raghavan7777"><img src="https://img.shields.io/badge/GitHub-Profile-181717?style=flat-square&logo=github"></a></td>
</tr>
<tr>
<td><b>🎙️ Audio & Intent Lead</b><br/><i>Voice Recognition, Command Parsing, AI Integration</i></td>
<td><b>Yeswanth Ram</b></td>
<td><a href="https://github.com/Yeswanthram28"><img src="https://img.shields.io/badge/GitHub-Profile-181717?style=flat-square&logo=github"></a></td>
</tr>
<tr>
<td><b>🧠 Fusion & Integration Lead</b><br/><i>Multimodal Fusion, System Integration, Testing</i></td>
<td><b>VetriSelvan</b></td>
<td><a href="https://github.com/njr-vetri"><img src="https://img.shields.io/badge/GitHub-Profile-181717?style=flat-square&logo=github"></a></td>
</tr>
</table>

---

<div align="center">

<img src="https://img.shields.io/badge/Built%20With-❤️-red?style=for-the-badge">
<img src="https://img.shields.io/badge/Focus-Accessible%20Technology-blue?style=for-the-badge">

</div>

---

> *"Surgical technology should be intelligent, hands-free, and seamlessly integrated into the workflow."*

---
