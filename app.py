import os
import json
import time
from datetime import datetime, date
from typing import Dict, Any, Optional
import streamlit as st
from dotenv import load_dotenv

# Page configuration
st.set_page_config(
    page_title="AI Email & Booking Agent",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for modern look
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(120deg, #2563EB, #7C3AED, #DB2777);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-blue { background-color: #DBEAFE; color: #1E40AF; }
    .badge-green { background-color: #DCFCE7; color: #166534; }
    .badge-amber { background-color: #FEF3C7; color: #92400E; }
    .badge-red { background-color: #FEE2E2; color: #991B1B; }
    .badge-purple { background-color: #F3E8FF; color: #6B21A8; }
</style>
""", unsafe_allow_html=True)

# Load existing environment
load_dotenv(override=True)

# ----------------- SIDEBAR: CONFIGURATION & CREDENTIALS -----------------
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/calendar-plus.png", width=64)
    st.markdown("### ⚙️ System Settings & Keys")
    st.caption("Manage connection keys and agent environment.")

    # Status check
    env_keys = {
        "GOOGLE_API_KEY": os.getenv("GOOGLE_API_KEY", ""),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "HF_TOKEN": os.getenv("HF_TOKEN", ""),
        "CAL_API_KEY": os.getenv("CAL_API_KEY", ""),
        "CAL_EVENT_TYPE_ID": os.getenv("CAL_EVENT_TYPE_ID", "0"),
        "EMAIL_ID_1": os.getenv("EMAIL_ID_1", ""),
        "EMAIL_PASSWORD_1": os.getenv("EMAIL_PASSWORD_1", ""),
        "IMAP_SERVER": os.getenv("IMAP_SERVER", "outlook.office365.com"),
        "OUTGOING_SMTP_SERVER": os.getenv("OUTGOING_SMTP_SERVER", "smtp.office365.com"),
        "OUTGOING_PORT": os.getenv("OUTGOING_PORT", "587"),
        "ESCALATION_EMAIL": os.getenv("ESCALATION_EMAIL", ""),
        "REPLIED_BY": os.getenv("REPLIED_BY", "AI Booking Assistant")
    }

    configured_count = sum(1 for k, v in env_keys.items() if v and v != "0")
    total_count = len(env_keys)
    st.progress(configured_count / total_count, text=f"{configured_count}/{total_count} Env Variables Configured")

    with st.expander("🔑 Edit Credentials (.env)", expanded=False):
        google_api = st.text_input("Google API Key", value=env_keys["GOOGLE_API_KEY"], type="password")
        openai_api = st.text_input("OpenAI API Key", value=env_keys["OPENAI_API_KEY"], type="password")
        hf_token = st.text_input("HuggingFace Token", value=env_keys["HF_TOKEN"], type="password")
        cal_key = st.text_input("Cal.com API Key", value=env_keys["CAL_API_KEY"], type="password")
        cal_event = st.text_input("Cal.com Event Type ID", value=env_keys["CAL_EVENT_TYPE_ID"])
        email_user = st.text_input("Email Account", value=env_keys["EMAIL_ID_1"])
        email_pass = st.text_input("Email Password / App Secret", value=env_keys["EMAIL_PASSWORD_1"], type="password")
        imap_serv = st.text_input("IMAP Server", value=env_keys["IMAP_SERVER"])
        smtp_serv = st.text_input("SMTP Server", value=env_keys["OUTGOING_SMTP_SERVER"])
        smtp_port = st.text_input("SMTP Port", value=env_keys["OUTGOING_PORT"])
        escalation_to = st.text_input("Escalation Email", value=env_keys["ESCALATION_EMAIL"])
        replied_by = st.text_input("Replied By Name", value=env_keys["REPLIED_BY"])

        if st.button("💾 Save Environment (.env)", use_container_width=True):
            env_content = f"""# Autonomous Email & Booking Agent Environment
GOOGLE_API_KEY={google_api}
OPENAI_API_KEY={openai_api}
HF_TOKEN={hf_token}
CAL_API_KEY={cal_key}
CAL_EVENT_TYPE_ID={cal_event}
EMAIL_ID_1={email_user}
EMAIL_PASSWORD_1={email_pass}
IMAP_SERVER={imap_serv}
OUTGOING_SMTP_SERVER={smtp_serv}
OUTGOING_PORT={smtp_port}
ESCALATION_EMAIL={escalation_to}
REPLIED_BY={replied_by}
INCOMING_PORT=993
DAYS_FORWARD=14
"""
            with open(".env", "w", encoding="utf-8") as f:
                f.write(env_content)
            load_dotenv(override=True)
            st.success("✅ Saved to .env successfully! Reloading...")
            st.rerun()

    st.divider()
    st.markdown("### 📊 Workflow Architecture")
    st.caption("LangGraph State Machine Pipeline:")
    st.code("""
START ──► [Read Unseen Email]
                │
                ▼
        [Classify (Gemini)]
                │
                ▼
        [Reply & Escalate]
                │
                ├── Meeting-request?
                │       │
                │       ▼
                │   [Extract Time (LLM)]
                │       │
                │       ▼
                │   [Verify/Suggest Slots]
                │       │
                │   Confirmed?
                │   ├── Yes ──► [Book via Cal.com]
                │   └── No  ──► [Email Suggested Slots]
                │
                └── Other/Spam ──► END
""", language="text")

# ----------------- MAIN UI TABS -----------------
st.markdown('<div class="main-header">📅 Autonomous Email & Meeting Booking Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">LangGraph agent for automated inbox monitoring, intent classification, calendar availability check, auto-booking, and smart replies.</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 Interactive Simulator",
    "📬 Live Email Fetcher & Runner",
    "🗓️ Cal.com Slot Inspector",
    "🧠 Classifier & Urgency Tester",
    "ℹ️ Architecture & Health"
])

# Lazy imports for stability
def get_workflow_app():
    try:
        from workflow import app
        return app, None
    except Exception as e:
        return None, str(e)

# ----------------- TAB 1: INTERACTIVE SIMULATOR -----------------
with tab1:
    st.markdown("### 🧪 Test the Full Pipeline (Without Touching Live Inbox)")
    st.caption("Simulate an incoming email and watch the agent classify, check availability, formulate responses, or trigger Cal.com bookings.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("#### 📝 Incoming Email Payload")
        sample_choice = st.selectbox(
            "Load Sample Scenario:",
            [
                "Custom Email Input",
                "Meeting Request (Specific Date & Time)",
                "Meeting Request (General Availability)",
                "Fresh Enquiry (Product / Pricing Question)",
                "Security Threat / Phishing Attempt",
                "Spam / Promotional Pitch",
                "Informative Update"
            ]
        )

        samples = {
            "Meeting Request (Specific Date & Time)": {
                "subject": "Discussion on AI Agent deployment - Tomorrow 3 PM",
                "sender": "client.sarah@acme-corp.com",
                "body": "Hi team,\n\nWe would like to book a 30-minute discussion regarding your AI Booking Agent. Can we meet on 2026-10-15 at 15:00:00 (Asia/Kolkata)?\n\nThanks,\nSarah",
                "auth": "spf=pass dkim=pass dmarc=pass"
            },
            "Meeting Request (General Availability)": {
                "subject": "Request for demo call next week",
                "sender": "david.miller@enterprise.io",
                "body": "Hello,\nCould you please share your available slots for a quick introductory call sometime next week? Thanks!\nDavid",
                "auth": "spf=pass dkim=pass dmarc=pass"
            },
            "Fresh Enquiry (Product / Pricing Question)": {
                "subject": "Inquiry about pricing plans",
                "sender": "inquiries@startuptech.com",
                "body": "Hi Allied Consultant team,\nCould you provide a quote for integrating your booking agent into our CRM? How does your pricing model work?\n\nBest,\nMark",
                "auth": "spf=pass dkim=pass dmarc=pass"
            },
            "Security Threat / Phishing Attempt": {
                "subject": "URGENT: Verify your bank account credentials immediately",
                "sender": "security-alert@suspicious-domain-fake.xyz",
                "body": "Your bank account has been locked. Click here immediately to input your password and wire 5000 USD to prevent account suspension.",
                "auth": "spf=fail dkim=fail dmarc=fail"
            },
            "Spam / Promotional Pitch": {
                "subject": "Grow your SEO traffic 10x with our automated backlinks",
                "sender": "sales@bulkseo-blast.org",
                "body": "Hey there! We sell high quality SEO guest posts for just $20 each. Reply YES to get our catalog.",
                "auth": "spf=neutral dkim=none"
            },
            "Informative Update": {
                "subject": "Product Release Notes - Version 3.4",
                "sender": "newsletter@technews.com",
                "body": "Here are the updates for Version 3.4 including minor bug fixes, performance improvements, and dark mode tweaks.",
                "auth": "spf=pass"
            }
        }

        preset = samples.get(sample_choice, {})

        sim_sender = st.text_input("Sender Email", value=preset.get("sender", "user@example.com"))
        sim_subject = st.text_input("Email Subject", value=preset.get("subject", "Meeting regarding project"))
        sim_auth = st.text_input("Auth Status / SPF / DKIM", value=preset.get("auth", "spf=pass dkim=pass"))
        sim_body = st.text_area("Email Body", value=preset.get("body", "Hi, can we meet next Friday at 2 PM IST?"), height=180)

        # Simulation Mode selector
        dry_run = st.checkbox("Dry Run Mode (Simulate without sending real emails / booking live Cal)", value=True,
                              help="When enabled, tests all nodes, classification, slot extraction, but skips actual SMTP dispatch or Cal.com mutation.")

    with col2:
        st.markdown("#### ⚡ Pipeline Execution Output")
        run_sim = st.button("🚀 Run Simulation Through Workflow", type="primary", use_container_width=True)

        if run_sim:
            with st.spinner("Processing through LangGraph pipeline..."):
                try:
                    from state import MeetingAgentState
                    
                    test_state = MeetingAgentState(
                        subject=sim_subject,
                        body=sim_body,
                        sender_emailid=sim_sender,
                        auth_status=sim_auth,
                        original_message_id=f"<sim-{int(time.time())}@booking-agent.local>"
                    )

                    steps_output = []

                    # Step 1: Classification
                    st.write("**1️⃣ Running Classifier Node (`classify_email_node_llm`)**")
                    if os.getenv("GOOGLE_API_KEY"):
                        from classify_email import classify_email_node_llm
                        class_result = classify_email_node_llm(test_state)
                        test_state.classification = class_result.get("classification")
                        test_state.urgency = class_result.get("urgency")
                        test_state.topic = class_result.get("topic")
                        test_state.summary = class_result.get("summary")
                    else:
                        st.warning("⚠️ No GOOGLE_API_KEY detected in .env. Mocking classification for demo.")
                        if "meeting" in sim_subject.lower() or "meet" in sim_body.lower():
                            test_state.classification = "Meeting-request"
                            test_state.urgency = "high"
                        elif "urgent" in sim_subject.lower() or "suspicious" in sim_sender:
                            test_state.classification = "Threat"
                            test_state.urgency = "critical"
                        else:
                            test_state.classification = "Fresh-enquiry"
                            test_state.urgency = "medium"
                        test_state.topic = sim_subject
                        test_state.summary = sim_body[:100]

                    # Display classification badges
                    badge_color = {
                        "Meeting-request": "badge-blue",
                        "Threat": "badge-red",
                        "Spam": "badge-amber",
                        "Fresh-enquiry": "badge-purple",
                        "Informative": "badge-green"
                    }.get(test_state.classification, "badge-blue")

                    st.markdown(f"""
                    <div style="margin: 10px 0;">
                        <span class="badge {badge_color}">Category: {test_state.classification}</span>
                        <span class="badge badge-amber">Urgency: {test_state.urgency}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.json({
                        "classification": test_state.classification,
                        "urgency": test_state.urgency,
                        "topic": test_state.topic,
                        "summary": test_state.summary
                    })

                    # Step 2: Auto-reply / Escalation Preview
                    st.write("**2️⃣ Reply & Escalation Decision Node (`reply_and_escalate_node`)**")
                    if test_state.classification in ['Fresh-enquiry', 'Other']:
                        st.info("📨 Auto-reply will be generated and dispatched to sender.")
                    if test_state.urgency in ["high", "critical"] or test_state.classification in ['Threat', 'Fresh-enquiry']:
                        st.error(f"🚨 Email qualifies for ESCALATION to admin ({os.getenv('ESCALATION_EMAIL', 'admin@example.com')}).")

                    # Step 3: Meeting Time Extraction
                    if test_state.classification == "Meeting-request":
                        st.write("**3️⃣ Extracting Meeting Time (`meeting_time`)**")
                        try:
                            from cal_availability import meeting_time
                            meeting_time(test_state)
                            st.success(f"Extracted Date: `{test_state.preferred_date}` | Time: `{test_state.preferred_time}` | Timezone: `{test_state.client_timezone}`")
                        except Exception as e:
                            st.warning(f"Local Hugging Face extraction skipped or raised: {e}")
                            st.info("Using standard regex/fallback extraction for demo.")
                            test_state.preferred_date = "2026-10-15"
                            test_state.preferred_time = "15:00:00"
                            test_state.client_timezone = "Asia/Kolkata"

                        # Step 4: Cal.com Slot verification
                        st.write("**4️⃣ Checking Calendar Availability (`verify_or_suggest_slots_node`)**")
                        if os.getenv("CAL_API_KEY") and not dry_run:
                            try:
                                from cal_availability import verify_or_suggest_slots_node
                                verify_or_suggest_slots_node(test_state)
                                st.write("Confirmed Slot:", test_state.confirmed_slot)
                                st.write("Suggested Slots:", test_state.suggested_slots)
                            except Exception as ce:
                                st.error(f"Cal.com check error: {ce}")
                        else:
                            st.info("ℹ️ Dry-run mode: Mocking Cal.com availability response.")
                            test_state.booking_status = "SLOT_CONFIRMED"
                            test_state.confirmed_slot = f"{test_state.preferred_date}T{test_state.preferred_time}+05:30"
                            st.success(f"Slot confirmed: {test_state.confirmed_slot}")

                        # Step 5: Booking
                        if test_state.confirmed_slot:
                            st.write("**5️⃣ Booking Node (`book_meeting_node`)**")
                            if dry_run:
                                st.success("✅ [DRY RUN] Would book via Cal.com API v2 for attendee.")
                                test_state.booking_status = "SUCCESS"
                                test_state.booking_url = "https://app.cal.com/booking/simulated-12345"
                            else:
                                from cal_booking import book_meeting_node
                                res = book_meeting_node(test_state)
                                st.json(res)
                    else:
                        st.write("⏹️ Not a meeting request: Pipeline completes after notification/escalation.")

                    st.success("🎉 Simulation run complete!")

                except Exception as ex:
                    st.error(f"Execution Error: {ex}")

# ----------------- TAB 2: LIVE EMAIL FETCHER & RUNNER -----------------
with tab2:
    st.markdown("### 📬 Live Inbox Execution")
    st.caption("Inspect live unread emails from your configured IMAP server and trigger the LangGraph workflow on real incoming messages.")

    imap_col1, imap_col2 = st.columns([1, 1])

    with imap_col1:
        st.markdown("#### IMAP Connection Status")
        st.write(f"**Server:** `{os.getenv('IMAP_SERVER')}`")
        st.write(f"**Account:** `{os.getenv('EMAIL_ID_1')}`")
        st.write(f"**Password Configured:** `{'Yes (masked)' if os.getenv('EMAIL_PASSWORD_1') else 'No'}`")

        email_filter_mode = st.radio(
            "Fetch Filter:",
            ["Unread (UNSEEN) First, fallback to latest", "Latest Unread (UNSEEN) Only", "Latest Email (ALL)"],
            help="Choose whether to search for unread emails only or test with the latest email in the inbox."
        )

        check_btn = st.button("🔍 Check & Fetch Live Email", use_container_width=True)

    with imap_col2:
        st.markdown("#### Workflow Execution")
        st.caption("Triggers the full LangGraph agent workflow (`read_email` ➔ `classify_email` ➔ `reply/escalate` ➔ `slot check/booking`).")
        run_full_btn = st.button("🚀 Run Full Workflow on Live Email", type="primary", use_container_width=True)

    if check_btn:
        with st.spinner("Connecting to IMAP server & fetching email..."):
            try:
                import imaplib
                from state import MeetingAgentState
                from read_email import read_latest_email

                blank_state = MeetingAgentState()
                email_data = read_latest_email(blank_state)

                if email_data and email_data.get("subject"):
                    st.success("✅ Email successfully fetched!")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Subject:** {email_data.get('subject')}")
                        st.markdown(f"**From:** `{email_data.get('sender_emailid')}`")
                    with c2:
                        st.markdown(f"**Authentication:** `{email_data.get('auth_status', 'N/A')}`")
                        st.markdown(f"**Message-ID:** `{email_data.get('original_message_id', 'N/A')}`")

                    with st.expander("📄 View Email Body", expanded=True):
                        st.text(email_data.get("body", "(Empty body)"))
                else:
                    st.warning("⚠️ No matching emails found in the inbox.")
            except Exception as e:
                st.error(f"Failed to fetch live email: {e}")

    if run_full_btn:
        with st.spinner("Executing full LangGraph agent workflow..."):
            try:
                from workflow import app
                from state import MeetingAgentState

                initial_state = MeetingAgentState()
                result = app.invoke(initial_state)

                res_dict = result.dict() if hasattr(result, "dict") else dict(result)
                
                if not res_dict.get("subject") and not res_dict.get("body"):
                    st.warning("⚠️ No unread emails were found. Pipeline exited early at `route_after_reading`.")
                else:
                    st.success("🏁 Workflow execution finished!")

                    # Show summary cards
                    m1, m2, m3 = st.columns(3)
                    with m1:
                        st.metric("Classification", res_dict.get("classification") or "N/A")
                    with m2:
                        st.metric("Urgency", (res_dict.get("urgency") or "N/A").upper())
                    with m3:
                        st.metric("Booking Status", res_dict.get("booking_status") or "N/A")

                    st.markdown("#### Full Execution State Result:")
                    st.json(res_dict)
            except Exception as e:
                st.error(f"Workflow execution encountered an error: {e}")

# ----------------- TAB 3: CAL.COM SLOT INSPECTOR -----------------
with tab3:
    st.markdown("### 🗓️ Cal.com Availability & Slot Inspector")
    st.caption("Directly test the Cal.com API v2 integration to inspect real open slots for your event type.")

    cal_col1, cal_col2 = st.columns([1, 1])

    with cal_col1:
        c_api = st.text_input("Cal API Key", value=os.getenv("CAL_API_KEY", ""), type="password", key="cal_tab_key")
        c_event = st.text_input("Event Type ID", value=os.getenv("CAL_EVENT_TYPE_ID", "0"), key="cal_tab_event")
        c_days = st.slider("Days Forward Search Window", min_value=1, max_value=30, value=int(os.getenv("DAYS_FORWARD", 14)))
        c_tz = st.selectbox("Client Timezone", ["Asia/Kolkata", "UTC", "America/New_York", "Europe/London", "Asia/Dubai"])

        fetch_slots_btn = st.button("🔎 Fetch Open Slots", use_container_width=True)

    with cal_col2:
        st.markdown("#### Available Calendar Slots")
        if fetch_slots_btn:
            if not c_api:
                st.error("Please provide a valid Cal.com API key.")
            else:
                with st.spinner("Fetching available slots from Cal.com API v2..."):
                    try:
                        import requests
                        from datetime import datetime, timezone, timedelta

                        now = datetime.now(timezone.utc)
                        url = "https://api.cal.com/v2/slots/available"
                        params = {
                            "eventTypeId": int(c_event),
                            "startTime": now.strftime("%Y-%m-%dT00:00:00Z"),
                            "endTime": (now + timedelta(days=c_days)).strftime("%Y-%m-%dT23:59:59Z"),
                            "timeZone": c_tz
                        }
                        headers = {
                            "Authorization": f"Bearer {c_api}",
                            "cal-api-version": "2024-08-13"
                        }
                        resp = requests.get(url, params=params, headers=headers, timeout=10)

                        if resp.status_code == 200:
                            data = resp.json()
                            slots_map = data.get("data", {}).get("slots", {})
                            raw_timestamps = [s["time"] for day_slots in slots_map.values() for s in day_slots if "time" in s]
                            
                            st.success(f"Found {len(raw_timestamps)} open time slots!")
                            if raw_timestamps:
                                st.dataframe([{"Slot (UTC)": s} for s in raw_timestamps[:25]], use_container_width=True)
                            else:
                                st.info("No open slots found for this event in the selected time range.")
                        else:
                            st.error(f"Cal.com Error {resp.status_code}: {resp.text}")
                    except Exception as ce:
                        st.error(f"Failed to communicate with Cal.com: {ce}")

# ----------------- TAB 4: CLASSIFIER & URGENCY TESTER -----------------
with tab4:
    st.markdown("### 🧠 Email Intent Classifier & Urgency Test")
    st.caption("Evaluate Gemini's structured classification output on any arbitrary text or customer message.")

    test_input = st.text_area(
        "Raw Email or Inbound Message Text:",
        value="Subject: Immediate payment needed for invoice #9821\n\nDear sir, our bank details have changed. Please wire payment immediately to avoid legal consequences.",
        height=140
    )

    if st.button("🧪 Classify Email", type="primary"):
        with st.spinner("Running Gemini classification..."):
            try:
                from state import EmailAgentState
                from classify_email import classify_email_node_llm

                state_obj = EmailAgentState(
                    subject="Email Subject Test",
                    body=test_input,
                    sender_emailid="test@domain.com",
                    auth_status="Not Available"
                )

                res = classify_email_node_llm(state_obj)
                st.write("### Result")
                st.json(res)
            except Exception as e:
                st.error(f"Classification failed: {e}")

# ----------------- TAB 5: ARCHITECTURE & HEALTH -----------------
with tab5:
    st.markdown("### ℹ️ Agent Architecture & Diagnostics")

    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.markdown("#### 📦 System Components")
        st.markdown("""
        - **LangGraph**: Directed cyclic/acyclic graph orchestrator (`workflow.py`).
        - **Google Gemini**: Structured JSON output for classification (`classify_email.py`).
        - **Hugging Face (`Qwen2.5-7B-Instruct`)**: Natural language date & time parsing (`cal_availability.py`).
        - **Cal.com API v2**: Real-time slot availability check & booking confirmation (`cal_booking.py`).
        - **IMAP / SMTP**: Microsoft 365 / Gmail / Custom email sync (`read_email.py`, `send_email.py`).
        - **Serverless API**: Vercel-ready handler for webhook / cron triggers (`api/index.py`).
        """)

    with col_b:
        st.markdown("#### 🩺 Environment Health Check")
        checks = [
            ("Google API Key", bool(os.getenv("GOOGLE_API_KEY"))),
            ("OpenAI API Key", bool(os.getenv("OPENAI_API_KEY"))),
            ("Cal.com API Key", bool(os.getenv("CAL_API_KEY"))),
            ("Cal.com Event ID", bool(os.getenv("CAL_EVENT_TYPE_ID") and os.getenv("CAL_EVENT_TYPE_ID") != "0")),
            ("Email Login", bool(os.getenv("EMAIL_ID_1"))),
            ("Email Password", bool(os.getenv("EMAIL_PASSWORD_1"))),
            ("Escalation Email", bool(os.getenv("ESCALATION_EMAIL"))),
        ]

        for name, status in checks:
            if status:
                st.markdown(f"✅ **{name}:** Configured")
            else:
                st.markdown(f"❌ **{name}:** Missing or Not Configured")
