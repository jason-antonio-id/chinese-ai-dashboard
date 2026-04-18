---
title: Chinese AI Dashboard
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
app_file: app.py
pinned: false
---
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

## 🚀 Get Started in 5 Minutes

### ① Prerequisites
- **Python 3.8–3.11**  
- **Tesseract OCR** ([Windows installer](https://github.com/UB-Mannheim/tesseract/wiki) / `brew install tesseract` on Mac)  
- A **Firebase project** with Firestore and Authentication enabled.

### ② Clone & Install
```bash
git clone https://github.com/jason-antonio-id/chinese-ai-dashboard.git
cd chinese-ai-dashboard
pip install -r requirements.txt
