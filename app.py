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

# --- 2. AI FUNCTIONS ---
def generate_study_plan(history, chapter):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Analyse ce diagnostic pour le chapitre {chapter}. Crée un plan d'étude de 4 étapes avec des cases à cocher (- [ ]). Français Académique."
    response = model.generate_content([prompt, str(history)])
    return response.text

def generate_resume(chapter):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Rédige un résumé de cours complet et structuré pour le chapitre de mathématiques : {chapter}. Inclus les formules clés et les définitions essentielles. Français Académique."
    response = model.generate_content(prompt)
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
if "resume" not in st.session_state:
    st.session_state.resume = None

# --- 5. MAIN LOGIC ---
if selected_chapter != "Sélectionner...":
    st.title(f"📖 {selected_chapter}")
    
    # UI Layout: Plan and Resume side-by-side
    col1, col2 = st.columns(2)
    
    if st.session_state.study_plan:
        with col1:
            with st.expander("✅ Plan d'Étude", expanded=True):
                st.markdown(st.session_state.study_plan)
    
    if st.session_state.study_plan and st.session_state.resume is None:
        if st.button("Générer le Résumé de Cours"):
            with st.spinner("Rédaction du résumé..."):
                st.session_state.resume = generate_resume(selected_chapter)
                st.rerun()

    if st.session_state.resume:
        with col2:
            with st.expander("📝 Résumé du Cours", expanded=True):
                st.markdown(st.session_state.resume)

    # Chat Display
    st.divider()
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"].replace("[PHASE_PLAN]", ""))

    # Chat Input
    if prompt := st.chat_input("Répondez au professeur..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            system_prompt = f"Tu es un professeur de maths pour {selected_chapter}. Pose 3 questions de diagnostic. À la fin de la 3ème, ajoute : [PHASE_PLAN]. Français Académique."
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_prompt)
            history = [{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]]
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(prompt)
            st.markdown(response.text.replace("[PHASE_PLAN]", ""))
            st.session_state.messages.append({"role": "assistant", "content": response.text})

            if "[PHASE_PLAN]" in response.text and st.session_state.study_plan is None:
                st.session_state.study_plan = generate_study_plan(st.session_state.messages, selected_chapter)
                st.rerun()
else:
    st.title("Bienvenue sur KhirMinTaki")
