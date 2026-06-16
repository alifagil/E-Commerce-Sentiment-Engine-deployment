# ReviewIN AI - Deployment

<div align="center">

# 🌐 ReviewIN AI

AI-powered sentiment analysis web application for Shopee and Tokopedia reviews.

### Live Demo

https://e-commerce-sentiment-engine-deploym.vercel.app/

</div>

---

## 📖 Overview

ReviewIN AI is a web-based sentiment analysis application capable of analyzing Indonesian e-commerce reviews in real time.

Users can directly paste reviews copied from:

- Shopee
- Tokopedia

and receive sentiment predictions instantly.

---

## 🚀 Features

### Multi-Platform Support

Supported platforms:

- Shopee
- Tokopedia

---

### Automatic Review Parsing

The system automatically extracts and separates reviews from raw marketplace copy-paste data.

#### Shopee Parser

Removes:

- Usernames
- Timestamps
- Video metadata
- UI artifacts

#### Tokopedia Parser

Removes:

- Product variants
- Relative timestamps
- Helpful vote counters
- Marketplace UI elements

---

### Sentiment Classification

Output classes:

- 😊 Positive
- 😐 Neutral
- 😞 Negative

---

### Confidence Visualization

Each prediction includes:

- Positive confidence
- Neutral confidence
- Negative confidence

Displayed using:

- Doughnut Charts
- Confidence Bars
- Result Cards

---

## 🏗 Application Workflow

```text
User Input
      │
      ▼
Platform Selection
      │
      ▼
Review Parser
      │
      ▼
Text Cleaning
      │
      ▼
TF-IDF Vectorizer
      │
      ▼
Linear SVM
      │
      ▼
Confidence Score
      │
      ▼
Frontend Visualization
```

---

## 🧠 Machine Learning Model

Model:

```text
Linear Support Vector Machine (SVM)
```

Feature Extraction:

```text
TF-IDF Vectorizer
```

Accuracy:

```text
94.92%
```

---

## 📂 Project Structure

```text
.
├── app.py
├── svm_model.pkl
├── tfidf_vectorizer.pkl
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   ├── js/
│   │   └── script.js
│   │
│   └── images/
│
└── README.md
```

---

## 🛠 Technologies

Backend:

- Flask
- Python

Machine Learning:

- TF-IDF
- Linear SVM
- Scikit-Learn

Frontend:

- HTML
- CSS
- JavaScript

Visualization:

- Chart.js

Deployment:

- Vercel

---

## ▶ Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

---

## 🌐 Live Application

Demo:

https://e-commerce-sentiment-engine-deploym.vercel.app/

---

## 👨‍💻 Authors

- Alif Agil
- Ahmad Rizki Wardana
- Muadz

---

## 📄 License

Educational and academic purposes only.
