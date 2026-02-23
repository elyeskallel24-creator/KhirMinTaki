import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client

# 1. Setup Connections using Streamlit Secrets
try:
    # AI Brains
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    
    # Database Vault
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Connection Error: Check if your Secrets are set up correctly!")

# 2. The Navigation (Mathematics Section)
st.set_page_config(page_title="KhirMinTaki", layout="wide")
st.sidebar.title("📚 KhirMinTaki")
st.sidebar.subheader("Mathematics Section")

# Fetch chapters from Supabase
chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]

selected_chapter = st.sidebar.selectbox("Choose a Chapter", ["Select..."] + chapter_names)

# 3. App Main Logic
if selected_chapter != "Select...":
    st.title(f"📖 Chapter: {selected_chapter}")
    st.info("The AI is ready to assess your level and create your studying plan.")
    
    # Placeholder for the next step: The Chatbot logic
    st.write("Click 'Start Session' to begin your AI diagnostic.")
    if st.button("Start Session"):
        st.session_state.current_phase = "assessment"
        st.rerun()
else:
    st.title("Welcome to KhirMinTaki")
    st.write("Better than Taki Academy, powered by AI. Select a math chapter on the left to start.")
