# Zero-Touch AI Features Implementation Plan 🧠

This plan outlines the steps to upgrade Zero-Touch from a navigation tool to a **Smart Surgical Assistant**, with a **Local-First (Ollama)** architecture.

## 1. Clinical Q&A Assistant (Speech-to-Text-to-LLM)
**Goal**: Enable the assistant to answer medical questions (e.g., "What is the max dose of Lidocaine?") using your local Ollama model.

### Implementation Steps:
1.  **Update `IntentEngine`**: 
    -   Modify `_llm_parse` to detect "Knowledge Queries" (vs Surgical Commands).
    -   If a query is detected, send it to **Ollama** (using the active model).
    -   Return the full text answer.
    -   *Fallback*: Only use Gemini if Ollama is unreachable.

## 2. Visual Pathology Analysis (Vision-to-LLM) 👁️
**Goal**: The surgeon can point at the screen and ask "What anomaly is this?", and the Local AI analyzes the video frame.

### Implementation Steps:
1.  **Modify `VisionManager`**:
    -   Add `get_current_frame()` to capture the live video feed.
2.  **Update `IntentEngine`**:
    -   Add `analyze_image(text, image_bytes)` method.
    -   **Primary**: Send image + prompt to **Ollama** (requires a vision model like `llava` or `moondream`).
    -   **Fallback**: Gemini 1.5 Pro.
3.  **Update `main_audio.py`**:
    -   Route `ANALYZE_REGION` intents to this new vision pipeline.

## 3. Automated Operative Notes ("The Scribe") 📝
**Goal**: Automatically generate a PDF report of actions taken during the surgery.

### Implementation Steps:
1.  **Logging**: Track all valid intents in `StateManager`.
2.  **Summarization**: At the end of the session, send the event log to **Ollama** to generate a "Surgical Procedure Note".
3.  **PDF Generation**: Save this text as a formatted PDF.

---

## 🛠️ User Prerequisites (Your Action Items)

### 1. Ollama Models
You need to ensure you have the right models pulled:
-   **Chat/Logic**: You already have `phi2-local`. (Consider pulling `llama3` or `medllama2` for better medical knowledge).
-   **Vision**: You **MUST** pull a vision-capable model for Phase 2.
    ```powershell
    ollama pull llava
    # OR
    ollama pull moondream
    ```

### 2. Python Dependencies
Install libraries for PDF reporting and Image handling:
```powershell
pip install reportlab Pillow
```

### 3. API Keys (Fallback Only)
-   Keep `GEMINI_API_KEY` in `.env` just in case the local model is too slow or hallucinates on complex vision tasks.
