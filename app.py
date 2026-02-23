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

st.set_page_config(page_title="KhirMinTaki", layout="tight")

# --- 2. THE LAYERED UI ENGINE (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    header, footer, [data-testid="stSidebar"] { visibility: hidden; }

    /* The Centered Column */
    .main-column { max-width: 750px; margin: 0 auto; padding: 20px; }

    /* Minimal Floating Header */
    .app-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(255,255,255,0.95); backdrop-filter: blur(8px);
        padding: 12px 20px; border-bottom: 1px solid #f0f0f0;
        z-index: 1000; display: flex; justify-content: space-between; align-items: center;
    }
    
    .mastery-progress {
        position: fixed; top: 50px; left: 0; width: 100%; height: 3px;
        background: #f0f0f0; z-index: 1001;
    }
    .mastery-fill { height: 100%; background: #10a37f; transition: width 1s ease; }

    /* Magic Cards (In-Chat UI) */
    .magic-card {
        background: #f9f9f9; border: 1px solid #eee; border-radius: 12px;
        padding: 20px; margin: 15px 0; border-left: 4px solid #10a37f;
    }

    /* Input Styling */
    .stChatFloatingInputContainer { background: white !important; padding-bottom: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC: SESSION & AUTH ---
if "user_email" not in st.session_state:
    st.markdown("<div style='text-align:center; padding-top:100px;'><h1>KhirMinTaki</h1>", unsafe_allow_html=True)
    c1, mid, c2 = st.columns([1, 2, 1])
    with mid:
        email = st.text_input("Email", placeholder="ton-email@taki.com")
        if st.button("Commencer", use_container_width=True):
            if email:
                st.session_state.user_email = email
                st.rerun()
    st.stop()

# --- 4. NAVIGATION (MODERN TOP MENU) ---
try:
    chapters = supabase.table("chapters").select("*").execute().data
    chapter_names = [c['name'] for c in chapters]
except:
    st.error("Connection error")
    st.stop()

# Minimal Header
mastery_pct = 45 # Dynamic value
st.markdown(f"""
    <div class="app-header">
        <span style="font-weight:700; font-size:16px;">KhirMinTaki</span>
        <span style="color:#10a37f; font-weight:700; font-size:14px;">Mastery: {mastery_pct}%</span>
    </div>
    <div class="mastery-progress"><div class="mastery-fill" style="width:{mastery_pct}%;"></div></div>
    <div style="height:70px;"></div>
""", unsafe_allow_html=True)

# Chapter Picker (Clean Dropdown)
sel_chap = st.selectbox("Chapitre actuel", ["Choisir un chapitre..."] + chapter_names, label_visibility="collapsed")

# --- 5. THE CONVERSATION (THE PRODUCT) ---
if sel_chap == "Choisir un chapitre...":
    st.markdown("<div style='text-align:center; padding-top:10vh;'><h2 style='color:#ccc;'>Bienvenue. Quel chapitre allons-nous maîtriser aujourd'hui ?</h2></div>", unsafe_allow_html=True)
else:
    chapter_id = next(c['id'] for c in chapters if c['name'] == sel_chap)
    
    # Load Database Session
    sess_res = supabase.table("student_sessions").select("*").eq("user_email", st.session_state.user_email).eq("chapter_id", chapter_id).execute()
    if not sess_res.data:
        supabase.table("student_sessions").insert({"user_email": st.session_state.user_email, "chapter_id": chapter_id, "phase": "assessment"}).execute()
        st.rerun()
    curr_sess = sess_res.data[0]

    # Initialize Messages
    if "messages" not in st.session_state or st.session_state.get("last_chap") != sel_chap:
        st.session_state.messages = [{"role": "assistant", "content": f"Asslema! On commence **{sel_chap}**. Avant de plonger dans le cours, dis-moi ce que tu sais déjà sur ce sujet ?"}]
        st.session_state.last_chap = sel_chap

    # Display Chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # Display "Magic Cards" if plan exists
            if "[PLAN_READY]" in msg["content"]:
                with st.expander("📂 Voir mon Plan d'étude & Résumé"):
                    t1, t2 = st.tabs(["Plan", "Résumé"])
                    t1.write(curr_sess.get('study_plan', 'Génération...'))
                    t2.write(curr_sess.get('course_resume', 'S\'ajoutera au fur et à mesure.'))

    # Input Area
    if prompt := st.chat_input("Réponds ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
        
        # (AI Logic would happen here in a real run)
