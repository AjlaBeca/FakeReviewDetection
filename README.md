# Fake Review Detection – Research & Deployed System

This repository contains the code for my Bachelor's thesis project, **Fake Review Detection Using NLP and Machine Learning**.

The project consists of:

- **Research component** – multiple ML models were trained and evaluated.
- **Deployed software system** – three models (two from the Hugging Face hub + one fine-tuned RoBERTa from this project) are exposed through a FastAPI backend and a browser extension.

---

## Project Overview

The goal of this project is to study how well ML models can distinguish **AI-generated** from **human-written** reviews and translate those findings into a practical, usable tool.

During research, several model families were explored, including:

- Classical ML models (TF-IDF + classifiers)
- RNN-based models
- Transformer-based models (RoBERTa, etc.)

For the deployed system, **three models** are used:

1. Two pre-trained models from Hugging Face
2. One fine-tuned RoBERTa model developed as part of this project

---

## Deployed System

The deployed system consists of:

- **FastAPI backend**
- **Browser extension** (Firefox / Chrome)

**Workflow:**

1. Receives text input from the extension
2. Runs inference using all three deployed models
3. Returns classification labels and confidence scores

---

## Backend (FastAPI)

The backend handles:

- API requests from the browser extension
- Text preprocessing
- Model loading and caching
- Inference and confidence scoring

---

## Browser Extension

The browser extension allows users to:

- Select text on a webpage
- Send it to the backend for analysis
- View predicted labels and confidence scores

---

## Running the Project Locally

**Backend:**

```bash
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

## Firefox Extension:

- Open about:debugging#/runtime/this-firefox
- Click Load Temporary Add-on
- Select manifest.json from extension/firefox/

## Author

Ajla Beća
BSc Information Technology
