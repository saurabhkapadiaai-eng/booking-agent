
# %%
# main.py
import os
import time
from dotenv import load_dotenv
from imapclient import IMAPClient
from state import EmailAgentState

# Import your compiled LangGraph app from workflow.py
from workflow import app

# --- CONFIGURATION ---
load_dotenv()

IMAP_SERVER = os.getenv("IMAP_SERVER", "outlook.office365.com")
EMAIL_ACCOUNT = os.getenv("EMAIL_ID_1")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD_1")

def run_idle_agent():
    print("Starting Real-Time Email Agent...")

    # Outer loop: Handles completely dropped connections (internet outages, etc.)
    while True:
        try:
            # Connect and log in using SSL
            with IMAPClient(IMAP_SERVER) as server:
                server.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
                server.select_folder('INBOX')
                print(f"✅ Logged in securely to {EMAIL_ACCOUNT}. Entering IDLE mode...")

                # Start IDLE mode (listening for push notifications)
                server.idle()

                # Inner loop: Listens for incoming traffic while connected
                while True:
                    # idle_check() blocks and waits for server activity.
                    # We set a timeout of 1700 seconds (~28 mins) to reset 
                    # before Microsoft/GoDaddy's 30-minute force-disconnect.
                    responses = server.idle_check(timeout=1700)

                    if responses:
                        print("\n[📧 ACTIVITY DETECTED] Server notification received:", responses)
                        
                        # We MUST exit IDLE mode before making other server requests or running the graph
                        server.idle_done()
                        
                        print("🚀 Triggering LangGraph workflow...")
                        # Initialize empty state and invoke the compiled graph
                        initial_state = EmailAgentState()
                        
                        # Your read_email node will fetch the UNSEEN email and pass it down the pipeline
                        app.invoke(initial_state)
                        
                        print("🏁 Workflow complete. Resuming IDLE mode...")
                        # Resume IDLE mode to wait for the next email
                        server.idle()
                        
                    else:
                        # If 28 minutes pass with no emails, refresh the IDLE session
                        print("\n[⏳ CONNECTION RENEWAL] Refreshing IDLE to prevent timeout...")
                        server.idle_done()
                        server.idle()

        except KeyboardInterrupt:
            print("\n🛑 Agent stopped by user.")
            break
        except Exception as e:
            # Catch network drops or unexpected server terminations and auto-reconnect
            print(f"\n[⚠️ ERROR] Connection lost: {e}")
            print("Attempting to reconnect in 15 seconds...")
            time.sleep(15)

if __name__ == "__main__":
    run_idle_agent()

# %%



