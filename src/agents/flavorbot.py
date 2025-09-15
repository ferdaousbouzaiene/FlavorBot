"""
LangGraph agent definition for FlavorBot.
"""

from langgraph.graph import StateGraph, END
from src.tools.rag import RecipeRetriever
from typing import TypedDict, List, Dict

#Define the state structure

class FlavorBotState(TypedDict):
    input: str
    retrieved: List[Dict]
    output: str

# Load the retriever
retriever = RecipeRetriever(
    index_path="models/faiss.index",
    data_path="data/processed/recipes_cleaned.csv"
)

# Node: retrieve top recipes
def rag_node(state: FlavorBotState) -> FlavorBotState:
    query = state["input"]
    results = retriever.query(query, k=3)
    state["retrieved"] = results
    return state

# Node: format response
def summarize_node(state: FlavorBotState) -> FlavorBotState:
    recipes = state["retrieved"]
    summary = "\n\n".join([
        f"🍽️ {r['name'].title()}\n🧂 Ingredients: {r['ingredients']}\n📋 Steps: {r['steps'][:300]}..."
        for r in recipes
    ])
    state["output"] = summary
    return state

# Build the LangGraph flow
def build_graph():
    graph = StateGraph(FlavorBotState)
    graph.add_node("retrieve", rag_node)
    graph.add_node("summarize", summarize_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "summarize")
    graph.set_finish_point("summarize")
    return graph

# Function to run the bot
def run_flavorbot(input_text: str) -> str:
    graph = build_graph().compile()
    state = {"input": input_text}
    result = graph.invoke(state)
    return result["output"]
