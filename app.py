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
    prompt = f"Analyse ce diagnostic pour {chapter}. Crée un plan de 4 étapes avec des cases à cocher. Français Académique."
    return model.generate_content([prompt, str(history)]).text

def generate_resume(chapter):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Rédige un résumé structuré pour {chapter}. Utilise impérativement LaTeX ($$ ... $$) pour toutes les formules. Français Académique."
    return model.generate_content(prompt).text

def generate_series(chapter):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Génère une série de 3 exercices progressifs pour {chapter}. Utilise LaTeX ($$ ... $$) pour les calculs. Français Académique."
    return model.generate_content(prompt).text

# --- 3. NAVIGATION & UI ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")
st.sidebar.title("📚 KhirMinTaki")

# Reset Functionality
if st.sidebar.button("🔄 Réinitialiser la session"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Choisir un Chapitre", ["Sélectionner..."] + chapter_names)

# --- 4. DATA LOADING ---
if selected_chapter != "Sélectionner...":
    chapter_id = chapters_data.data[chapter_names.index(selected_chapter)]['id']
    existing = supabase.table("studying_plans").select("*").eq("chapter_id", chapter_id).execute()
    
    if existing.data:
        st.session_state.study_plan = existing.data[0].get('content')
        st.session_state.resume = existing.data[0].get('resume')
        st.session_state.series = existing.data[0].get('series')
    else:
        for key in ['study_plan', 'resume', 'series']:
            if key not in st.session_state: st.session_state[key] = None

if "messages" not in st.session_state: st.session_state.messages = []

# --- 5. PROGRESS & UI ---
if selected_chapter != "Sélectionner...":
    # Dynamic Progress Calculation
    score = 0
    if st.session_state.get('study_plan'): score += 30
    if st.session_state.get('resume'): score += 35
    if st.session_state.get('series'): score += 35
    
    st.write(f"### Progression : {score}%")
    st.progress(score / 100)
    
    tab1, tab2, tab3 = st.tabs(["📋 Diagnostic", "📝 Cours", "✍️ Exercices"])
    
    with tab1:
        if st.session_state.get('study_plan'):
            with st.expander("✅ Votre Plan d'Étude Personnalisé", expanded=True):
                st.markdown(st.session_state.study_plan)
        st.divider()
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"].replace("[PHASE_PLAN]", ""))

    with tab2:
        if st.session_state.get('resume'):
            st.markdown(st.session_state.resume)
        elif st.session_state.get('study_plan'):
            if st.button("Générer le Résumé (LaTeX)"):
                with st.spinner("Rédaction en cours..."):
                    content = generate_resume(selected_chapter)
                    supabase.table("studying_plans").update({"resume": content}).eq("chapter_id", chapter_id).execute()
                    st.session_state.resume = content
                    st.rerun()

    with tab3:
        if st.session_state.get('series'):
            st.markdown(st.session_state.series)
        elif st.session_state.get('resume'):
            if st.button("Générer la Série d'Exercices"):
                with st.spinner("Création des problèmes..."):
                    content = generate_series(selected_chapter)
                    supabase.table("studying_plans").update({"series": content}).eq("chapter_id", chapter_id).execute()
                    st.session_state.series = content
                    st.rerun()

    # Chat logic for Diagnostic
    if prompt := st.chat_input("Répondez au prof..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Prof de maths tunisien. Français Académique. Socratique. Termine par [PHASE_PLAN] après 3 questions.")
            chat = model.start_chat(history=[{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
            response = chat.send_message(prompt)
            st.markdown(response.text.replace("[PHASE_PLAN]", ""))
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            if "[PHASE_PLAN]" in response.text and not st.session_state.get('study_plan'):
                plan = generate_study_plan(st.session_state.messages, selected_chapter)
                supabase.table("studying_plans").insert({"chapter_id": chapter_id, "content": plan}).execute()
                st.session_state.study_plan = plan
                st.rerun()
else:
    st.title("KhirMinTaki")
    st.info("Sélectionnez un chapitre sur la gauche pour commencer votre diagnostic.")
