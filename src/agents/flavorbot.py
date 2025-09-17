"""
LangGraph agent definition for FlavorBot.
"""

from langgraph.graph import StateGraph, END
from langchain.memory import ConversationBufferMemory
from langchain.schema import messages_from_dict, messages_to_dict
from tools.rag import RecipeRetriever
from typing import TypedDict, List, Dict
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG for more detail
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FlavorBot")

# Define the state structure
class FlavorBotState(TypedDict):
    input: str
    retrieved: List[Dict]
    output: str
    chat_history: List[dict]


# Load the retriever
retriever = RecipeRetriever(
    index_path="models/faiss.index",
    data_path="data/processed/recipes_cleaned.csv"
    
)


# Node: retrieve top recipes
def rag_node(state: FlavorBotState) -> FlavorBotState:
    query = state["input"]
    logger.info("👂 Received user query: '%s'", query)
    logger.info("🔎 Searching recipe index...")
    results = retriever.query(query, k=3)
    logger.info("📦 Retrieved %d candidate recipes", len(results))
    for idx, r in enumerate(results, 1):
        logger.debug("🍲 [%d] %s", idx, r["name"])
    state["retrieved"] = results
    logger.info("✅ Retrieval step complete")
    print("📦 📦 📦 📦 📦 📦 Retrieved recipes for LLM:")
    for r in state:
        print(" ----", r["name"])

    return state


# Node: summarize with LLM
def summarize_node(state: FlavorBotState) -> FlavorBotState:
    recipes = state["retrieved"]
    logger.info("📝 Formatting %d recipes for the LLM", len(recipes))

    formatted_recipes = "\n\n".join([
        f"🍽️ Recipe: {r['name']}\n🛒 Ingredients: {r['ingredients']}\n👨‍🍳 Steps: {r['steps'][:500]}..."
        for r in recipes
    ])

    chat_history = state.get("chat_history", [])
    logger.info("📜 Including %d past chat messages", len(chat_history))

    # Build messages for OpenAI
    logger.debug("⚙️ Building system + user prompts")
    messages = chat_history.copy()
    messages.insert(0, {
        "role": "system",
        "content": (
            "You are a friendly and knowledgeable cooking assistant. "
            "You suggest and explain recipes based on user input and retrieved recipe matches. "
            "Always refer to previous messages for context. Be natural and helpful."
        )
    })
    messages.append({
        "role": "user",
        "content": f"Here are some matching recipes:\n{formatted_recipes}"
    })

    logger.info("🤖 Sending request to OpenAI model...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.3
    )

    result_text = response.choices[0].message.content.strip()
    logger.info("📬 Response received from LLM")
    state["output"] = result_text
    logger.info("✨ Summarization complete")
    return state


# Build the LangGraph flow
def build_graph():
    logger.info("🛠️ Building FlavorBot workflow graph...")
    graph = StateGraph(FlavorBotState)
    graph.add_node("retrieve", rag_node)
    graph.add_node("summarize", summarize_node)
    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "summarize")
    graph.set_finish_point("summarize")
    logger.info("🧩 Graph assembly complete")
    return graph


# Function to run the bot
def run_flavorbot(input_text: str, chat_history: List[dict]) -> str:
    logger.info("🚀 Starting FlavorBot run...")
    graph = build_graph().compile()
    state = {
        "input": input_text,
        "chat_history": chat_history,
        "retrieved": [],
        "output": ""
    }
    logger.info("👤 User said: %s", input_text)
    logger.info("▶️ Invoking workflow...")
    result = graph.invoke(state)
    logger.info("🏁 FlavorBot run finished successfully")
    logger.info("🗨️ Final output: %s", result['output'][:120] + "..." if len(result['output']) > 120 else result['output'])
    return result["output"]