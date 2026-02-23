import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client

# --- KEEP THIS: SETUP CONNECTIONS ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Connection Error: Check if your Secrets are set up correctly!")

# --- KEEP THIS: NAVIGATION ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")
st.sidebar.title("📚 KhirMinTaki")
st.sidebar.subheader("Mathematics Section")

# Fetch chapters
chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Choose a Chapter", ["Select..."] + chapter_names)

# --- REPLACE EVERYTHING BELOW THIS LINE WITH THE NEW LOGIC ---

if "messages" not in st.session_state:
    st.session_state.messages = []

if selected_chapter != "Select...":
    st.title(f"📖 {selected_chapter}")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("أكتب إجابتك هنا..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            system_prompt = f"""
            You are a specialized Tunisian Mathematics Tutor for the {selected_chapter} chapter.
            Your goal is to assess the student's level before creating a study plan.
            
            STRICT RULES:
            1. Language: You MUST speak in Tunisian Arabic (Derja) using the ARABIC ALPHABET ONLY. 
            2. Content: Use French for math terms (like 'complex numbers') but write them in Arabic script or French as per Tunisian classroom style.
            3. Method: Socratic method. Ask leading questions, no direct answers.
            4. Flow: Start with a warm Tunisian greeting, then ask 3 diagnostic questions one by one.
            """
            
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_prompt)
            
            history = []
            for m in st.session_state.messages[:-1]:
                history.append({"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]})
            
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
else:
    st.title("مرحباً بك في KhirMinTaki")
    st.write("أحسن من Taki Academy، بالذكاء الاصطناعي. اختار درس الرياضيات على اليسار باش نبدو.")
