# MerchantGPT 🚀

> **Autonomous AI Growth Manager for E-commerce Merchants**

MerchantGPT is a production-grade AI SaaS platform that helps online merchants analyze sales, refunds, abandoned carts, customer behavior, and revenue trends using **Gemini 3.6 Flash**, **FastAPI**, **PostgreSQL**, and **Next.js**.

---

## 🌐 Live Demo

* **Frontend:** https://merchant-gpt.vercel.app
* **Backend API:** https://merchantgpt-api.onrender.com/docs
* **GitHub:** https://github.com/Manish-kumar-reddy/MerchantGPT

---

## ✨ Features

* 🤖 AI Business Chat powered by Gemini 3.6 Flash
* 📊 Executive Analytics Dashboard
* 💸 Revenue Leak Detection
* 🛒 Abandoned Cart Recovery Insights
* 👥 RFM Customer Segmentation
* ⚠️ Customer Churn Prediction
* 📣 AI Marketing Campaign Generator
* 📈 Weekly Executive Reports
* 🔐 JWT Authentication
* 🧠 Persistent Chat Memory with pgvector

---

## 📸 Screenshots

### Dashboard

![Dashboard](docs/dashboard.png)

### AI Chat

![AI Chat](docs/chat.png)

### Revenue Leak Detection

![Revenue Leaks](docs/leaks.png)

### Customer Segmentation

![Customer Segments](docs/segments.png)

---

## 💼 Business Value

MerchantGPT helps e-commerce businesses:

* Identify revenue leaks before they become costly
* Recover abandoned carts with AI-generated campaigns
* Segment customers based on purchasing behavior
* Predict churn risk using merchant analytics
* Generate executive-ready business reports
* Ask natural-language questions about business performance

---

## 🏗 Cloud Architecture

```text
              Vercel
        (Next.js Frontend)
                 │
        HTTPS + JWT API
                 │
              Render
        (FastAPI Backend)
                 │
        PostgreSQL + pgvector
              (Neon Database)
                 │
         Gemini 3.6 Flash AI
```

---

## 🛠 Tech Stack

### Frontend

* Next.js 15
* TypeScript
* Tailwind CSS
* Recharts
* Lucide React

### Backend

* FastAPI
* SQLAlchemy
* PostgreSQL
* pgvector
* JWT Authentication
* Pydantic

### AI

* Gemini 3.6 Flash
* Function / Tool Calling
* Context Memory
* SQL-powered Business Analytics

### Cloud

* Vercel (Frontend)
* Render (Backend)
* Neon (Database)

---

## 🤖 AI Capabilities

MerchantGPT can answer questions like:

* Why did revenue drop this week?
* Which customers are most likely to churn?
* What products have the highest refund rates?
* Generate an abandoned cart recovery email.
* Create a campaign for loyal customers.
* Produce a CEO weekly executive report.

The AI retrieves live merchant data through SQL tools before generating executive-quality business insights.

---

## 🔑 Demo Credentials

| Field        | Value                     |
| ------------ | ------------------------- |
| **Email**    | `demo@aurorahome.example` |
| **Password** | `Demo@12345`              |

---

## ⚙️ Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/Manish-kumar-reddy/MerchantGPT.git
cd MerchantGPT
```

### 2. Backend

```bash
cd backend

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend runs at:

```text
http://localhost:8000
```

### 3. Frontend

```bash
cd ../frontend

npm install

npm run dev
```

Frontend runs at:

```text
http://localhost:3000
```

---

## 🧠 AI Workflow

```text
User Question
      │
      ▼
 Gemini decides the required tool
      │
      ▼
 FastAPI executes SQL analytics
      │
      ▼
 PostgreSQL returns merchant data
      │
      ▼
 Gemini generates business insights
      │
      ▼
 Conversation stored in pgvector
```

---

## 📁 Project Structure

```text
MerchantGPT
│
├── frontend/
│   ├── src/
│   ├── components/
│   └── lib/
│
├── backend/
│   ├── app/
│   ├── scripts/
│   ├── tests/
│   └── requirements.txt
│
├── docs/
│   ├── dashboard.png
│   ├── chat.png
│   ├── leaks.png
│   └── segments.png
│
└── README.md
```

---

## 🚀 API Endpoints

| Method | Endpoint                          | Description           |
| ------ | --------------------------------- | --------------------- |
| POST   | `/api/v1/auth/login`              | User authentication   |
| POST   | `/api/v1/auth/register`           | Merchant registration |
| GET    | `/api/v1/auth/me`                 | Current user          |
| GET    | `/api/v1/analytics/dashboard`     | Executive dashboard   |
| GET    | `/api/v1/analytics/revenue-leaks` | Revenue leak insights |
| GET    | `/api/v1/analytics/segments`      | Customer segmentation |
| POST   | `/api/v1/chat/messages`           | AI business chat      |
| POST   | `/api/v1/campaigns/generate`      | Generate campaigns    |

Interactive Swagger documentation is available at:

**https://merchantgpt-api.onrender.com/docs**

---

## 🔒 Authentication

MerchantGPT uses **JWT Bearer Authentication**.

After login, the frontend securely stores the access token and automatically authenticates all protected API requests.

---

## 👨‍💻 Author

**Manish Kumar Reddy**

Full Stack AI Developer

* GitHub: https://github.com/Manish-kumar-reddy
* Live Project: https://merchant-gpt.vercel.app

---

## ⭐ Support

If you found MerchantGPT interesting, consider giving this repository a **Star ⭐**. It helps the project reach more developers and recruiters.
