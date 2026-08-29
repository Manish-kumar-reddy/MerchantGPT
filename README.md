# MerchantGPT 🚀

> Autonomous AI Growth Manager for E-commerce Merchants

MerchantGPT is a production-grade AI SaaS platform that analyzes merchant sales, refunds, abandoned carts, customer behavior, and revenue trends, then generates actionable growth recommendations using Gemini AI, PostgreSQL analytics, and FastAPI.

---

## ✨ Features

- 🤖 AI Chat with SQL Tool Calling
- 📊 Merchant Analytics Dashboard
- 💸 Revenue Leak Detection
- 🛒 Abandoned Cart Recovery
- 👥 Customer Segmentation (RFM)
- ⚠️ Churn Prediction
- 📣 AI Marketing Campaign Generator
- 📈 Weekly Executive AI Report
- 🔐 JWT Authentication
- 🧠 Chat Memory with pgvector

---

## Tech Stack

### Frontend
- Next.js 15
- TypeScript
- Tailwind CSS
- Recharts

### Backend
- FastAPI
- PostgreSQL
- SQLAlchemy
- pgvector

### AI
- Gemini 3.6 Flash
- Tool Calling
- Vector Memory

---

## Demo Credentials

**Email**

demo@aurorahome.example

**Password**

Demo@12345

---

## Local Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## AI Workflow

1. User asks a business question.
2. Gemini decides which SQL tool to call.
3. FastAPI executes analytical queries.
4. PostgreSQL returns merchant data.
5. Gemini generates an executive-quality answer.

---

## Testing

```bash
pytest
```

**37/37 tests passing ✅**

---

## Author

**Manish Kumar Reddy**

Built for the Razorpay AI Builder Internship 2026.