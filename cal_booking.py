# %%
import os
import requests
from dotenv import load_dotenv
from state import MeetingAgentState

load_dotenv()

CAL_API_KEY = os.getenv("CAL_API_KEY")
CAL_EVENT_TYPE_ID = int(os.getenv("CAL_EVENT_TYPE_ID", "0"))
CAL_USER_EMAIL = os.getenv("CAL_USER_EMAIL", "abc@def.com")

def book_meeting_node(state: MeetingAgentState) -> dict:
    """LangGraph node to book a meeting slot via Cal.com API v2."""

    # 1. Safely extract values from the Pydantic state
    attendee_email = state.sender_emailid
    confirmed_slot = state.confirmed_slot

    timezone = state.client_timezone if state.client_timezone else "Asia/Kolkata"
    
    if not all([attendee_email, confirmed_slot]):
        return {"error_message": "Missing required booking details (email or confirmed slot)."}
    
    # 2. Format ISO 8601 Start Time (e.g., '2026-07-25T10:00:00Z')
    start_time_iso = confirmed_slot #f"{date_str}T{time_str}:00Z"
    
    # 3. Construct API Payload
    url = "https://api.cal.com/v2/bookings"
    headers = {
        "Authorization": f"Bearer {CAL_API_KEY}",
        "Content-Type": "application/json",
        "cal-api-version": "2024-08-13" 
    }
    
    payload = {
        "start": start_time_iso,
        "eventTypeId": CAL_EVENT_TYPE_ID,
        "attendee": {
            "name": attendee_email.split("@")[0], 
            "email": attendee_email,
            "timeZone": timezone,
            "language": "en"
        },
        "metadata": {
            "booked_by": "LangGraph Python Agent",
            "host_email": CAL_USER_EMAIL
        }
    }
    
    # 4. Execute Booking
    try:
        print(f"Attempting to book slot for {attendee_email} at {start_time_iso}...")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code in [200, 201]:
            data = response.json()
            booking_id = data.get("data", {}).get("id")
            print(f"Booking Successful! ID: {booking_id}")

            state.booking_status = "SUCCESS"
            state.booking_url = f"https://app.cal.com/booking/{booking_id}"
            state.error_message = None
            return {
                "booking_status": "SUCCESS",
                "booking_url": f"https://app.cal.com/booking/{booking_id}",
                "error_message": None
            }
        else:
            err_msg = f"API Error {response.status_code}: {response.text}"
            print(err_msg)
            state.booking_status = "FAILED"
            state.error_message = err_msg
            return {"booking_status": "FAILED", "error_message": err_msg}
            
    except Exception as e:
        state.booking_status = "ERROR"
        state.error_message = str(e)
        return {"booking_status": "ERROR", "error_message": str(e)}

if __name__ == "__main__":
    print("Testing Cal.com booking node locally...")
    
    # 1. Create a mock state with the exact fields your node expects
    mock_state = MeetingAgentState(
        sender_emailid="test.attendee@example.com", # Change to your own email to test!
        confirmed_slot="2026-08-15T15:00:00+05:30", 
        client_timezone="Asia/Kolkata"
    )
    
    # 2. Run the node just like LangGraph would
    result = book_meeting_node(mock_state)
    
    # 3. Print the dictionary returned to LangGraph
    print("\n--- Node Output ---")
    print(result)
