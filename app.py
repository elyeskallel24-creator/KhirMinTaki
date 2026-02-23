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

# --- 2. THE "CLEAN SLATE" UI ENGINE ---
st.set_page_config(page_title="KhirMinTaki", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Aesthetic */
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif !important; 
        background-color: #ffffff !important; 
    }
    
    /* Hide Streamlit Native Elements */
    header, footer, [data-testid="stSidebarNav"] { visibility: hidden !important; }
    [data-testid="stSidebar"] { background-color: #f9f9f9 !important; border-right: 1px solid #f0f0f0 !important; }

    /* Centering the Welcome Screen */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 70vh;
        text-align: center;
    }

    /* Fixed AI Header */
    .chat-header {
        position: fixed;
        top: 0; left: 0; width: 100%;
        background: white;
        padding: 15px 20px;
        border-bottom: 1px solid #f0f0f0;
        z-index: 99;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Mastery Bar */
    .mastery-container { width: 100%; height: 3px; background: #f0f0f0; position: fixed; top: 55px; left: 0; z-index: 100; }
    .mastery-fill { height: 100%; background: #10a37f; transition: width 0.8s ease; }

    /* Chat Input Area */
    .stChatFloatingInputContainer {
        max-width: 800px !important;
        margin: 0 auto !important;
        background: transparent !important;
    }
    
    /* Study Plan Chip */
    .chip {
        display: inline-block;
        padding: 8px 16px;
        background: #f0f7f4;
        color: #10a37f;
        border-radius: 20px;
        font-weight: 600;
        font-size: 13px;
        cursor: pointer;
        border: 1px solid #d1e7dd;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if "user_email" not in st.session_state:
    st.markdown("<div class='welcome-container'>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 42px; font-weight: 800;'>KhirMinTaki</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; margin-bottom: 30px;'>Your personalized Tunisian AI Tutor.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        email = st.text_input("Email", placeholder="me@example.com", label_visibility="collapsed")
        if st.button("Start Learning", use_container_width=True):
            if email:
                st.session_state.user_email = email
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 4. SIDEBAR (CHAT HISTORY STYLE) ---
with st.sidebar:
    st.markdown("<h2 style='font-size: 18px; font-weight: 700; margin-bottom: 20px;'>Mathematics</h2>", unsafe_allow_html=True)
    try:
        chapters = supabase.table("chapters").select("*").execute().data
        for ch in chapters:
            if st.button(f"💬 {ch['name']}", key=f"btn_{ch['id']}", use_container_width=True):
                st.session_state.current_chapter = ch['name']
                st.session_state.chapter_id = ch['id']
                st.session_state.messages = [] # New thread
                st.rerun()
    except:
        st.error("DB Error")
    
    st.markdown("<div style='position: fixed; bottom: 20px;'>", unsafe_allow_html=True)
    if st.button("Log out"):
        st.session_state.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. MAIN WORKSPACE ---
if "current_chapter" not in st.session_state:
    # This is the "Blank Page" fix - Explicitly centering the content
    st.markdown("<div class='welcome-container'>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-weight: 700; color: #1a1a1a;'>How can I help you revise today?</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #888;'>Select a chapter from the sidebar on the left to start.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Force open sidebar if they haven't picked a chapter
    st.info("← Open the sidebar menu to pick a chapter.")
else:
    # Chapter Header & Mastery
    mastery_val = 42 
    st.markdown(f"""
        <div class="chat-header">
            <span style="font-weight: 700; font-size: 14px;">Mathématiques — {st.session_state.current_chapter}</span>
            <span style="color: #10a37f; font-weight: 700; font-size: 14px;">Mastery: {mastery_val}%</span>
        </div>
        <div class="mastery-container"><div class="mastery-fill" style="width: {mastery_val}%;"></div></div>
        <div style="height: 70px;"></div>
    """, unsafe_allow_html=True)

    # Chat Logic
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": f"Before we begin **{st.session_state.current_chapter}**, tell me: what's your current level or what do you find hardest here?"}]

    # Create a container for chat to keep it centered
    chat_container = st.container()
    with chat_container:
        col_left, col_mid, col_right = st.columns([1, 4, 1])
        with col_mid:
            for m in st.session_state.messages:
                with st.chat_message(m["role"]):
                    st.markdown(m["content"])
                    if "[PLAN_READY]" in m["content"]:
                        st.markdown("<div class='chip'>Study Plan Created ✓</div>", unsafe_allow_html=True)

    # Input Fixed at Bottom
    if prompt := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()
