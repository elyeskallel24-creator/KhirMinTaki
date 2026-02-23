import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
import streamlit.components.v1 as components

# --- 1. CORE SETUP ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"System Error: {e}")

st.set_page_config(page_title="KhirMinTaki Workspace", layout="wide", initial_sidebar_state="collapsed")

# --- 2. THE MASTER ARCHITECTURE (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* 100% Accuracy Layout Engine */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"], header, footer { display: none !important; }

    /* Three-Column Grid */
    .workspace-container {
        display: grid;
        grid-template-columns: 260px 1fr 320px;
        height: 100vh;
        overflow: hidden;
    }

    /* Left Sidebar: Curriculum */
    .left-nav {
        background-color: #f9f9f9;
        border-right: 1px solid #efefef;
        padding: 20px 15px;
        display: flex;
        flex-direction: column;
    }

    /* Central Workspace: Chat */
    .central-chat {
        background-color: #ffffff;
        display: flex;
        flex-direction: column;
        padding: 0 40px;
        overflow-y: auto;
    }

    /* Right Panel: Academic Persistence */
    .right-academic {
        background-color: #ffffff;
        border-left: 1px solid #efefef;
        padding: 20px;
        overflow-y: auto;
    }

    /* Mastery Progress UI */
    .mastery-ring {
        width: 40px; height: 40px;
        border-radius: 50%;
        border: 3px solid #f0f0f0;
        border-top: 3px solid #10a37f;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 10px; font-weight: 800;
    }

    /* Message Blocks */
    .stChatMessage { border: none !important; margin-bottom: 20px !important; }
    
    /* Persistent Tabs */
    .academic-tab {
        font-size: 12px; font-weight: 600; color: #666;
        padding: 8px 12px; border-radius: 6px;
        cursor: pointer; margin-bottom: 10px;
        transition: all 0.2s;
        border: 1px solid transparent;
    }
    .academic-tab:hover { background: #f0f0f0; }
    .active-tab { background: #f0f0f0; border-color: #ddd; color: #000; }

    /* Theorem/Formula Boxes */
    .formula-box {
        background: #f7f7f8; border-left: 4px solid #10a37f;
        padding: 15px; border-radius: 0 8px 8px 0; margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION & DASHBOARD VIEW ---
if "user_email" not in st.session_state:
    st.markdown("<div style='text-align:center; padding-top:100px;'><h1>KhirMinTaki</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        email = st.text_input("Email Student", placeholder="email@taki.com")
        if st.button("Resume Activity", use_container_width=True):
            if email:
                st.session_state.user_email = email
                supabase.table("users").upsert({"email": email}).execute()
                st.rerun()
    st.stop()

# --- 4. SUBJECT SELECTOR (DASHBOARD CARDS) ---
if "selected_subject" not in st.session_state:
    st.markdown("### Subject Workspace")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style='padding:30px; border:1px solid #eee; border-radius:15px; cursor:pointer;'>
            <h3>Mathematics</h3>
            <div class='mastery-ring'>72%</div>
            <p style='color:#666; font-size:13px;'>Last activity: Today, 10:20</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Enter Mathematics", use_container_width=True):
            st.session_state.selected_subject = "Mathematics"
            st.rerun()
    st.stop()

# --- 5. THE THREE-COLUMN WORKSPACE ---
try:
    chapters = supabase.table("chapters").select("*").execute().data
except:
    st.error("Connection lost.")
    st.stop()

# We use Streamlit columns to simulate the 3-column architecture
left_col, center_col, right_col = st.columns([1, 2.5, 1.5])

# --- LEFT SIDEBAR: CURRICULUM HIERARCHY ---
with left_col:
    st.markdown("<h4 style='font-weight:800;'>Curriculum</h4>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:12px; color:#888;'>SUBJECT: MATHEMATICS</p>", unsafe_allow_html=True)
    
    for ch in chapters:
        is_selected = st.session_state.get("current_chapter") == ch['name']
        btn_label = f"{ch['name']}"
        if st.button(btn_label, use_container_width=True, type="secondary" if not is_selected else "primary"):
            st.session_state.current_chapter = ch['name']
            st.session_state.chapter_id = ch['id']
            st.rerun()

    st.divider()
    if st.button("Log Out"):
        st.session_state.clear()
        st.rerun()

# --- CENTRAL: CONVERSATIONAL TUTOR ---
with center_col:
    if "current_chapter" not in st.session_state:
        st.markdown("<div style='height:20vh;'></div>", unsafe_allow_html=True)
        st.info("Select a chapter from the curriculum tree to begin your Diagnostic Phase.")
    else:
        # Chapter Header
        st.markdown(f"""
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2 style='margin:0;'>{st.session_state.current_chapter}</h2>
                <span style='background:#e7f5ff; color:#007bff; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:700;'>Diagnosing Phase</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Load Session Data
        sess = supabase.table("student_sessions").select("*").eq("user_email", st.session_state.user_email).eq("chapter_id", st.session_state.chapter_id).execute()
        if not sess.data:
            supabase.table("student_sessions").insert({"user_email": st.session_state.user_email, "chapter_id": st.session_state.chapter_id, "phase": "assessment"}).execute()
            st.rerun()
        
        curr_sess = sess.data[0]
        
        # Chat Messages
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": f"Asslema! I'm ready to teach you **{st.session_state.current_chapter}**. Let's start the diagnostic. How confident do you feel about the prerequisites?"}]
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Message AI Tutor..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                sys_prompt = f"Expert Tunisian Tutor. Current Phase: {curr_sess['phase']}. Use LaTeX. If assessment is done, end with [GENERATE_PLAN]. If teaching, end with [UPDATE_RESUME]."
                try:
                    chat = groq_client.chat.completions.create(
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages[-5:],
                        model="llama-3.3-70b-versatile",
                    )
                    res_text = chat.choices[0].message.content
                except:
                    res_text = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt).text
                
                st.markdown(res_text.replace("[GENERATE_PLAN]", "").replace("[UPDATE_RESUME]", ""))
                st.session_state.messages.append({"role": "assistant", "content": res_text})
                
                # Logic Triggers
                if "[GENERATE_PLAN]" in res_text:
                    supabase.table("student_sessions").update({"study_plan": res_text, "phase": "learning"}).eq("id", curr_sess['id']).execute()
                if "[UPDATE_RESUME]" in res_text:
                    supabase.table("student_sessions").update({"course_resume": res_text}).eq("id", curr_sess['id']).execute()

# --- RIGHT: ACADEMIC KNOWLEDGE PANEL ---
with right_col:
    if "current_chapter" in st.session_state:
        st.markdown("<h4 style='font-weight:800;'>Academic Panel</h4>", unsafe_allow_html=True)
        
        # Mastery Tracker
        st.markdown(f"""
            <div style='background:#fcfcfc; border:1px solid #eee; padding:15px; border-radius:10px;'>
                <p style='font-size:11px; font-weight:700; color:#888; margin:0;'>MASTERY PROGRESS</p>
                <div style='height:8px; background:#f0f0f0; border-radius:4px; margin:10px 0;'>
                    <div style='width:15%; height:100%; background:#10a37f; border-radius:4px;'></div>
                </div>
                <small>Phase: {curr_sess['phase'].upper()}</small>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Structured Knowledge Tabs
        with st.expander("📅 Study Plan", expanded=True):
            st.markdown(curr_sess.get('study_plan') or "_AI is currently analyzing your level to build your plan._")
            
        with st.expander("📝 Course Resume"):
            st.markdown(curr_sess.get('course_resume') or "_Resume will populate as we cover concepts._")
            
        with st.expander("✍️ Personal Notes"):
            st.markdown(curr_sess.get('notes') or "_Personal observations will appear here._")

        with st.expander("🎯 Exercises"):
            st.write("Exercise history and accuracy tracking.")
