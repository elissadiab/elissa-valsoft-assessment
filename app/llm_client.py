"""
llm_client.py

Handles communication with the LLM provider.

For this project, Groq is used for classification, enrichment, entity extraction,
confidence scoring, and summary generation.
"""

import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from app.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    build_classification_user_prompt,
)
from app.schemas import AIAnalysisResult, CustomerRequest


load_dotenv()


DEFAULT_MODEL_PROVIDER = "groq"
DEFAULT_MODEL_NAME = "llama-3.3-70b-versatile"


# Read the configured model provider.
def get_model_provider() -> str:
    return os.getenv("LLM_PROVIDER", DEFAULT_MODEL_PROVIDER)


# Read the configured model name.
def get_model_name() -> str:
    return os.getenv("LLM_MODEL", DEFAULT_MODEL_NAME)


# Build the Groq chat model.
def build_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "Missing GROQ_API_KEY. Please create a .env file and add your Groq API key."
        )

    return ChatGroq(
        groq_api_key=api_key,
        model_name=get_model_name(),
        temperature=0, # 0 to be deterministic and as consistent as possible
    )


# Analyze one customer request using structured LLM output.
def analyze_request_with_llm(request: CustomerRequest) -> AIAnalysisResult:
    llm = build_llm()

    structured_llm = llm.with_structured_output(AIAnalysisResult)

    messages = [
        SystemMessage(content=CLASSIFICATION_SYSTEM_PROMPT),
        HumanMessage(content=build_classification_user_prompt(request)),
    ]

    result = structured_llm.invoke(messages)

    return result