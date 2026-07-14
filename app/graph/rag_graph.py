from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app import models
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.generation_service import generate_answer
from app.services.groundedness_service import is_answer_grounded
from google import genai
from app.config import settings

_client = genai.Client(api_key=settings.gemini_api_key)


class RAGState(TypedDict):
    question: str
    company_id: str
    db: Session
    needs_retrieval: bool
    retrieved_chunks: list
    answer: str
    was_grounded: bool


def router_node(state: RAGState) -> RAGState:
    """Decides whether this question needs document retrieval at all."""
    prompt = f"""Does answering this question require looking up specific information
from company documents, or is it a general conversational message
(greeting, thanks, small talk, asking what the assistant can do)?

Question: "{state['question']}"

Respond with exactly one word: "retrieve" or "general"."""

    response = _client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
    decision = response.text.strip().lower()

    state["needs_retrieval"] = "retrieve" in decision
    return state


def retrieve_node(state: RAGState) -> RAGState:
    chunks = retrieve_relevant_chunks(state["question"], state["company_id"], state["db"])
    state["retrieved_chunks"] = chunks
    return state


def generate_with_context_node(state: RAGState) -> RAGState:
    context_texts = [chunk.chunk_text for chunk in state["retrieved_chunks"]]
    state["answer"] = generate_answer(state["question"], context_texts)
    return state


def generate_general_node(state: RAGState) -> RAGState:
    """For questions that don't need retrieval — a plain, direct response."""
    response = _client.models.generate_content(
        model="gemini-3.5-flash",
        contents=f"Respond briefly and helpfully to: {state['question']}",
    )
    state["answer"] = response.text.strip()
    state["retrieved_chunks"] = []
    return state


def groundedness_check_node(state: RAGState) -> RAGState:
    context_texts = [chunk.chunk_text for chunk in state["retrieved_chunks"]]
    state["was_grounded"] = is_answer_grounded(state["answer"], context_texts)
    return state


def route_decision(state: RAGState) -> str:
    """Tells the graph which path to take after the router node runs."""
    return "retrieve" if state["needs_retrieval"] else "general"


# Build the graph
graph_builder = StateGraph(RAGState)

graph_builder.add_node("router", router_node)
graph_builder.add_node("retrieve", retrieve_node)
graph_builder.add_node("generate_with_context", generate_with_context_node)
graph_builder.add_node("generate_general", generate_general_node)
graph_builder.add_node("groundedness_check", groundedness_check_node)

graph_builder.set_entry_point("router")

graph_builder.add_conditional_edges(
    "router",
    route_decision,
    {"retrieve": "retrieve", "general": "generate_general"},
)

graph_builder.add_edge("retrieve", "generate_with_context")
graph_builder.add_edge("generate_with_context", "groundedness_check")
graph_builder.add_edge("groundedness_check", END)
graph_builder.add_edge("generate_general", END)

rag_graph = graph_builder.compile()