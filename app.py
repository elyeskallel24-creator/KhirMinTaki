import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client

# --- 1. CORE SETUP ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Configuration Error: {e}")

st.set_page_config(page_title="KhirMinTaki", layout="centered")

# --- 2. CLEAN AI-NATIVE CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    header, footer, [data-testid="stSidebar"] { visibility: hidden; }

    /* Centered UI */
    .main-container { max-width: 700px; margin: 0 auto; padding-top: 50px; }
    
    /* Fixed Mastery Header */
    .mastery-header {
        position: fixed; top: 0; left: 0; width: 100%; background: white;
        padding: 15px 20px; border-bottom: 1px solid #f0f0f0; z-index: 1000;
        display: flex; justify-content: space-between; align-items: center;
    }
    .progress-bar-bg { position: fixed; top: 55px; left: 0; width: 100%; height: 3px; background: #f0f0f0; z-index: 1001; }
    .progress-bar-fill { height: 100%; background: #10a37f; transition: width 0.8s ease; }

    /* Interactive Cards */
    .subject-card {
        padding: 30px; border: 1px solid #eee; border-radius: 15px; 
        text-align: center; cursor: pointer; transition: 0.3s;
    }
    .subject-card:hover { border-color: #10a37f; background: #f9fbf9; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. WORKFLOW CONTROLLER ---
if "view" not in st.session_state: st.session_state.view = "dashboard"

# --- VIEW 1: SUBJECT DASHBOARD ---
if st.session_state.view == "dashboard":
    st.markdown("<div style='text-align:center; padding-top:100px;'><h1>KhirMinTaki</h1><p>Choose a subject to begin</p></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='subject-card'><h2>📐</h2><h3>Mathematics</h3></div>", unsafe_allow_html=True)
        if st.button("Open Mathematics", use_container_width=True):
            st.session_state.selected_subject = "Mathematics"
            st.session_state.view = "chapters"
            st.rerun()

# --- VIEW 2: CHAPTER LIST ---
elif st.session_state.view == "chapters":
    st.button("← Back", on_click=lambda: st.session_state.update({"view": "dashboard"}))
    st.markdown(f"## {st.session_state.selected_subject} Chapters")
    try:
        chapters = supabase.table("chapters").select("*").execute().data
        for ch in chapters:
            if st.button(f"💬 {ch['name']}", use_container_width=True):
                st.session_state.current_chapter = ch['name']
                st.session_state.chapter_id = ch['id']
                st.session_state.view = "chat"
                st.session_state.messages = []
                st.rerun()
    except: st.error("Database unavailable.")

# --- VIEW 3: THE LEARNING WORKSPACE ---
elif st.session_state.view == "chat":
    # Header
    st.markdown(f"""
        <div class="mastery-header">
            <span style="font-weight:700;">{st.session_state.current_chapter}</span>
            <span style="color:#10a37f; font-weight:700;">Mastery: 0%</span>
        </div>
        <div class="progress-bar-bg"><div class="progress-bar-fill" style="width:5%;"></div></div>
    """, unsafe_allow_html=True)
    
    # Session Persistence
    res = supabase.table("student_sessions").select("*").eq("chapter_id", st.session_state.chapter_id).execute()
    curr_sess = res.data[0] if res.data else {"phase": "assessment", "study_plan": None, "course_resume": None}

    # Shadow Infrastructure (The Drawer)
    with st.expander("📚 Study Records (Plan, Resume, Exercises)"):
        tab1, tab2, tab3, tab4 = st.tabs(["Study Plan", "Course Resume", "Exercises", "Notes"])
        tab1.write(curr_sess.get('study_plan') or "AI is building this based on your chat...")
        tab2.write(curr_sess.get('course_resume') or "Key concepts will appear here as we go.")
        tab3.write("Exercise history will be stored here.")
        tab4.write("Personalized remarks and hints tailored for you.")

    # Chat Logic
    if not st.session_state.messages:
        st.session_state.messages = [{"role": "assistant", "content": f"Asslema! Let's master **{st.session_state.current_chapter}**. To start, what's your current level with this topic?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Answer the tutor..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            sys_msg = f"Tunisian Math Tutor. Phase: {curr_sess['phase']}. If you have enough info, write [GENERATE_PLAN]. If teaching, write [UPDATE_RESUME]."
            try:
                response = groq_client.chat.completions.create(
                    messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:],
                    model="llama-3.3-70b-versatile"
                ).choices[0].message.content
            except:
                response = "Désolé, j'ai eu un petit problème technique. Peux-tu répéter ?"
            
            st.markdown(response.replace("[GENERATE_PLAN]", "").replace("[UPDATE_RESUME]", ""))
            st.session_state.messages.append({"role": "assistant", "content": response})

            # Update Hidden Infrastructure
            if "[GENERATE_PLAN]" in response:
                supabase.table("student_sessions").upsert({
                    "chapter_id": st.session_state.chapter_id,
                    "study_plan": response,
                    "phase": "teaching"
                }).execute()
                st.toast("Studying Plan Created!")
