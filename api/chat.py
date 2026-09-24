import os
from http.server import BaseHTTPRequestHandler
import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

load_dotenv()

llm = ChatOpenAI(
    model="openai/gpt-4o-mini",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    temperature=0.3,
)

triage_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "Classify this customer message with a category and priority, "
            "separated by a comma, nothing else. "
            "Category: 'policy_violation', 'genuine_defect', or 'other'. "
            "Priority: 'High', 'Medium', or 'Low'."
        ),
    ),
    ("human", "{input}"),
])

def parse_triage(raw: str) -> dict:
    parts = [p.strip() for p in raw.split(",")]
    return {
        "category": parts[0] if len(parts) > 0 else "other",
        "priority": parts[1] if len(parts) > 1 else "Medium",
    }

triage_subchain = (
    triage_prompt
    | llm
    | StrOutputParser()
    | RunnableLambda(parse_triage)
)

combo_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        (
            "You are a Hopscotch customer support assistant. Every incoming "
            "message has already been internally triaged (not shown to the "
            "customer). Use this to calibrate tone and urgency: for "
            "genuine_defect with High priority, apologize sincerely and offer "
            "an immediate replacement or refund; for policy_violation, explain "
            "the policy warmly; for other, ask a clarifying question. "
            "NEVER mention the words category, priority, or triage to the customer."
        ),
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "[internal triage: {triage}]\nCustomer: {input}"),
])

combo_chain = (
    RunnablePassthrough.assign(
        triage=(lambda x: {"input": x["input"]}) | triage_subchain
    )
    | combo_prompt
    | llm
    | StrOutputParser()
)

class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json(200, {"ok": True})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw_body = self.rfile.read(length)
            data = json.loads(raw_body.decode("utf-8"))

            message = data.get("message", "").strip()
            history = data.get("history", [])

            if not message:
                self._send_json(400, {"error": "Message is required"})
                return

            chat_history = []
            for item in history:
                role = item.get("role")
                content = item.get("content", "")
                if role == "user":
                    chat_history.append(("human", content))
                elif role == "assistant":
                    chat_history.append(("ai", content))

            result = combo_chain.invoke({
                "input": message,
                "chat_history": chat_history,
            })

            self._send_json(200, {"reply": result})

        except Exception as e:
            self._send_json(500, {"error": str(e)})
