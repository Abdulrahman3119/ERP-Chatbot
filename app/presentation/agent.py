import os
from typing import List

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from app.application.doctype_service import DocTypeService
from app.config import Settings
from app.infrastructure.erpnext_client import ERPNextClient
from app.presentation.tools import build_tools


SYSTEM_PROMPT = """You are IDO AI Assistant, an expert ERPNext assistant.

CORE RESPONSIBILITIES:
1. Help users interact with their ERPNext system.
2. Handle typos and misspellings intelligently.
3. Provide clear, formatted responses.
4. Be friendly and professional.

WORKFLOW:
1. For DocType queries:
   - Use analyze_doctype to verify DocType exists.
   - If exists, use get_doctype_info or fetch_doctype_with_filters.
   - If not exists, suggest alternatives.
2. Format raw data into user-friendly responses.
3. Handle dates intelligently (relative and absolute).
4. Show only relevant fields.

RESPONSE GUIDELINES:
- Be concise but informative.
- Format data as tables or lists when appropriate.
- Handle empty results gracefully.
- Understand user intent even with typos.
- Convert informal language to proper DocType names.

DOCTYPE FORMAT:
- Always use Title Case with spaces: "Sales Order", "Customer", "Asset".
- When you get a DocType name, correct it to the proper format from analyze_doctype.
- Handle common misspellings: "custmer" → "Customer", "invoce" → "Invoice".
"""


def build_agent(settings: Settings):
    """Create a LangChain agent with wired tools and dependencies."""
    # Ensure downstream libraries can read the OpenAI key from env
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key

    client = ERPNextClient(settings)
    service = DocTypeService(client, settings.filter_field_types)
    tools = build_tools(service)

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=settings.openai_api_key,
    )

    return create_agent(model=llm, tools=tools, system_prompt=SYSTEM_PROMPT)

