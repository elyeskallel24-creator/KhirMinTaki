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

# --- 2. THE PLANNING FUNCTION ---
def generate_study_plan(history, chapter):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    En tant que professeur expert, analyse cette conversation de diagnostic pour le chapitre {chapter}.
    Crée un 'Studying Plan' personnalisé en 4 étapes clés.
    Chaque étape doit être concise et adaptée au niveau montré par l'élève.
    Formatte le résultat en Markdown avec des cases à cocher (- [ ]).
    Langue : Français Académique.
    """
    response = model.generate_content([prompt, str(history)])
    return response.text

# --- 3. NAVIGATION & UI ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")
st.sidebar.title("📚 KhirMinTaki")
st.sidebar.subheader("Section Mathématiques")

chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Choisir un Chapitre", ["Sélectionner..."] + chapter_names)

# --- 4. STATE MANAGEMENT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "study_plan" not in st.session_state:
    st.session_state.study_plan = None

# --- 5. MAIN LOGIC ---
if selected_chapter != "Sélectionner...":
    st.title(f"📖 Chapitre : {selected_chapter}")
    
    # If a study plan exists, show it at the top
    if st.session_state.study_plan:
        with st.expander("✅ Votre Plan d'Étude Personnalisé", expanded=True):
            st.markdown(st.session_state.study_plan)

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"].replace("[PHASE_PLAN]", ""))

    # Chat Input
    if prompt := st.chat_input("Répondez au professeur..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            system_prompt = f"""
            Tu es un professeur de mathématiques tunisien pour le chapitre : {selected_chapter}.
            Pose 3 questions de diagnostic une par une. 
            À la fin de la 3ème réponse, ajoute impérativement : [PHASE_PLAN]
            Langue : Français Académique.
            """
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_prompt)
            
            history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(prompt)
            
            st.markdown(response.text.replace("[PHASE_PLAN]", ""))
            st.session_state.messages.append({"role": "assistant", "content": response.text})

            # TRIGGER: Generate Plan if tag is detected
            if "[PHASE_PLAN]" in response.text and st.session_state.study_plan is None:
                with st.spinner("Génération de votre plan d'étude..."):
                    plan = generate_study_plan(st.session_state.messages, selected_chapter)
                    st.session_state.study_plan = plan
                    st.rerun()

else:
    st.title("Bienvenue sur KhirMinTaki")
    st.write("Sélectionnez un chapitre pour commencer votre évaluation.")
