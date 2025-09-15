"""
LangGraph agent definition for FlavorBot.
"""

from langgraph.graph import StateGraph, END
from tools.rag import RecipeRetriever
from typing import TypedDict, List, Dict
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
api_key = os.getenv("OPENAI_API_KEY")



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
# def summarize_node(state: FlavorBotState) -> FlavorBotState:
#     recipes = state["retrieved"]
#     summary = "\n\n".join([
#         f"🍽️ {r['name'].title()}\n🧂 Ingredients: {r['ingredients']}\n📋 Steps: {r['steps'][:300]}..."
#         for r in recipes
#     ])
#     state["output"] = summary
#     return state


def summarize_node(state: FlavorBotState) -> FlavorBotState:
    recipes = state["retrieved"]

    # Build context prompt for the LLM
    formatted = "\n\n".join([
        f"Recipe: {r['name']}\nIngredients: {r['ingredients']}\nSteps: {r['steps'][:500]}"
        for r in recipes
    ])

    prompt = f"""
You are a helpful cooking assistant. Based on the following recipes, suggest the best one or summarize the top 3 options for a user query. Be friendly and informative.

### Recipes:
{formatted}

### Respond:
"""

    # Call GPT-4 or GPT-3.5-turbo
    response = client.chat.completions.create(model="gpt-3.5-turbo",  # or "gpt-4"
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7)

    state["output"] = response.choices[0].message.content.strip()
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
