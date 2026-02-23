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
    prompt = f"Rédige un résumé de cours structuré pour le chapitre : {chapter}. Inclus les formules clés en LaTeX (ex: $$x^2$$). Français Académique."
    response = model.generate_content(prompt)
    return response.text

def generate_series(chapter):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Génère une série de 3 exercices d'application progressifs pour {chapter}. Utilise LaTeX. Français Académique."
    response = model.generate_content(prompt)
    return response.text

def generate_correction(series, chapter):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Donne la correction détaillée de cette série d'exercices pour le chapitre {chapter} : {series}. Explique chaque étape. Utilise LaTeX. Français Académique."
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
if "series" not in st.session_state:
    st.session_state.series = None
if "correction" not in st.session_state:
    st.session_state.correction = None

# --- 5. MAIN LOGIC ---
if selected_chapter != "Sélectionner...":
    st.title(f"📖 {selected_chapter}")
    
    tab1, tab2, tab3 = st.tabs(["📋 Plan & Diagnostic", "📝 Résumé", "✍️ Série & Correction"])
    
    with tab1:
        if st.session_state.study_plan:
            with st.expander("Voir le Plan d'Étude", expanded=True):
                st.markdown(st.session_state.study_plan)
        st.divider()
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"].replace("[PHASE_PLAN]", ""))

    with tab2:
        if st.session_state.resume:
            st.markdown(st.session_state.resume)
        elif st.session_state.study_plan:
            if st.button("Générer le Résumé"):
                with st.spinner("Rédaction..."):
                    st.session_state.resume = generate_resume(selected_chapter)
                    st.rerun()

    with tab3:
        if st.session_state.series:
            st.markdown("### Exercices")
            st.markdown(st.session_state.series)
            st.divider()
            if st.session_state.correction:
                st.markdown("### Correction Détaillée")
                st.markdown(st.session_state.correction)
            else:
                if st.button("Afficher la Correction"):
                    with st.spinner("Calcul de la correction..."):
                        st.session_state.correction = generate_correction(st.session_state.series, selected_chapter)
                        st.rerun()
        elif st.session_state.resume:
            if st.button("Générer la Série"):
                with st.spinner("Création..."):
                    st.session_state.series = generate_series(selected_chapter)
                    st.rerun()

    # Chat Input
    if prompt := st.chat_input("Posez une question ou soumettez une réponse..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            # Context-Aware System Prompt
            context = "Diagnostic" if st.session_state.study_plan is None else "Support/Correction"
            system_prompt = f"""
            Tu es un professeur de maths tunisien. Phase actuelle : {context}.
            Si Phase=Diagnostic: Pose 3 questions, fini par [PHASE_PLAN].
            Si Phase=Support: Aide l'élève sur le résumé ou la série d'exercices. Ne donne pas la réponse direct, guide-le.
            Langue : Français Académique. LaTeX pour maths.
            """
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
