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
    prompt = f"Rédige un résumé de cours structuré pour le chapitre : {chapter}. Inclus les formules clés en LaTeX. Français Académique."
    response = model.generate_content(prompt)
    return response.text

def generate_series(chapter):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Génère une série de 3 exercices d'application progressifs pour {chapter}. Utilise LaTeX. Français Académique."
    response = model.generate_content(prompt)
    return response.text

# --- 3. NAVIGATION & UI ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")
st.sidebar.title("📚 KhirMinTaki")

# Fetch chapters
chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Choisir un Chapitre", ["Sélectionner..."] + chapter_names)

# --- 4. STATE MANAGEMENT & DATABASE FETCH ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Logic to load existing data from Supabase if it exists
if selected_chapter != "Sélectionner...":
    # Try to find existing plan for this chapter
    existing = supabase.table("studying_plans").select("*").eq("chapter_id", chapters_data.data[chapter_names.index(selected_chapter)]['id']).execute()
    
    if existing.data:
        st.session_state.study_plan = existing.data[0].get('content')
        st.session_state.resume = existing.data[0].get('resume')
        st.session_state.series = existing.data[0].get('series')
    else:
        if "study_plan" not in st.session_state: st.session_state.study_plan = None
        if "resume" not in st.session_state: st.session_state.resume = None
        if "series" not in st.session_state: st.session_state.series = None

# --- 5. MAIN LOGIC ---
if selected_chapter != "Sélectionner...":
    st.title(f"📖 {selected_chapter}")
    
    tab1, tab2, tab3 = st.tabs(["📋 Plan & Diagnostic", "📝 Résumé", "✍️ Série"])
    
    with tab1:
        if st.session_state.get('study_plan'):
            with st.expander("✅ Votre Plan d'Étude", expanded=True):
                st.markdown(st.session_state.study_plan)
        st.divider()
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"].replace("[PHASE_PLAN]", ""))

    with tab2:
        if st.session_state.get('resume'):
            st.markdown(st.session_state.resume)
        elif st.session_state.get('study_plan'):
            if st.button("Générer le Résumé"):
                content = generate_resume(selected_chapter)
                # Update Supabase
                supabase.table("studying_plans").update({"resume": content}).eq("chapter_id", chapters_data.data[chapter_names.index(selected_chapter)]['id']).execute()
                st.session_state.resume = content
                st.rerun()

    with tab3:
        if st.session_state.get('series'):
            st.markdown(st.session_state.series)
        elif st.session_state.get('resume'):
            if st.button("Générer la Série"):
                content = generate_series(selected_chapter)
                # Update Supabase
                supabase.table("studying_plans").update({"series": content}).eq("chapter_id", chapters_data.data[chapter_names.index(selected_chapter)]['id']).execute()
                st.session_state.series = content
                st.rerun()

    # Chat Input
    if prompt := st.chat_input("Posez votre question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Prof de maths, Français Académique, Socratique. Fini par [PHASE_PLAN] après 3 questions.")
            chat = model.start_chat(history=[{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
            response = chat.send_message(prompt)
            st.markdown(response.text.replace("[PHASE_PLAN]", ""))
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            if "[PHASE_PLAN]" in response.text and not st.session_state.get('study_plan'):
                plan = generate_study_plan(st.session_state.messages, selected_chapter)
                # Save New Plan to Supabase
                chapter_id = chapters_data.data[chapter_names.index(selected_chapter)]['id']
                supabase.table("studying_plans").insert({"chapter_id": chapter_id, "content": plan}).execute()
                st.session_state.study_plan = plan
                st.rerun()
else:
    st.title("Bienvenue sur KhirMinTaki")
