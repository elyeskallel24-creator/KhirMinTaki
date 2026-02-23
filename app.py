import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
import streamlit.components.v1 as components

# --- 1. SETUP ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Configuration Error: {e}")

# --- 2. STYLE & BRANDING (MODERN DARK/LIGHT HYBRID) ---
st.set_page_config(page_title="KhirMinTaki", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Main Chat Container */
    .stChatFloatingInputContainer { background-color: white; border-top: 1px solid #f0f0f0; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #e0e0e0;
        min-width: 300px !important;
    }
    
    /* Header removal for clean look */
    #MainMenu, footer, header {visibility: hidden;}
    
    .sidebar-title { font-size: 20px; font-weight: 800; margin-bottom: 20px; color: #1a1a1a; }
    .nav-label { font-size: 14px; font-weight: 600; color: #666; margin-top: 15px; text-transform: uppercase; }
    .status-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #eee; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if "user_email" not in st.session_state:
    st.markdown("<h1 style='text-align: center; margin-top: 50px;'>KhirMinTaki</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        email = st.text_input("Email", placeholder="votre@email.com")
        if st.button("Se connecter", use_container_width=True):
            if email:
                st.session_state.user_email = email
                try: supabase.table("users").upsert({"email": email}).execute()
                except: pass
                st.rerun()
    st.stop()

# --- 4. SIDEBAR (THE "CHATGPT" STYLE NAVIGATION) ---
with st.sidebar:
    st.markdown("<div class='sidebar-title'>KhirMinTaki</div>", unsafe_allow_html=True)
    
    # 1. Chapter Selection
    try:
        chapters = supabase.table("chapters").select("*").execute().data
        names = [c['name'] for c in chapters]
        sel_chap = st.selectbox("📚 Cours", ["Sélectionner..."] + names)
    except:
        st.error("Base de données indisponible.")
        st.stop()
    
    if sel_chap != "Sélectionner...":
        chapter_id = next(c['id'] for c in chapters if c['name'] == sel_chap)
        session_res = supabase.table("student_sessions").select("*").eq("user_email", st.session_state.user_email).eq("chapter_id", chapter_id).execute()
        
        if not session_res.data:
            supabase.table("student_sessions").insert({"user_email": st.session_state.user_email, "chapter_id": chapter_id, "phase": "assessment"}).execute()
            st.rerun()
        
        curr_session = session_res.data[0]
        
        # 2. Progress Tracker
        st.markdown("<div class='nav-label'>Progression</div>", unsafe_allow_html=True)
        phase_map = {"assessment": "Évaluation", "learning": "Apprentissage", "mastery": "Maîtrise"}
        st.markdown(f"<div class='status-card'>Phase: <b>{phase_map.get(curr_session['phase'], 'Début')}</b></div>", unsafe_allow_html=True)
        
        # 3. Subsections (Study Plan, Resume, etc.)
        st.markdown("<div class='nav-label'>Bibliothèque</div>", unsafe_allow_html=True)
        
        with st.expander("📅 Studying Plan"):
            st.write(curr_session.get('study_plan') or "En attente...")
            
        with st.expander("📝 Course Resume"):
            st.write(curr_session.get('course_resume') or "En cours de création...")

        with st.expander("✍️ Notes & Remarques"):
            st.write(curr_session.get('notes') or "Notes à venir.")

    st.markdown("---")
    if st.button("Log Out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 5. MAIN CHAT AREA ---
if sel_chap == "Sélectionner...":
    st.write(f"## **Asslema, {st.session_state.user_email.split('@')[0].capitalize()} !**")
    st.info("Utilise la barre latérale à gauche pour choisir un chapitre et commencer ton tutorat.")
else:
    st.write(f"### Tutorat : {sel_chap}")
    
    # Chat Logic
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": f"Asslema! Je suis ton tuteur expert pour {sel_chap}. Commençons par évaluer tes bases. Quel est ton niveau actuel ?"}]
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    
    if prompt := st.chat_input("Pose ta question ou réponds au tuteur..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            phase = curr_session.get('phase', 'assessment')
            sys_prompt = f"Tu es un tuteur expert tunisien. Phase: {phase}. Utilise LaTeX. Si tu as assez d'infos pour le plan d'étude, finis par [GENERATE_PLAN]."
            
            try:
                chat = groq_client.chat.completions.create(
                    messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages[-5:],
                    model="llama-3.3-70b-versatile",
                )
                res_text = chat.choices[0].message.content
            except:
                model = genai.GenerativeModel("gemini-1.5-flash")
                res_text = model.generate_content(prompt).text

            st.markdown(res_text.replace("[GENERATE_PLAN]", ""))
            st.session_state.messages.append({"role": "assistant", "content": res_text})

            # Handle DB Updates
            if "[GENERATE_PLAN]" in res_text:
                supabase.table("student_sessions").update({"study_plan": res_text, "phase": "learning"}).eq("id", curr_session['id']).execute()
                st.toast("Studying Plan mis à jour dans la barre latérale !")
