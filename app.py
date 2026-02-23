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
    st.error(f"Setup Error: {e}")

st.set_page_config(page_title="KhirMinTaki", layout="wide", initial_sidebar_state="expanded")

# --- 2. AI-NATIVE DESIGN SYSTEM (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Modern AI Reset */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; color: #1a1a1a; }
    header, footer { visibility: hidden; }
    
    /* Clean Sidebar (Chat List Style) */
    [data-testid="stSidebar"] { background-color: #f9f9f9 !important; border-right: 1px solid #f0f0f0; }
    .sidebar-content { padding: 20px; }
    .chat-thread-item { 
        padding: 10px; border-radius: 8px; margin-bottom: 5px; 
        font-size: 14px; color: #444; cursor: pointer; transition: 0.2s;
    }
    .chat-thread-item:hover { background-color: #ececec; }

    /* Centered Conversation Panel */
    .main-chat-container { max-width: 800px; margin: 0 auto; padding-top: 20px; }
    
    /* AI Header with Progress Bar */
    .chat-header {
        position: fixed; top: 0; width: 100%; background: rgba(255,255,255,0.9);
        backdrop-filter: blur(10px); z-index: 1000; padding: 15px 0; border-bottom: 1px solid #f0f0f0;
    }
    .mastery-progress-bg { height: 4px; width: 100%; background: #f0f0f0; position: absolute; bottom: 0; }
    .mastery-progress-fill { height: 4px; background: #10a37f; transition: width 0.5s ease; }

    /* AI Message Styling */
    .stChatMessage { background: transparent !important; border: none !important; }
    
    /* Interactive Cards & Chips */
    .study-plan-chip {
        display: inline-flex; align-items: center; gap: 8px;
        background: #f0f7f4; color: #10a37f; padding: 8px 16px;
        border-radius: 20px; border: 1px solid #d1e7dd;
        font-size: 13px; font-weight: 600; cursor: pointer; margin-top: 10px;
    }
    .exercise-card {
        border: 1px solid #e5e5e5; border-radius: 12px; padding: 20px;
        margin: 15px 0; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Hide scrollbars but keep functionality */
    ::-webkit-scrollbar { width: 0px; background: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION & AUTH ---
if "user_email" not in st.session_state:
    st.markdown("<div style='text-align:center; padding-top:100px;'><h1>KhirMinTaki</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        email = st.text_input("Email", placeholder="email@example.com")
        if st.button("Continue", use_container_width=True):
            if email:
                st.session_state.user_email = email
                st.rerun()
    st.stop()

# --- 4. SIDEBAR (CHAPTERS AS CHAT THREADS) ---
with st.sidebar:
    st.markdown("<div style='font-weight:700; font-size:18px; margin-bottom:20px;'>KhirMinTaki</div>", unsafe_allow_html=True)
    
    st.markdown("<p style='font-size:11px; color:#999; font-weight:700;'>MATHEMATICS</p>", unsafe_allow_html=True)
    try:
        chapters = supabase.table("chapters").select("*").execute().data
        for ch in chapters:
            if st.button(f"💬 {ch['name']}", key=ch['id'], use_container_width=True):
                st.session_state.current_chapter = ch['name']
                st.session_state.chapter_id = ch['id']
                st.session_state.messages = [] # Reset for new thread look
                st.rerun()
    except: st.error("Database connection error.")

    st.markdown("---")
    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# --- 5. MAIN CONVERSATION ---
if "current_chapter" not in st.session_state:
    st.markdown("<div style='height:40vh;'></div><h2 style='text-align:center; color:#ccc;'>Select a chapter to start chatting.</h2>", unsafe_allow_html=True)
else:
    # 5.1 HEADER WITH MASTERY BAR
    mastery = 42 # This would be pulled from Supabase
    st.markdown(f"""
        <div class="chat-header">
            <div style="max-width:800px; margin:0 auto; padding:0 20px; display:flex; justify-content:space-between;">
                <span style="font-weight:600;">Mathematics — {st.session_state.current_chapter}</span>
                <span style="color:#10a37f; font-weight:700;">Mastery: {mastery}%</span>
            </div>
            <div class="mastery-progress-bg"><div class="mastery-progress-fill" style="width:{mastery}%;"></div></div>
        </div>
    """, unsafe_allow_html=True)

    # 5.2 CHAT AREA
    st.markdown("<div class='main-chat-container'>", unsafe_allow_html=True)
    
    # Load session state for the chapter
    sess_res = supabase.table("student_sessions").select("*").eq("user_email", st.session_state.user_email).eq("chapter_id", st.session_state.chapter_id).execute()
    if not sess_res.data:
        supabase.table("student_sessions").insert({"user_email": st.session_state.user_email, "chapter_id": st.session_state.chapter_id, "phase": "assessment"}).execute()
        st.rerun()
    curr_sess = sess_res.data[0]

    if not st.session_state.get("messages"):
        st.session_state.messages = [{"role": "assistant", "content": f"Before we begin **{st.session_state.current_chapter}**, I need to understand your current level. How would you describe your understanding of this topic so far?"}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if "[PLAN_READY]" in m["content"]:
                if st.button("Study Plan Created ✓"):
                    st.session_state.show_panel = True

    # 5.3 PANEL SLIDE-OVER (CONTROLLED BY STATE)
    if st.session_state.get("show_panel"):
        with st.sidebar: # Using sidebar as a temporary "right panel" simulator for stability
            st.markdown("### Academic Records")
            tab_p, tab_s, tab_e, tab_n = st.tabs(["Plan", "Summary", "Ex", "Notes"])
            with tab_p: st.write(curr_sess.get("study_plan") or "Generating...")
            with tab_s: st.write(curr_sess.get("course_resume") or "Empty...")
            if st.button("Close Panel"): 
                st.session_state.show_panel = False
                st.rerun()

    # 5.4 CHAT INPUT
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            sys_msg = "You are a modern AI tutor. Be clean, concise, and use LaTeX. If you've gathered enough info, trigger [PLAN_READY]."
            try:
                chat = groq_client.chat.completions.create(
                    messages=[{"role": "system", "content": sys_msg}] + st.session_state.messages[-5:],
                    model="llama-3.3-70b-versatile",
                )
                res = chat.choices[0].message.content
            except:
                res = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt).text
            
            st.markdown(res.replace("[PLAN_READY]", ""))
            st.session_state.messages.append({"role": "assistant", "content": res})
            
            if "[PLAN_READY]" in res:
                supabase.table("student_sessions").update({"study_plan": "Your custom plan based on our talk.", "phase": "teaching"}).eq("id", curr_sess["id"]).execute()
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
