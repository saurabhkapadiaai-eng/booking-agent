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

        # 4. Search for emails (Here we search for "ALL". You could use "UNSEEN" for unread)
        status, messages = mail.search(None, "ALL") # "UNSEEN" / "ALL" replaced with "UNSEEN" before activating initiate.py

        # Convert the space-separated string of email IDs into a list
        email_ids = messages[0].split()

        if email_ids:
            # 5. Fetch the latest email (the last one in the list)
            latest_email_id = email_ids[-1]
            print(f"Fetching email ID: {latest_email_id.decode()}...")
            
            status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # Parse the raw bytes into an email message object
                    msg = email.message_from_bytes(response_part[1])

                    auth_header = msg.get("Authentication-Results", "Not Found")

                    # Decode the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        # If it's a bytes type, decode to string
                        subject = subject.decode(encoding if encoding else "utf-8")
                        
                    sender_name, sender_emailid = parseaddr(msg.get('From'))

                    original_message_id = msg.get("Message-ID")

                    # Extract basic information
                    print("="*50)
                    print(f"Subject: {subject}")
                    print(f"From: {msg.get('From')}")
                    print("="*50)

                    # Extract the body of the email
                    if msg.is_multipart():
                        full_body = ""
                        # Iterate over email parts to find the plain text body
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                chunk = part.get_payload(decode=True).decode()
                                full_body += chunk

                        state.body = full_body
                        print(f"Body:\n{full_body}")

                        return {
                            "subject": subject, 
                            "body": full_body,
                            "error_message": None, # Clear any previous errors
                            "sender_emailid": sender_emailid,
                            "original_message_id": original_message_id,
                            "auth_status": auth_header
                        }

                    else:
                        # If the email is not multipart, just read the payload
                        body = msg.get_payload(decode=True).decode()
                        state.body = body
                        print(f"Body:\n{body}")

                        return {
                            "subject": subject, 
                            "body": body,
                            "error_message": None, # Clear any previous errors
                            "sender_emailid": sender_emailid,
                            "original_message_id": original_message_id,
                            "auth_status": auth_header
                        }
                        
        else:
            print("No emails found in the inbox.")

        # 6. Logout and safely close the connection
        mail.logout()

    except imaplib.IMAP4.error as e:
        print(f"Authentication failed or IMAP error: {e}")
        print("Note: If MFA is enabled, ensure you are using an App Password.")
    except Exception as e:
        print(f"An error occurred: {e}")


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



