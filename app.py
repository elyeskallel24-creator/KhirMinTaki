import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client

# --- 1. SETUP CONNECTIONS ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Connection Error: Check if your Secrets are set up correctly!")

# --- 2. NAVIGATION & UI ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")
st.sidebar.title("📚 KhirMinTaki")
st.sidebar.subheader("Section Mathématiques")

# Fetch chapters from Supabase
chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Choisir un Chapitre", ["Sélectionner..."] + chapter_names)

# --- 3. STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_phase" not in st.session_state:
    st.session_state.current_phase = "assessment"

# --- 4. MAIN LOGIC ---
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
            # SYSTEM PROMPT: Updated with a Trigger for Phase 2
            system_prompt = f"""
            Tu es un professeur de mathématiques tunisien spécialisé dans le chapitre : {selected_chapter}.
            
            PHASE 1 : DIAGNOSTIC
            1. Salue l'élève et pose 3 questions de diagnostic (une par une) sur {selected_chapter}.
            2. Évalue ses réponses en français académique.
            
            PHASE 2 : TRANSITION
            Une fois que tu as posé les 3 questions et reçu les réponses, tu dois conclure le diagnostic.
            IMPORTANT : À la fin de ta dernière réponse de diagnostic, ajoute EXACTEMENT le texte suivant : [PHASE_PLAN]
            
            RÈGLES :
            - Langue : Français Académique.
            - Méthode : Socratique (ne pas donner de réponses directes).
            """
            
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_prompt)
            
            # Format history for Gemini
            history = []
            for m in st.session_state.messages[:-1]:
                history.append({"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]})
            
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(prompt)
            
            # Clean the response for display (hide the trigger tag from the student)
            display_text = response.text.replace("[PHASE_PLAN]", "")
            st.markdown(display_text)
            
            # Save the full response in history
            st.session_state.messages.append({"role": "assistant", "content": response.text})

            # THE SENSOR: Detecting if Phase 1 is over
            if "[PHASE_PLAN]" in response.text:
                st.success("Diagnostic terminé ! Préparation de votre plan d'étude personnalisé...")
                st.session_state.current_phase = "planning"
                st.info("Étape suivante : Génération du 'Studying Plan' dans la base de données.")

else:
    st.title("Bienvenue sur KhirMinTaki")
    st.write("L'excellence académique par l'IA. Sélectionnez un chapitre dans la barre latérale pour commencer.")
