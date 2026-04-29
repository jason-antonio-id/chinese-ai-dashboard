# 🤖 人工智能工具平台 · Chinese AI Dashboard

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8%2B-306998?logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Firebase](https://img.shields.io/badge/Firebase-🔥-FFA000?logo=firebase)](https://firebase.google.com)
[![Status](https://img.shields.io/badge/status-active-success)](#)

**Nine AI tools. One dashboard. Built for Chinese business.**  
*九种人工智能工具。一个仪表板。专为中国商业打造。*

</div>

---

## ✨ Why This Exists

Most AI platforms ignore the nuances of Chinese language and e‑commerce data.  
This dashboard bridges that gap — offering **bilingual, ready‑to‑use tools** that understand Chinese reviews, detect fake comments, predict prices, and more.

---

## 🧰 The Toolkit

| ⚡ Tool | 🎯 What It Does |
|--------|----------------|
| **💬 Sentiment Analyzer** | Reads Chinese reviews and tells you if customers are happy, neutral, or unhappy. |
| **🔍 Keyword Extractor** | Pulls out the most important words from product descriptions or feedback using TF‑IDF. |
| **📄 OCR Scanner** | Snaps text from images — perfect for scanning receipts or product labels (Chinese + English). |
| **👥 Churn Prediction** | Flags customers who might stop buying, so you can reach out before they leave. |
| **📈 Sales Forecast** | Predicts next month's sales using Facebook Prophet — upload your history, get a forecast. |
| **🛒 Recommendations** | Suggests products a user might like based on similar shoppers' behavior. |
| **🚨 Fake Review Detector** | Spots fake reviews with 5 linguistic signals + duplicate detection — protects your brand. |
| **🖼️ Image Classifier** | Identifies products in photos using MobileNetV2 (trained on 14 million images). |
| **💰 Price Prediction** | Estimates optimal price from category, rating, review count, and brand tier. |

---

## 📋 Prerequisites

- **Python 3.8 – 3.11** (TensorFlow may not work on 3.12+)
- **Tesseract OCR** – required for the OCR Scanner tool
  - Windows: Download from [UB‑Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) (install to `C:\Program Files\Tesseract-OCR`)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`
- **Firebase account** (free tier works) – for storing user data and settings

---

## 🚀 Get Started in 5 Minutes

### ① Clone the repository

```bash
git clone https://github.com/jason-antonio-id/chinese-ai-dashboard.git
cd chinese-ai-dashboard
