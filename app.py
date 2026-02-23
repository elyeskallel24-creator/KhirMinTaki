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

# FIX: Layout must be "centered" or "wide". We use "centered" for that clean AI feel.
st.set_page_config(page_title="KhirMinTaki", layout="centered")

# --- 2. THE LAYERED UI ENGINE (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    header, footer, [data-testid="stSidebar"] { visibility: hidden; }

    /* Minimal Floating Header */
    .app-header {
        position: fixed; top: 0; left: 0; width: 100%;
        background: rgba(255,255,255,0.95); backdrop-filter: blur(8px);
        padding: 12px 20px; border-bottom: 1px solid #f0f0f0;
        z-index: 1000; display: flex; justify-content: space-between; align-items: center;
    }
    
    .mastery-progress {
        position: fixed; top: 55px; left: 0; width: 100%; height: 3px;
        background: #f0f0f0; z-index: 1001;
    }
    .mastery-fill { height: 100%; background: #10a37f; transition: width 1s ease; }

    /* Input Styling */
    .stChatFloatingInputContainer { background: white !important; padding-bottom: 20px !important; }
    
    /* Center Fix */
    .block-container { padding-top: 80px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC: SESSION & AUTH ---
if "user_email" not in st.session_state:
    st.markdown("<div style='text-align:center; padding-top:50px;'><h1>KhirMinTaki</h1></div>", unsafe_allow_html=True)
    c1, mid, c2 = st.columns([1, 2, 1])
    with mid:
        email = st.text_input("Email", placeholder="ton-email@taki.com")
        if st.button("Commencer", use_container_width=True):
            if email:
                st.session_state.user_email = email
                st.rerun()
    st.stop()

# --- 4. NAVIGATION ---
try:
    chapters = supabase.table("chapters").select("*").execute().data
    chapter_names = [c['name'] for c in chapters]
except:
    st.error("Connection error")
    st.stop()

# Header Display
mastery_pct = 45 
st.markdown(f"""
    <div class="app-header">
        <span style="font-weight:700; font-size:16px;">KhirMinTaki</span>
        <span style="color:#10a37f; font-weight:700; font-size:14px;">Mastery: {mastery_pct}%</span>
    </div>
    <div class="mastery-progress"><div class="mastery-fill" style="width:{mastery_pct}%;"></div></div>
""", unsafe_allow_html=True)

sel_chap = st.selectbox("Chapitre", ["Choisir un chapitre..."] + chapter_names, label_visibility="collapsed")

# --- 5. THE CONVERSATION ---
if sel_chap == "Choisir un chapitre...":
    st.markdown("<div style='text-align:center; padding-top:10vh;'><h2 style='color:#ccc;'>Bienvenue. Quel chapitre allons-nous maîtriser aujourd'hui ?</h2></div>", unsafe_allow_html=True)
else:
    chapter_id = next(c['id'] for c in chapters if c['name'] == sel_chap)
    
    # DB Session Sync
    sess_res = supabase.table("student_sessions").select("*").eq("user_email", st.session_state.user_email).eq("chapter_id", chapter_id).execute()
    if not sess_res.data:
        supabase.table("student_sessions").insert({"user_email": st.session_state.user_email, "chapter_id": chapter_id, "phase": "assessment"}).execute()
        st.rerun()
    curr_sess = sess_res.data[0]

    if "messages" not in st.session_state or st.session_state.get("last_chap") != sel_chap:
        st.session_state.messages = [{"role": "assistant", "content": f"Asslema! On commence **{sel_chap}**. Quel est ton niveau actuel ?"}]
        st.session_state.last_chap = sel_chap

    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "[PLAN_READY]" in msg["content"]:
                with st.expander("📂 Voir mon Plan d'étude & Résumé", expanded=True):
                    t1, t2 = st.tabs(["Plan", "Résumé"])
                    t1.write(curr_sess.get('study_plan', 'Analyse en cours...'))
                    t2.write(curr_sess.get('course_resume', 'S\'ajoutera bientôt.'))

    # Input Logic
    if prompt := st.chat_input("Réponds ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                # Using Groq/Llama for speed, Gemini as fallback
                chat_completion = groq_client.chat.completions.create(
                    messages=[{"role": "system", "content": "Tu es un tuteur expert tunisien. Utilise LaTeX. Si l'évaluation est finie, ajoute [PLAN_READY] à la fin."}] + st.session_state.messages[-5:],
                    model="llama-3.3-70b-versatile",
                )
                response = chat_completion.choices[0].message.content
            except:
                response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt).text
            
            st.markdown(response.replace("[PLAN_READY]", ""))
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            if "[PLAN_READY]" in response:
                supabase.table("student_sessions").update({"study_plan": response, "phase": "learning"}).eq("id", curr_sess["id"]).execute()
                st.rerun()
