# 📅 AI Email & Meeting Booking Agent

An automated LangGraph agent that processes incoming emails, classifies requests, verifies meeting schedules via [Cal.com](https://cal.com), extracts dates and times using LLMs, and sends automated replies or escalations.

---

## 🏗️ Project Architecture & Structure

```
├── api/
│   └── index.py            # Vercel Serverless Function entry point
├── cal_availability.py     # Slot availability verification & Cal.com API integration
├── cal_booking.py          # Cal.com booking workflow
├── classify_email.py       # Email classification & intent detection (Google Gemini)
├── main.py                 # Persistent IMAP IDLE daemon (for local / VPS execution)
├── read_email.py           # Email reader & parser (IMAP)
├── send_email.py           # Email sender & responder (SMTP)
├── state.py                # Pydantic state schemas (EmailAgentState, MeetingAgentState)
├── workflow.py             # Compiled LangGraph workflow
├── requirements.txt        # Python package dependencies
├── vercel.json             # Vercel deployment & routing configuration
├── .env.example            # Sample environment variables template
├── .gitignore              # Ignored files (secrets, venv, pycache, .vercel)
└── README.md               # Documentation and deployment guide
```

---

## ⚡ Deployment on Vercel

Vercel operates on an **event-driven Serverless Architecture**. 

> 💡 **Important Architectural Note:**
> - [main.py](file:///e:/AI/Booking%20Agent/main.py) uses a persistent socket connection (`IMAPClient.idle()`) which waits indefinitely for incoming push notifications. **Serverless environments (like Vercel) terminate after request execution (10–60s max execution time).**
> - On Vercel, the agent runs via the Serverless function [api/index.py](file:///e:/AI/Booking%20Agent/api/index.py), triggered via **HTTP POST / GET** requests or **Vercel Cron Jobs** (e.g., checking email every 5–15 minutes).
> - If you require persistent 24/7 IMAP IDLE push sockets, run `python main.py` on a long-running instance (like a VPS, Docker container, Railway, or Render), or use an email webhook (e.g., SendGrid, Postmark, Mailgun) pointed to your Vercel endpoint.

---

### Step 1: Push Project to GitHub

Ensure your project is committed to a GitHub repository:

```bash
git add .
git commit -m "Configure project for Vercel deployment"
git push origin main
```

---

### Step 2: Deploy to Vercel

#### Option A: Via Vercel Web Dashboard (Recommended)

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard) and click **"Add New Project"**.
2. Select your GitHub repository.
3. Keep **Framework Preset** as **Other**.
4. Set the Root Directory as `./`.
5. Under **Environment Variables**, add the required environment variables (see below).
6. Click **Deploy**.

#### Option B: Via Vercel CLI

```bash
# 1. Install Vercel CLI (if not already installed)
npm install -g vercel

# 2. Log in and deploy
vercel login
vercel

# 3. Deploy to production
vercel --prod
```

---

### Step 3: Configure Environment Variables in Vercel

Go to your Vercel Project Settings -> **Environment Variables**, and add:

| Key | Description | Example |
| :--- | :--- | :--- |
| `EMAIL_ID_1` | IMAP & SMTP Email Account | `agent@yourdomain.com` |
| `EMAIL_PASSWORD_1` | Email or App Password | `your-secure-app-password` |
| `IMAP_SERVER` | Incoming IMAP Server | `outlook.office365.com` / `imap.gmail.com` |
| `INCOMING_PORT` | IMAP Port | `993` |
| `OUTGOING_SMTP_SERVER`| Outgoing SMTP Host | `smtp.office365.com` / `smtp.gmail.com` |
| `OUTGOING_PORT` | SMTP Port | `587` |
| `ESCALATION_EMAIL` | Admin email for escalations | `manager@yourdomain.com` |
| `REPLIED_BY` | Sign-off Name | `Allied Consultant Team` |
| `GOOGLE_API_KEY` | Google Gemini API Key | `AIzaSy...` |
| `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |
| `HF_TOKEN` | Hugging Face Access Token | `hf_...` |
| `CAL_API_KEY` | Cal.com API v2 Key | `cal_live_...` |
| `CAL_EVENT_TYPE_ID` | Event Type ID from Cal.com | `123456` |
| `CAL_USER_EMAIL` | Cal.com User Account Email | `booking@yourdomain.com` |
| `DAYS_FORWARD` | Booking Window (days) | `14` |
| `CRON_SECRET` | Secret token to secure triggers | `custom-random-secret` |

---

### Step 4: Triggering the Agent on Vercel

#### 1. Health Check
```bash
curl -X GET https://your-project.vercel.app/api/index
```

#### 2. Triggering Email Check & Processing
```bash
curl -X POST https://your-project.vercel.app/api/index \
  -H "Authorization: Bearer your-random-secret" \
  -H "Content-Type: application/json"
```

#### 3. Automatic Polling with Vercel Cron (Optional)
To have Vercel automatically check unread emails periodically, add a `crons` block inside [vercel.json](file:///e:/AI/Booking%20Agent/vercel.json):

```json
{
  "version": 2,
  "crons": [
    {
      "path": "/api/index",
      "schedule": "*/10 * * * *"
    }
  ],
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index.py" },
    { "source": "/", "destination": "/api/index.py" }
  ]
}
```

---

## 💻 Local Development

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in your credentials:
   ```bash
   cp .env.example .env
   ```

4. Run locally:
   - **Real-time IMAP push daemon:**
     ```bash
     python main.py
     ```
   - **Single run of LangGraph workflow:**
     ```bash
     python workflow.py
     ```
