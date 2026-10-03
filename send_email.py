# %%
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

os.environ["HF_TOKEN"] = os.getenv("HF_TOKEN")

# Import your schema
from state import MeetingAgentState

# Load environment variables for SMTP
load_dotenv()
SMTP_SERVER = os.getenv("OUTGOING_SMTP_SERVER", "smtp.office365.com")
SMTP_PORT = int(os.getenv("OUTGOING_PORT", 587))
MY_SENDER_EMAIL = os.getenv("EMAIL_ID_1")
MY_SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD_1")
ESCALATION_EMAIL = os.getenv("ESCALATION_EMAIL")

# %%
from read_email import read_latest_email
from classify_email import classify_email_node_llm

# %%
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from transformers import pipeline, set_seed
set_seed(42)

generator = pipeline('text-generation', model='Qwen/Qwen2.5-7B-Instruct')

# %%
# import smtplib (Del, duplicate)

# Update your function like this:
def send_email(to_address: str, subject: str, body: str, message_id: str):
    """Helper function to send an email via SMTP."""
    
    msg = EmailMessage()
    msg['Subject'] = F"Re: {subject}"
    msg['From'] = MY_SENDER_EMAIL
    msg['To'] = to_address

    if message_id:
        msg['In-Reply-To'] = message_id
        msg['References'] = message_id

    msg.set_content(body)

    try:
    # Adding the timeout parameter (in seconds)
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.set_debuglevel(1)  # THIS IS KEY: It prints the SMTP exchange to your output cell
            server.login(MY_SENDER_EMAIL, MY_SENDER_PASSWORD)
            server.send_message(msg)

    except Exception as e:
        print(f"Failed to send email to {to_address}: {e}")
        raise e

# %%
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from transformers import pipeline, set_seed
set_seed(42)

def reply_and_escalate_node(state: MeetingAgentState) -> dict:
    """LangGraph node to auto-reply and escalate based on classification and urgency."""

    mail_class = state.classification
    mail_urgency = state.urgency
    mail_subject = state.subject
    mail_body = state.body
    mail_summary = state.summary
    sender_emailid = state.sender_emailid
    original_message_id = state.original_message_id
    #confirmed_slot = state.confirmed_slot
    suggested_slots = state.suggested_slots
               
    # Testing
    if sender_emailid == None:
        print(sender_emailid)
        return
    else:
        print(sender_emailid)

    if mail_class in ['Fresh-enquiry', 'Other']:

        prompt = [
        {
            "role": "system", 
            "content": f"You are a helpful customer support assistant with name Akanksha Patel from a firm named Allied Consultant. Write a professional, concise auto-reply to the following email. We want only mail body with proper salutation. Do not include placeholders like [Your Name]."
        },
        {
            "role": "user", 
            "content": mail_body
        }]

        output = generator(prompt)
        #print(output)

        output_body = output[0]['generated_text'][-1]['content']
        state.output_body = output_body

        send_email(sender_emailid, mail_subject, output_body, original_message_id)
        print("Auto reply sent to the sender!")
    else:
        pass

    if mail_urgency in ["high", "critical"] or mail_class in ['Threat', 'Fresh-enquiry']:
        escalation_subject = f"URGENT: {mail_urgency.upper()} - {mail_subject}"
        esclation_body = (
            f"Hi,\n\n"
            f"An email reuqiring immidiate attention has been received.\n\n"
            f"Subject: {mail_subject}\n\n"
            f"Classification: {mail_class.title()}\n"
            f"urgency: {mail_urgency.upper()}\n"
            f"Email Summary: {mail_summary}\n\n"
            f"Please review and take appropriate action."
        )
        send_email(ESCALATION_EMAIL, escalation_subject, esclation_body, None)
        print("Escalated to info@ mail id!")
    return {'error_message': None}

def email_suggested_slots(state: MeetingAgentState) -> dict:
    """LangGraph node to send suggested slots to the sender."""

    mail_subject = state.subject
    sender_emailid = state.sender_emailid
    original_message_id = state.original_message_id
    suggested_slots = state.suggested_slots

    if not suggested_slots:
        print("No suggested slots available.")
        return {'error_message': "No suggested slots available."}

    formatted_slots = []
    for idxm, slot in enumerate(suggested_slots, start=1):
        dt = datetime.fromisoformat(slot)
        formatted_slots.append(f"{idxm}. {dt.strftime('%A, %B %d, %Y at %I:%M %p')} ({state.client_timezone})")
    
    slots_body = (
        f"Hi,\n\n"
        f"Thank you for your email. Here are the suggested meeting slots:\n"
        f"{",\n".join(formatted_slots)}\n\n"
        f"Please let us know which slot works best for you.\n\n"
        f"Or you can schedule a meeting as per your convinience looking at calender at https://cal.com/allied-consultant/enauiry-discussion\n\n"
        f"Best regards,\n{os.getenv('REPLIED_BY')}"
    )
    
    send_email(sender_emailid, mail_subject, slots_body, original_message_id)
    print("Suggested slots sent to the sender!")

    return {'error_message': None}

if __name__ == "__main__":
    print("Testing email responder locally with mock state...")
    
    # 1. Import your working email reader function
    from read_email import read_latest_email
    from state import MeetingAgentState
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
    classification_result = classify_email_node_llm(current_state)
    
    print("\n--- Final Pipeline Output ---")
    print(classification_result)

    # Run the node
    reply_and_escalate_node(current_state)

    if not current_state.confirmed_slot and current_state.suggested_slots:
        email_suggested_slots(current_state)

# %%