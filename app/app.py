import sys
import os
import streamlit as st

# Add "src/" to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# ✅ Correct import after updating sys.path
from agents.flavorbot import run_flavorbot

st.set_page_config(page_title="FlavorBot", page_icon="🍲")

st.title("🍲 FlavorBot")
st.markdown("**Ask me what you can cook with ingredients!**")
st.markdown("_Example: 'What can I cook with lentils and spinach?'_")

# Chat input
user_input = st.text_input("Your ingredients or question:", placeholder="e.g. What can I make with garlic and mushrooms?")

if user_input:
    with st.spinner("Finding tasty ideas..."):
        try:
            response = run_flavorbot(user_input)
            st.success("Here's what I found:")
            st.markdown(response)
        except Exception as e:
            st.error(f"Error: {str(e)}")
