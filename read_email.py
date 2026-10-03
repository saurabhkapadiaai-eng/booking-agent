# %%
import os
from dotenv import load_dotenv
load_dotenv()

os.environ["EMAIL_ID_1"] = os.getenv("EMAIL_ID_1")
os.environ["EMAIL_PASSWORD_1"] = os.getenv("EMAIL_PASSWORD_1")
os.environ["IMAP_SERVER"] = os.getenv("IMAP_SERVER")
os.environ["INCOMING_PORT"] = os.getenv("INCOMING_PORT")
os.environ["OUTGOING_SMTP_SERVER"] = os.getenv("OUTGOING_SMTP_SERVER")
os.environ["OUTGOING_PORT"] = os.getenv("OUTGOING_PORT")

# %% [markdown]
# - **Step 1: Importing Libraries**

# %%
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr

# %% [markdown]
# - **Step 2: Saving Credentials**

# %%
username = os.environ["EMAIL_ID_1"]
password = os.environ["EMAIL_PASSWORD_1"]
imap_server = os.environ["IMAP_SERVER"]

# %%
# Import your schema from your state.py file
from state import MeetingAgentState

def read_latest_email(state: MeetingAgentState) -> dict:
    try:
        # 1. Connect to the IMAP server over SSL
        print("Connecting to the server...")
        mail = imaplib.IMAP4_SSL(imap_server)

        # 2. Login to your account
        mail.login(username, password)
        print("Login successful!\n")

        # 3. Select the mailbox you want to check (default is 'inbox')
        mail.select("inbox")

        # 4. Search for unread emails first, fallback to ALL if no unread
        status, messages = mail.search(None, "UNSEEN")
        email_ids = messages[0].split() if messages and messages[0] else []
        
        if not email_ids:
            # If no unread, check recent ALL emails
            status, messages = mail.search(None, "ALL")
            email_ids = messages[0].split() if messages and messages[0] else []

        if email_ids:
            # Sort IDs numerically to always guarantee the latest chronological email
            email_ids = sorted(email_ids, key=lambda x: int(x))
            latest_email_id = email_ids[-1]
            print(f"Fetching latest email ID: {latest_email_id.decode()} (from {len(email_ids)} emails)...")
            
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # Parse the raw bytes into an email message object
                    msg = email.message_from_bytes(response_part[1])

                    auth_header = msg.get("Authentication-Results", "Not Found")

                    # Decode the email subject
                    subject_header = msg.get("Subject", "")
                    if subject_header:
                        decoded_chunks = decode_header(subject_header)
                        subject_parts = []
                        for text, encoding in decoded_chunks:
                            if isinstance(text, bytes):
                                subject_parts.append(text.decode(encoding or "utf-8", errors="replace"))
                            else:
                                subject_parts.append(str(text))
                        subject = "".join(subject_parts)
                    else:
                        subject = "(No Subject)"
                        
                    sender_name, sender_emailid = parseaddr(msg.get('From', ''))
                    original_message_id = msg.get("Message-ID")

                    # Extract basic information safely
                    print("="*50)
                    try:
                        print(f"Subject: {subject}")
                        print(f"From: {msg.get('From')}")
                    except UnicodeEncodeError:
                        print(f"Subject: {subject.encode('ascii', 'replace').decode()}")
                    print("="*50)

                    # Extract the body of the email safely
                    full_body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition", ""))

                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    charset = part.get_content_charset() or "utf-8"
                                    try:
                                        full_body += payload.decode(charset, errors="replace")
                                    except Exception:
                                        full_body += payload.decode("utf-8", errors="replace")
                    else:
                        payload = msg.get_payload(decode=True)
                        if payload:
                            charset = msg.get_content_charset() or "utf-8"
                            try:
                                full_body = payload.decode(charset, errors="replace")
                            except Exception:
                                full_body = payload.decode("utf-8", errors="replace")

                    state.subject = subject
                    state.body = full_body
                    state.sender_emailid = sender_emailid
                    state.original_message_id = original_message_id
                    state.auth_status = auth_header

                    try:
                        print(f"Body length: {len(full_body)} characters")
                    except Exception:
                        pass

                    return {
                        "subject": subject, 
                        "body": full_body,
                        "error_message": None,
                        "sender_emailid": sender_emailid,
                        "original_message_id": original_message_id,
                        "auth_status": auth_header
                    }
                        
        else:
            print("No emails found in the inbox.")

        # 6. Logout and safely close the connection
        mail.logout()
        return {}

    except imaplib.IMAP4.error as e:
        print(f"Authentication failed or IMAP error: {e}")
        return {"error_message": f"IMAP Error: {e}"}
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"error_message": f"Read Error: {e}"}


# if __name__ == "__main__":
#     print("Testing email reader locally...")
    
    # # Unpack the returned tuple
    # email = read_latest_email()
    
    # if email['subject']:
    #     print(f"Success! Fetched Subject: {email['subject']}")
    #     # print(f"Fetched Body: {test_body}") # Uncomment to view the full body
    # else:
    #     print("Test finished: No emails found or an error occurred.")

# %%
if __name__ == "__main__":
    print("Testing email reader locally with LIVE data...")
    
    # 1. Create a blank initial state to satisfy the function's requirement
    # (Assuming MeetingAgentState has default values or Optional fields)
    initial_state = MeetingAgentState() 
    
    # 2. Run the function, passing in the blank state, and save the result
    returned_data = read_latest_email(initial_state)
    
    # 3. Print the exact raw dictionary returned by the function
    print("\n" + "="*50)
    print("EXACT RETURNED DICTIONARY:")
    print("="*50)
    print(returned_data)

# %%



