# 🤖 人工智能工具平台 · Chinese AI Dashboard

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-306998?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Firebase](https://img.shields.io/badge/Firebase-🔥-FFA000?logo=firebase)](https://firebase.google.com)
[![Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-Live%20Demo-yellow)](https://huggingface.co/spaces/JasonAntonio/chinese-ai-dashboard)
[![Status](https://img.shields.io/badge/status-active-success)](#)

**Nine AI tools. One dashboard. Built for Chinese business.**  
*九种人工智能工具。一个仪表板。专为中国商业打造。*

### 🚀 [**Try the Live Demo on Hugging Face →**](https://huggingface.co/spaces/JasonAntonio/chinese-ai-dashboard)

</div>

---

## ✨ Why This Exists

Most AI platforms ignore the nuances of **Chinese language** and **e-commerce data**.  
This dashboard bridges that gap by offering **bilingual, ready-to-use tools** designed for real-world Chinese business workflows—such as analyzing reviews, detecting fake comments, predicting prices, and more.

---

## 🌐 Live Demo

Try the app instantly without installation:  
👉 **[https://huggingface.co/spaces/JasonAntonio/chinese-ai-dashboard](https://huggingface.co/spaces/JasonAntonio/chinese-ai-dashboard)**

---

## 🧰 The Toolkit

| ⚡ Tool | 🎯 What It Does |
|--------|----------------|
| **💬 Sentiment Analyzer** | Reads Chinese reviews and determines whether customers are happy, neutral, or unhappy. |
| **🔍 Keyword Extractor** | Extracts important keywords from product descriptions or feedback using TF‑IDF. |
| **📄 OCR Scanner** | Extracts text from images (receipts, product labels, Chinese + English). |
| **👥 Churn Prediction** | Predicts customers who may stop buying so you can act early. |
| **📈 Sales Forecast** | Predicts next month's sales using Facebook Prophet (requires sales history upload). |
| **🛒 Recommendations** | Recommends products using similar-user behavior patterns. |
| **🚨 Fake Review Detector** | Detects suspicious reviews using linguistic signals + duplicate detection. |
| **🖼️ Image Classifier** | Identifies products in images using MobileNetV2 (trained on large-scale datasets). |
| **💰 Price Prediction** | Estimates optimal pricing using category, rating, review count, and brand tier. |

---

## 📋 Prerequisites

- **Python 3.8 – 3.11** *(TensorFlow may not work well on 3.12+)*
- **Tesseract OCR** — required for the OCR Scanner
  - **Windows:** Download and install from [UB‑Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)  
    Install location example: `C:\Program Files\Tesseract-OCR`
  - **macOS:** `brew install tesseract`
  - **Linux:** `sudo apt install tesseract-ocr`
- **Firebase account** *(free tier works)* — used for storing user data and settings

---

## 🚀 Get Started in 5 Minutes

> 💡 **Don't want to install anything?** Just use the [**live demo**](https://huggingface.co/spaces/JasonAntonio/chinese-ai-dashboard) instead!

### 1) Clone the repository

    git clone https://github.com/jason-antonio-id/chinese-ai-dashboard.git
    cd chinese-ai-dashboard

### 2) Create and activate a virtual environment (recommended)

**Windows (PowerShell):**

    python -m venv .venv
    .venv\Scripts\Activate.ps1

**macOS/Linux:**

    python -m venv .venv
    source .venv/bin/activate

### 3) Install dependencies

    pip install -r requirements.txt

### 4) Configure Firebase

Set up Firebase credentials so the app can read/write user data.  
> If your repo includes a `.env.example` file, copy it to `.env` and fill in the values.  
> Otherwise, follow the configuration variables used in your code (commonly API keys / service account file).

### 5) Run the Flask app

    python app.py

Then open the app URL shown in your terminal (commonly `http://127.0.0.1:5000`).

---

## 📌 Notes

- Some AI features may require model downloads on first run.
- OCR accuracy improves with high-resolution, well-cropped images.
- The hosted version on Hugging Face may take a moment to wake up if it has been idle.

---

## 🤝 Contributing

Contributions are welcome!  
If you'd like to add a new tool or improve existing models:

1. Fork the repo
2. Create a feature branch
3. Commit changes
4. Push your branch
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 👤 Author

**Jason Antonio**
- GitHub: [@jason-antonio-id](https://github.com/jason-antonio-id)
- Hugging Face: [@JasonAntonio](https://huggingface.co/JasonAntonio)
- Live Demo: [Chinese AI Dashboard](https://huggingface.co/spaces/JasonAntonio/chinese-ai-dashboard)

---

## ❤️ Built for Chinese business intelligence

Designed to help businesses understand data faster—especially Chinese reviews, images, and product signals.
