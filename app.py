import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client

# --- SETUP CONNECTIONS ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Connection Error: Check if your Secrets are set up correctly!")

# --- NAVIGATION & UI ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")
st.sidebar.title("📚 KhirMinTaki")
st.sidebar.subheader("Section Mathématiques")

# Fetch chapters from Supabase
chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Choisir un Chapitre", ["Sélectionner..."] + chapter_names)

# --- STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- MAIN LOGIC ---
if selected_chapter != "Sélectionner...":
    st.title(f"📖 Chapitre : {selected_chapter}")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Posez votre question ou répondez ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # SYSTEM PROMPT: Formal Academic French Tutor
            system_prompt = f"""
            Tu es un professeur de mathématiques tunisien spécialisé dans le chapitre : {selected_chapter}.
            Ton objectif est d'évaluer le niveau de l'élève avant de créer un plan d'étude.
            
            RÈGLES STRICTES :
            1. Langue : Tu dois t'exprimer exclusivement en FRANÇAIS ACADÉMIQUE formel (niveau Lycée/Baccalauréat).
            2. Méthode Socratique : Ne donne jamais la réponse directement. Guide l'élève par des questions pertinentes.
            3. Déroulement : 
               - Commence par saluer l'élève formellement.
               - Pose 3 questions de diagnostic, une par une, pour tester ses prérequis sur le chapitre {selected_chapter}.
            4. Ton : Professionnel, encourageant et rigoureux.
            """
            
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_prompt)
            
            # Format history for Gemini
            history = []
            for m in st.session_state.messages[:-1]:
                history.append({"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]})
            
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(prompt)
            st.markdown(response.text)
            
            # Add assistant response to history
            st.session_state.messages.append({"role": "assistant", "content": response.text})
else:
    st.title("Bienvenue sur KhirMinTaki")
    st.write("L'excellence académique par l'IA. Sélectionnez un chapitre dans la barre latérale pour commencer.")
