import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
from fpdf import FPDF

# --- 1. SETUP CONNECTIONS ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Connection Error: Check Secrets.")

# --- 2. ULTRA MINIMALIST CSS ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #000000; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #f0f0f0; }
    [data-testid="stSidebar"] * { color: #000000 !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    h1, h2, h3 { font-weight: 400 !important; }
    .stChatInputContainer { border-top: 1px solid #f0f0f0 !important; }
    .stChatMessage { border: none !important; background: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIN GATE ---
if "user_email" not in st.session_state:
    st.write("### **KhirMinTaki**")
    st.write("Bienvenue. Veuillez entrer votre email pour accéder à votre espace d'apprentissage.")
    
    email_input = st.text_input("Email", placeholder="exemple@email.com")
    if st.button("Commencer"):
        if email_input:
            st.session_state.user_email = email_input
            st.rerun()
        else:
            st.error("Veuillez entrer un email valide.")
    st.stop() 

# --- 4. NAVIGATION & LOGOUT ---
st.sidebar.markdown("### **KhirMinTaki**") 
st.sidebar.write(f"Utilisateur: {st.session_state.user_email}")

if st.sidebar.button("Déconnexion"):
    del st.session_state.user_email
    st.rerun()

chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Chapitres", ["Sélectionner..."] + chapter_names)

# Fetch stats ONLY for this user
num_mastered = 0
try:
    all_sessions = supabase.table("student_sessions").select("id").eq("user_email", st.session_state.user_email).execute()
    num_mastered = len(all_sessions.data)
except:
    num_mastered = 0

# --- 5. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    st.write("### **Bienvenue**") 
    st.write("Sélectionnez un module pour commencer votre session d'apprentissage.")
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("Niveau")
        st.write(f"**{'Expert' if num_mastered > 2 else 'Apprenti'}**")
    with c2:
        st.write("Progression")
        st.write(f"**{num_mastered} chapitres**")
    with c3:
        st.write("Total Points")
        st.write(f"**{num_mastered * 100}**")

else:
    chapter_id = chapters_data.data[chapter_names.index(selected_chapter)]['id']
    
    # Filter by user_email so students don't see each other's plans
    existing = supabase.table("student_sessions").select("*").eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).execute()
    
    if "messages" not in st.session_state: st.session_state.messages = []
    
    if existing.data:
        st.session_state.study_plan = existing.data[0].get('study_plan')
        st.session_state.resume = existing.data[0].get('course_resume')
    else:
        st.session_state.study_plan = st.session_state.get('study_plan', None)
        st.session_state.resume = st.session_state.get('resume', None)

    st.write(f"## {selected_chapter}")
    tab1, tab2 = st.tabs(["Conversation", "Documents"])
    
    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"].replace("[PHASE_PLAN]", ""))
        
        if prompt := st.chat_input("..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Tuteur de maths. Style minimaliste. Pas d'emojis. Utilise LaTeX.")
                chat = model.start_chat(history=[{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
                response = chat.send_message(prompt)
                st.markdown(response.text.replace("[PHASE_PLAN]", ""))
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                if "[PHASE_PLAN]" in response.text and not st.session_state.get('study_plan'):
                    plan_prompt = f"Génère un plan d'étude pour {selected_chapter}."
                    plan = genai.GenerativeModel("gemini-1.5-flash").generate_content(plan_prompt).text
                    # IMPORTANT: Save with user_email
                    supabase.table("student_sessions").insert({
                        "chapter_id": chapter_id, 
                        "study_plan": plan,
                        "user_email": st.session_state.user_email
                    }).execute()
                    st.session_state.study_plan = plan
                    st.rerun()

    with tab2:
        if st.session_state.get('study_plan'):
            st.write("### Plan d'étude")
            st.markdown(st.session_state.study_plan)
            if st.session_state.get('resume'):
                st.divider()
                st.write("### Résumé")
                st.markdown(st.session_state.resume)
            else:
                if st.button("Générer le résumé"):
                    res_prompt = f"Résumé LaTeX pour {selected_chapter}."
                    content = genai.GenerativeModel("gemini-1.5-flash").generate_content(res_prompt).text
                    supabase.table("student_sessions").update({"course_resume": content}).eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).execute()
                    st.session_state.resume = content
                    st.rerun()
