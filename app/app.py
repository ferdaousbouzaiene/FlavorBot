import os
import sys
import streamlit as st
import csv
import base64
from datetime import datetime

# Set up import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

try:
    from agents.flavorbot import run_flavorbot
except ImportError:
    st.error("FlavorBot module not found. Please ensure the agents/flavorbot module is properly installed.")
    st.stop()

# --------------------------
# BACKGROUND IMAGE FUNCTIONS - FIXED VERSION
# --------------------------
def get_base64_of_image(path):
    """Convert image to base64 string."""
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"Error loading background image: {e}")
        return None


def set_background_simple(image_path):
    """Simple working version with blurred background and visible content."""
    bin_str = get_base64_of_image(image_path)
    if bin_str is None:
        return

    css = f"""
    <style>
    .stApp {{
        background: url("data:image/png;base64,{bin_str}") no-repeat center center fixed;
        background-size: cover;
    }}

    /* MAIN APP CONTENT */
    [data-testid="stAppViewContainer"] > .main {{
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(4px);
        border-radius: 12px;
        padding: 2rem;
        margin: 1rem;
    }}

    /* SIDEBAR - FIXED: Proper rgba syntax */
    section[data-testid="stSidebar"] {{
        background: rgba(237, 206, 233, 0.9);
        backdrop-filter: blur(6px);
        border-radius: 8px;
    }}

    /* CHAT MESSAGE */
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 12px;
        border: 1px solid rgba(200, 200, 200, 0.3);
        padding: 1rem;
    }}

    /* CHAT INPUT */
    .stChatInput > div {{
        background: rgba(255, 255, 255, 0.95);
        border-radius: 10px;
        border: 1px solid rgba(200, 200, 200, 0.3);
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# --------------------------
# CONFIG
# --------------------------
st.set_page_config(page_title="FlavorBot", page_icon="🍲")

# --------------------------
# BACKGROUND SETUP 
# --------------------------

set_background_simple("background2.png")



st.title("🍲 FlavorBot - Smart Recipe Assistant")

# --------------------------
# FEEDBACK LOGGER
# --------------------------
def log_feedback(query, response, is_helpful, timestamp=None):
    """Log user feedback to CSV file with proper error handling."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        file_exists = os.path.isfile("feedback_log.csv")
        with open("feedback_log.csv", mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["timestamp", "query", "response", "feedback"])
            writer.writerow([timestamp, query, response, "👍" if is_helpful else "👎"])
    except Exception as e:
        st.error(f"Failed to log feedback: {str(e)}")

# --------------------------
# INITIALIZE SESSION STATE  
# --------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm FlavorBot. Tell me what ingredients you have and I'll suggest some recipes."}
    ]

if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = set()

# --------------------------
# SIDEBAR FILTERS
# --------------------------
st.sidebar.header("🍴 Recipe Filters")
diet = st.sidebar.selectbox("Diet", ["", "vegan", "vegetarian", "keto", "gluten-free"])
time = st.sidebar.selectbox("Prep Time", ["", "under 30 minutes", "under 1 hour"])
course = st.sidebar.selectbox("Course", ["", "breakfast", "lunch", "dinner", "dessert"])

# --------------------------
# CHAT DISPLAY
# --------------------------
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        if (msg["role"] == "assistant" and 
            i > 0 and  
            i not in st.session_state.feedback_submitted):

            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 Helpful", key=f"thumbs_up_{i}"):
                    user_query = st.session_state.messages[i-1]["content"] if i > 0 else "N/A"
                    log_feedback(user_query, msg["content"], True)
                    st.session_state.feedback_submitted.add(i)
                    st.success("Thanks for your feedback!")
                    st.rerun()

            with col2:
                if st.button("👎 Not helpful", key=f"thumbs_down_{i}"):
                    user_query = st.session_state.messages[i-1]["content"] if i > 0 else "N/A"
                    log_feedback(user_query, msg["content"], False)
                    st.session_state.feedback_submitted.add(i)
                    st.warning("Got it! We'll improve.")
                    st.rerun()

# --------------------------
# USER INPUT HANDLING
# --------------------------
if user_input := st.chat_input("What do you have in your fridge?"):
    # Build filter string
    filters = [f for f in [diet, time, course] if f]
    filter_str = ". ".join(filters)
    full_input = user_input
    if filter_str:
        full_input += f". Please filter recipes by: {filter_str}"

    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Get recent chat history for context
                chat_history = st.session_state.messages[-6:]
                response = run_flavorbot(full_input, chat_history=chat_history)
            except Exception as e:
                response = f"⚠️ Sorry, I encountered an error: {str(e)}. Please try again."
                st.error("FlavorBot encountered an issue. Please check your connection and try again.")

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Use experimental_rerun to avoid potential loops
        st.rerun()

# --------------------------
# SIDEBAR CONTROLS
# --------------------------
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Reset Conversation"):
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm FlavorBot. Tell me what ingredients you have and I'll suggest some recipes."}
    ]
    st.session_state.feedback_submitted = set()
    st.rerun()

st.sidebar.markdown(f"**Messages:** {len(st.session_state.messages)}")
st.sidebar.markdown(f"**Feedback given:** {len(st.session_state.feedback_submitted)}")
