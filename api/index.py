import os
import json
from http.server import BaseHTTPRequestHandler
from state import MeetingAgentState
from workflow import app

class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode('utf-8'))

    def do_OPTIONS(self):
        self._send_json(200, {"status": "ok"})

    def do_GET(self):
        # Health check and status endpoint
        self._send_json(200, {
            "status": "healthy",
            "service": "AI Meeting Booking Agent",
            "usage": {
                "health_check": "GET /api/index",
                "trigger_workflow": "POST /api/index"
            }
        })

    def do_POST(self):
        # Optional: verify bearer token / cron secret
        cron_secret = os.getenv("CRON_SECRET")
        auth_header = self.headers.get("Authorization", "")
        if cron_secret and auth_header != f"Bearer {cron_secret}":
            self._send_json(401, {"error": "Unauthorized: Invalid CRON_SECRET token"})
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            payload = {}
            if content_length > 0:
                body = self.rfile.read(content_length)
                try:
                    payload = json.loads(body.decode('utf-8'))
                except json.JSONDecodeError:
                    pass

            # Initialize state with any custom input provided, else standard empty state
            state_data = MeetingAgentState(**payload) if payload else MeetingAgentState()

            # Execute the LangGraph workflow
            result = app.invoke(state_data)

            # Return serialized result
            result_dict = result.dict() if hasattr(result, "dict") else dict(result)

            self._send_json(200, {
                "status": "success",
                "message": "Workflow executed successfully",
                "result": result_dict
            })
        except Exception as e:
            self._send_json(500, {
                "status": "error",
                "error": str(e)
            })
