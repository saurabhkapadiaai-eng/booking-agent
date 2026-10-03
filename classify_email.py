# %%
import os
from dotenv import load_dotenv
load_dotenv()

#os.environ["HF_TOKEN"] = "your_huggingface_token_here" **********************************

#Your pipeline code continues here...
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

if os.environ['GOOGLE_API_KEY'] and os.environ['OPENAI_API_KEY']:
    print("Bro, API keys are loaded!")
else:
    raise ValueError("LLM API keys are not set.")

from langchain_google_genai import ChatGoogleGenerativeAI

#llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite", #gemini-3.1-flash-lite
    temperature=1.0,  # Gemini 3.0+ defaults to 1.0
)

# %%
# welcome = llm.invoke("Namah Shivay")
# welcome.text

# %%
from typing import Optional, Literal
from pydantic import BaseModel, Field, EmailStr

class ClassificationOutput(BaseModel):
    # Fixed: Wrapped inside Optional[...] since default is None
        classification: Optional[Literal['Informative',
                                             'Sales & Marketing',
                                             'Meeting-request',
                                             'Email-reply',
                                             'Fresh-enquiry',
                                             'Spam', 'Threat', 'Other']] = Field(                                                               
                                                                    default=None, description=("Categorize the email into one of these exact types:"
                                                                    "1. 'Meeting-request' (HIGHEST PRIORITY: Any email requesting to schedule, book, reschedule, or confirm a meeting/call, EVEN IF it is part of an ongoing reply thread with 'Re:' or 'Fwd:'),\n"
                                                                    "2. 'Email-reply' (responses to ongoing threads that DO NOT contain any meeting requests),\n"
                                                                    "3. 'Fresh-enquiry' (new leads, projects, or questions on previous reply or thread or proposal),\n"
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
                                                                            "'critical' (immediate security alerts, system failures, password resets, or high-value account issues)."))
        topic: Optional[str] = Field(default=None, description="The core topic topic of the message")
        summary: Optional[str] = Field(default=None, description="A brief summary of the email content")

class reply_meeting_class(BaseModel):
            classification: Optional[Literal['Meeting-request','Email-reply']] = Field(
                default='Email-reply', description=("Categorize the email into one of these exact types:"
                                                    "1. 'Meeting-request' (HIGHEST PRIORITY: Any email requesting to schedule, book, reschedule, or confirm a meeting/call, EVEN IF it is part of an ongoing reply thread with 'Re:' or 'Fwd:'),\n"
                                                    "2. 'Email-reply' (responses to ongoing threads that DO NOT contain any meeting requests)"))

llm_with_struct_output = llm.with_structured_output(ClassificationOutput)
llm_reply_meeting_class = llm.with_structured_output(reply_meeting_class)

# %%
from bs4 import BeautifulSoup
from transformers import pipeline

# Import your schema from your state.py file
from state import EmailAgentState

CANDIDATE_LABELS = ['Informative', 'Sales & Marketing', 'Email-reply', 'Fresh-enquiry', 'Spam', 'Other']

def classify_email_node_llm(state: EmailAgentState) -> dict:
    # Read the data left on the whiteboard by the previous node
    subject = state.subject or ""
    raw_body = state.body or ""
    sender_emailid = state.sender_emailid or ""
    auth_status = state.auth_status or "Not Available"
    #print(f'Raw Body: \n{raw_body}\n\n')

    if raw_body:
        soup = BeautifulSoup(raw_body, "html.parser")
        clean_body = soup.get_text(separator=" ", strip=True)
    else:
        clean_body = ""

    # 3. Combine the Subject and Body for maximum context
    # We add "Subject:" and "Body:" prefixes to help the model understand the structure
    combined_text = f"Authentication Status: {auth_status}, sender email id: {sender_emailid}\nSubject: {subject}\n\nBody: {clean_body}"
    
    # 4. Truncate to prevent crashing the model (BART has a token limit)
    text_to_classify = combined_text[:1500]

    try:
        result = llm_with_struct_output.invoke(text_to_classify)

        if result.classification == 'Email-reply':
                    text_class = f"topic: {result.topic}, summary: {result.summary}"
                    result.classification = llm_reply_meeting_class(text_class)
                
        # The zero-shot pipeline returns a dictionary with 'labels' and 'scores' sorted by highest confidence
        state.classification = result.classification
        state.urgency = result.urgency
        state.topic = result.topic
        state.summary = result.summary

        print(f"Mail is classified as {result.classification}")
        # 6. Return the updated classification field as a dictionary for LangGraph to merge
        return {"classification": result.classification,
                "urgency": result.urgency,
                "topic": result.topic,
                "summary": result.summary}
            
    except Exception as e:
        print(f"Classification failed: {e}")
        # Optionally update the error_message in your state if it fails
        return {"error_message": f"Classifier Error: {str(e)}"}

# %%
if __name__ == "__main__":
    print("Testing Full Pipeline: Reading -> Classifying...\n")
    
    # 1. Import your working email reader function
    from read_email import read_latest_email
    
    # 2. Create a blank state to start the pipeline
    current_state = EmailAgentState()
    
    # 3. RUN NODE 1: Fetch the live email
    print("--- Running Email Reader Node ---")
    reader_output = read_latest_email(current_state)
    
    # 4. MANUALLY MERGE STATE (LangGraph will do this automatically later)
    # Update our current_state with the data Node 1 found
    current_state.subject = reader_output.get("subject")
    current_state.body = reader_output.get("body")
    current_state.auth_status = reader_output.get("auth_stauts")
    current_state.sender_emailid = reader_output.get("sender_emailid")
    
    # 5. RUN NODE 2: Classify the live email
    print("\n--- Running Classifier Node ---")
    classification_result = classify_email_node_llm(current_state)
    
    print("\n--- Final Pipeline Output ---")
    print(classification_result)