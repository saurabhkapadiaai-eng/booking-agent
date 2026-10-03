# %% [markdown]
# > - **Input:**
#     - 1. we may get date and time directly from client to book meeting or 
#     - 2. client may ask us for available slot.
# > - **Objective: we need to check available schedule for meeting from cal.com.**
#     - 1. if meeting slot (date & time) is provided and available we should confirm the availability for the given slot
#     - 2. if meeting slot(Date and time) is not provided or if the provided meeting slot is not available, we should suggest next three available slots. write a code for the same.

# %% [markdown]
# ## **Done Code**

# %%
import os
import time
import requests
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from typing import TypedDict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

from state import MeetingAgentState

from datetime import datetime, date, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field, field_validator
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()
CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_EVENT_TYPE_ID = int(os.getenv("CAL_EVENT_TYPE_ID", "0"))
DAYS_FORWARD = int(os.getenv('DAYS_FORWARD', 14))

# %%
class ExtractedDateTime(BaseModel):
    """
    Schema for extracting a scheduled date, time, and timezone from natural language.
    """
    event_date: date = Field(..., description="The calendar date of the event in YYYY-MM-DD format (e.g., '2026-07-24').")
    event_time: time = Field(..., description="The local time of the event using the 24-hour clock in HH:MM:SS or HH:MM format (e.g., '14:30:00' for 2:30 PM)."    )    
    timezone: str = Field(..., description=(
            "The official IANA time zone name in 'Region/City' format. "
            "Examples: 'Asia/Kolkata', 'America/New_York', 'Europe/London', 'Pacific/Honolulu'. "
            "NEVER use abbreviations like EST, PST, IST, or CET. "
            "If the location is India, use 'Asia/Kolkata'."
            )
        )

    @field_validator("timezone")
    @classmethod
    def validate_iana_timezone(cls, value: str) -> str:
        # Common LLM spelling correction: Kolkata is often misspelled with two T's
        if value.lower() == "asia/kolkatta":
            value = "Asia/Kolkata"
            
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise ValueError(f"'{value}' is not a valid IANA timezone name. Must be format like 'America/New_York' or 'Asia/Kolkata'.")
        
        return value

    def to_aware_datetime(self) -> datetime:
        """Helper method to combine the fields into a real Python timezone-aware datetime."""
        tz = ZoneInfo(self.timezone)
        return datetime.combine(self.event_date, self.event_time, tzinfo=tz)

from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from transformers import pipeline, set_seed

from transformers import set_seed
set_seed(42)
generator = pipeline('text-generation', model='Qwen/Qwen2.5-7B-Instruct', return_full_text=False)

llm = HuggingFacePipeline(pipeline=generator)
chat_model = ChatHuggingFace(llm=llm)
structured_llm_HF = chat_model.with_structured_output(ExtractedDateTime, method="json_mode")

def meeting_time(state: MeetingAgentState) -> MeetingAgentState:
    """I read email text and extract the preferred date, time, and timezone using a structured LLM."""

    input = state.body

    prompt = ChatPromptTemplate.from_messages([
        ("system", """
        Extract the date, time, and timezone. Assume today is {today} unless specified otherwise.
        
        You are a strict data extraction API. You MUST return exactly one valid JSON object and absolutely nothing else.
        Do NOT wrap the JSON in markdown blocks (like ```json).
        Do NOT include any conversational text, greetings, or explanations.
        You will check current and the previous email if available. And then, you will conculde the preferred slot for meeting.
        If the email does not specify a timezone, first you can check the previous email to check the timezone inofrmation.
        If there is no previous email or there is no mention of any timezone in previous email, return the Asia/Kolkata timezone.
        
        Required JSON format:
        {{
            "event_date": "YYYY-MM-DD",
            "event_time": "HH:MM:SS",
            "timezone": "Region/City"
        }}"""),
        ("human", "{input}")
    ])

    # 5. Connect the prompt to the structured LLM
    chain = prompt | structured_llm_HF

    # 6. NOW you call .invoke()!
    result = chain.invoke({
        "today": date.today().isoformat(),
        "input": input
    })

    state.preferred_date = result['event_date']
    state.preferred_time = result['event_time']
    state.client_timezone = result['timezone']
    
    return state

# %%
def create_rugged_session() -> requests.Session:
    """Creates an HTTP session that auto-retries on network drops or API rate limits."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,  # Wait 0.5s, then 1s, then 2s
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

def fetch_calcom_slots(state: MeetingAgentState) -> List[datetime]:
    """Fetches upcoming slots cleanly with short timeouts and auto-retries."""

    meeting_time(state)  # Ensure the state has preferred_date, preferred_time, and client_timezone set
    
    time_zone = state.client_timezone

    if state.preferred_date:
        # If the user requested a specific date, start the 14-day search window from that date
        pref_date_str = str(state.preferred_date).strip()
        now = datetime.strptime(pref_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        # Otherwise, default to searching from today
        now = datetime.now(timezone.utc)

    url = "https://api.cal.com/v2/slots/available"
    params = {
        "eventTypeId": CAL_EVENT_TYPE_ID,
        "startTime": now.strftime("%Y-%m-%dT00:00:00Z"),
        "endTime": (now + timedelta(days=DAYS_FORWARD)).strftime("%Y-%m-%dT23:59:59Z"),
        "timeZone": time_zone
    }
    headers = {"Authorization": f"Bearer {CAL_API_KEY}", "cal-api-version": "2024-08-13"}

    session = create_rugged_session()
    try:
        # Use a tight 6-second timeout; if it stalls, the retry adapter kicks in automatically
        response = session.get(url, params=params, headers=headers, timeout=6)
        if response.status_code != 200:
            return []

        slots_map = response.json().get("data", {}).get("slots", {})
        
        # Extract all UTC timestamp strings cleanly into a flat list
        raw_timestamps = [
            slot["time"] for day_slots in slots_map.values() for slot in day_slots if "time" in slot
        ]
        
        # Parse to datetime objects and sort chronologically
        datetimes = [datetime.fromisoformat(ts.replace("Z", "+00:00")) for ts in raw_timestamps]
        return sorted(datetimes)

    except Exception as e:
        print(f"[Network Error] Could not reach Cal.com: {e}")
        return []
    finally:
        session.close()

def verify_or_suggest_slots_node(state: MeetingAgentState) -> MeetingAgentState:
    """Core LangGraph Node: Confirms requested slot or returns top 3 available alternatives."""
    
    client_tz_str = state.client_timezone
    pref_date = state.preferred_date
    pref_time = state.preferred_time
    print(f'{pref_date} /t {pref_time}')

    client_tz = ZoneInfo(str(client_tz_str).strip())  # Ensure valid IANA timezone

    available_slots = fetch_calcom_slots(state)
    available_slots.sort()  # Ensure chronological order

    print(f"Available Solts are:\n\n{[s.astimezone(client_tz).isoformat() for s in available_slots]}\n")
    
    if not available_slots:
        state.booking_status = "NO_SLOTS_AVAILABLE"
        state.suggested_slots = []
        state.error_message = "No open time slots found over the next 14 days."
        return state

    # Scenario 1: Client provided Date & Time -> Try to Confirm
    if pref_date and pref_time:
        
        clean_date = str(pref_date).strip()  # Ensure "YYYY-MM-DD" format
        clean_time = str(pref_time).strip()[:5]  # Ensure "HH:MM" format

        target_local_prefix = f"{clean_date}T{clean_time}"

        client_tz = ZoneInfo(str(client_tz_str).strip())

        for slot_utc in available_slots:

            local_slot_iso = slot_utc.astimezone(client_tz).isoformat()

            # Convert UTC slot to client's local timezone for accurate matching
            if target_local_prefix in local_slot_iso:
                state.booking_status = "SLOT_CONFIRMED"
                state.confirmed_slot = local_slot_iso #slot_utc.astimezone(client_tz).isoformat()
                state.suggested_slots = []
                state.error_message = None
                return state
                break

        # If requested slot wasn't found, fall back to alternatives
        state.booking_status = "SLOT_UNAVAILABLE_SUGGESTING_ALTERNATIVES"
        state.confirmed_slot = None
        state.suggested_slots = [s.astimezone(client_tz).isoformat() for s in available_slots[:3]]
        state.error_message = f"Requested time {pref_date} at {pref_time} is not available."
        return state
    
    else:
        # Scenario 2: General availability requested -> Suggest Top 3
        state.booking_status = "SUGGESTING_TOP_3"
        state.confirmed_slot = None
        state.suggested_slots = [s.astimezone(client_tz).isoformat() for s in available_slots[:3]]
        state.error_message = None
        return state

# %%
if __name__ == "__main__":
    print("Testing email responder locally with mock state...")
    
    # 1. Import your working email reader function
    from read_email import read_latest_email
    from state import EmailAgentState, MeetingAgentState
    from send_email import reply_and_escalate_node
    # 2. Create a blank state to start the pipeline
    current_state = MeetingAgentState()
    
    # 3. RUN NODE 1: Fetch the live email
    print("--- Running Email Reader Node ---")
    reader_output = read_latest_email(current_state)
    
    # 4. MANUALLY MERGE STATE (LangGraph will do this automatically later)
    # Update our current_state with the data Node 1 found
    current_state.subject = reader_output.get("subject")
    current_state.body = reader_output.get("body")
    current_state.sender_emailid = reader_output.get("sender_emailid")
    current_state.original_message_id = reader_output.get("original_message_id")
    
    from classify_email import classify_email_node_llm
    # 5. RUN NODE 2: Classify the live email
    print("\n--- Running Classifier Node ---")
    classify_email_node_llm(current_state)
    
    # Run the node
    reply_and_escalate_node(current_state)

    if current_state.classification == "Meeting-request":
        meeting_time(current_state)
        verify_or_suggest_slots_node(current_state)
        
    else:
        print("Email is not a meeting request.")

    print(current_state)

# %%