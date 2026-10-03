# %%
from state import EmailAgentState, MeetingAgentState
from read_email import read_latest_email
from classify_email import classify_email_node_llm
from send_email import email_suggested_slots, send_email, reply_and_escalate_node
from cal_availability import meeting_time, fetch_calcom_slots, verify_or_suggest_slots_node
from cal_booking import book_meeting_node

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import RetryPolicy
from langgraph.graph import StateGraph, START, END

# Create the graph
workflow = StateGraph(MeetingAgentState)

# Add nodes with appropriate error handling
workflow.add_node("read_email", read_latest_email)
workflow.add_node("classify_email", classify_email_node_llm)
workflow.add_node("reply_and_escalate", reply_and_escalate_node)
workflow.add_node("extract_meeting_time", meeting_time)
#workflow.add_node("fetch_calcom_slots", fetch_calcom_slots)
workflow.add_node("verify_or_suggest_slots", verify_or_suggest_slots_node)
workflow.add_node("book_meeting", book_meeting_node)
workflow.add_node("email_suggested_slots", email_suggested_slots)

def route_after_reading(state: MeetingAgentState):
    """Check if an email was actually fetched. If not, stop the graph."""
    if not state.subject and not state.body:
        print("No unread emails found. Ending working flow early.")
        return "end"
    return "continue"

def meeting_mail(state: MeetingAgentState):
    """Check if the email is a meeting request. If not, stop the graph."""
    if state.classification != "Meeting-request":
        print("Email is not a meeting request. Ending working flow early.")
        return "end"
    return "continue"

def slot_confirmed(state: MeetingAgentState):
    """Check if a meeting slot was confirmed. If not, suggest other available slots."""
    if not state.confirmed_slot and state.suggested_slots:
        print("No meeting slot confirmed. Suggesting alternative slots.")
        return "suggest_slots"
    return "continue"

# Add only the essential edges
workflow.add_edge(START, "read_email")
workflow.add_conditional_edges(
    "read_email",
    route_after_reading,{"continue": "classify_email", "end": END}
)

#workflow.add_edge("read_email", "classify_email")
workflow.add_edge("classify_email", "reply_and_escalate")
workflow.add_conditional_edges(
    "reply_and_escalate",
    meeting_mail,
    {"continue": "extract_meeting_time", "end": END}
)
workflow.add_edge("extract_meeting_time", "verify_or_suggest_slots")
workflow.add_conditional_edges(
    "verify_or_suggest_slots",
    slot_confirmed,
    {"continue": "book_meeting", "suggest_slots": "email_suggested_slots", "end": END}
)
workflow.add_edge("book_meeting", END)
#workflow.add_edge("send_email", END)

# Compile with checkpointer for persistence, in case run graph with Local_Server --> Please compile without checkpointer
# memory = MemorySaver()
# app = workflow.compile(checkpointer=memory)
app = workflow.compile()

# %%
# --- Run the graph when executed directly from terminal ---
if __name__ == "__main__":
    print("Starting Meeting Agent Workflow...")

    current_state = MeetingAgentState()
    output = MeetingAgentState()

    output = app.invoke(current_state)
# %%

# %%
# graph = workflow.compile()

# from IPython.display import Image, display

# # # if error is thrown on the below command
# Image(app.get_graph().draw_mermaid_png())

# # # MINIMAL CHANGE: Force the local rendering method
# Image(app.get_graph().draw_mermaid_png())

# %%



