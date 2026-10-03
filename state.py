from typing import Optional, Literal, List
from pydantic import BaseModel, Field, EmailStr

# Notice we inherit from BaseModel now, not TypedDict
class EmailAgentState(BaseModel):
    # Using default=None is safer for LangGraph so nodes can do partial updates
    subject: Optional[str] = Field(default=None, description="Subject of an email")
    body: Optional[str] = Field(default=None,
                                description="The full extracted body text of the email")
    
    original_message_id: Optional[str] =Field(default=None, description="The message ID of the received email")
    auth_status: Optional[str] = Field(default=None, description="Authentication status (e.g., SPF, DKIM, DMARC pass/fail results or raw Authentication-Results header) used to detect email spoofing and sender domain mismatches.")
    classification: Optional[Literal['Informative',
                                    'Sales & Marketing',
                                    'Meeting-request',
                                    'Email-reply',
                                    'Fresh-enquiry',
                                    'Spam', 'Threat', 'Other']] = Field(                                                               
                                                        default=None, description=("Categorize the email into one of these exact types:"
                                                        "1. 'Meeting-request' (HIGHEST PRIORITY: Any email requesting to schedule, book, reschedule, or confirm a meeting/call, EVEN IF it is part of an ongoing reply thread with 'Re:' or 'Fwd:'),\n"
                                                        "2. 'Email-reply' (responses to ongoing threads that DO NOT contain any meeting requests),\n"
                                                        "3. 'Fresh-enquiry' (new leads, projects, or questions),\n"
                                                        "4. 'Informative' (newsletters, updates, general FYI),\n"
                                                        "5. 'Sales & Marketing' (promos, vendor pitches),\n"
                                                        "6. 'Spam' (unsolicited junk mail),\n"
                                                        "7. 'Threat' (Phishing, pharming, asking for urgent payment or sensitive credentials. Check auth_status as reference),\n"
                                                        "8. 'Other' (for all emails where the category cannot be defined)."))
    urgency: Optional[Literal['low', 'medium', 'high', 'critical']] = Field(
        default=None,
        description=(
        "Assess and categorize the operational urgency of the email strictly into one of these types: "
        "'low' (general updates, newsletters, no response needed), "
        "'medium' (standard business inquiries, partnership requests, tasks with flexible deadlines), "
        "'high' (fresh leads, active customer requests, or items needing a response within 24 hours), "
        "or 'critical' (immediate security alerts, system failures, password resets, or high-value account issues)."
        ))
    sender_emailid: Optional[EmailStr] = Field(default=None, description="Email Id from which the email has been received.")
    #email_subject: Optional[str] = Field(default=None, description="Subject of the received email")
    topic: Optional[str] = Field(default=None, description="The core topic of the message")
    summary: Optional[str] = Field(default=None, description="A brief summary of the email content")
    error_message: Optional[str] = Field(default=None, description="Any IMAP or processing errors encountered")
    output_body: Optional[str] = Field(default=None, description="The full body text of the email to be sent excluding email signature")
    email_signature: Optional[str] = Field(default=None, description="Email Signature")

class MeetingAgentState(EmailAgentState):
    """
    Inherits all email fields automatically without re-declaring them,
    and adds the scheduling/booking capabilities for relevant email branches.
    """
    # New Scheduling Fields
    preferred_date: Optional[str] = Field(default=None, description="ISO format date YYYY-MM-DD")
    preferred_time: Optional[str] = Field(default=None, description="Time in HH:MM format (24hr)")
    duration_minutes: Optional[int] = Field(default=30, description="Meeting length in minutes")
    client_timezone: Optional[str] = Field(default="Asia/Kolkata", description="Attendee timezone")
    suggested_slots: Optional[List[str]] = Field(default=None, description="Top 3 available ISO timestamps")
    confirmed_slot: Optional[str] = Field(default=None, description="Confirmed slot (date and time) for calender booking")
    
    # Output Status
    booking_status: Optional[str] = Field(default=None, description="Status of the Cal.com booking")
    booking_url: Optional[str] = Field(default=None, description="Confirmation link")
    error_message: Optional[str] = Field(default=None, description="Any processing errors encountered")

if __name__ == "__main__":
    print("--- Testing State Schema Validation ---")
    try:
        # Test if it rejects invalid classification types or handles defaults cleanly
        test_state = EmailAgentState(subject="Test", classification="Other")
    except Exception as e:
        print(f"Schema successfully caught invalid data: {e}")
# from typing import TypedDict, Optional, Annotated

# class EmailAgentState(TypedDict):
#     # Annotated allows you to attach metadata (like descriptions) to standard types
#     subject: Annotated[Optional[str], "Subject of an email"]
#     body: Annotated[Optional[str], "The full extracted body text of the email"]
#     classification: Annotated[Optional[str], "The final category assigned by the LLM"]
#     error_message: Annotated[Optional[str], "Any IMAP or processing errors encountered"]