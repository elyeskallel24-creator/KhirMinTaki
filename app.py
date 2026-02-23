import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
import streamlit.components.v1 as components

# --- 1. CONFIG & SETUP ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Setup Error: {e}")

st.set_page_config(page_title="KhirMinTaki", layout="wide", initial_sidebar_state="expanded")

# --- 2. THE "CHATGPT" DESIGN ENGINE (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Reset */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    
    /* Sidebar Overhaul */
    [data-testid="stSidebar"] {
        background-color: #171717 !important;
        border-right: none;
        padding-top: 20px;
    }
    
    /* Sidebar Item Styling */
    .nav-item {
        padding: 10px 14px;
        margin: 4px 8px;
        border-radius: 8px;
        color: #ececec;
        font-size: 14px;
        cursor: pointer;
        transition: background 0.2s ease;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .nav-item:hover { background-color: #2f2f2f; }
    .nav-section-title {
        color: #666;
        font-size: 11px;
        font-weight: 700;
        margin: 20px 0 10px 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Chat Area Styling */
    .stChatMessage { border: none !important; background: transparent !important; padding: 20px 0 !important; }
    .stChatFloatingInputContainer { 
        bottom: 20px !important; 
        background: transparent !important; 
        border: none !important;
        padding-bottom: 20px !important;
    }
    
    /* Custom Input Wrapper */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 1px solid #e5e5e5 !important;
        padding: 15px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }

    /* Hide Default Headers */
    header, footer, #MainMenu { visibility: hidden; }
    
    /* Dashboard Cards (Right Side) */
    .db-card {
        background: #ffffff;
        border: 1px solid #f0f0f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        transition: transform 0.2s ease;
    }
    .db-card:hover { border-color: #d1d1d1; transform: translateY(-2px); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if "user_email" not in st.session_state:
    st.markdown("<h1 style='text-align:center; margin-top:100px; font-weight:700;'>KhirMinTaki</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        email = st.text_input("Email", placeholder="Continuez avec votre email...", label_visibility="collapsed")
        if st.button("Se connecter", use_container_width=True):
            if email:
                st.session_state.user_email = email
                try: supabase.table("users").upsert({"email": email}).execute()
                except: pass
                st.rerun()
    st.stop()

# --- 4. SIDEBAR (NAVIGATION & HISTORY) ---
with st.sidebar:
    st.markdown("<h2 style='color:white; padding-left:15px; font-size:22px;'>KhirMinTaki</h2>", unsafe_allow_html=True)
    
    if st.button("＋ Nouveau Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("<div class='nav-section-title'>Vos Cours</div>", unsafe_allow_html=True)
    try:
        chapters = supabase.table("chapters").select("*").execute().data
        chapter_names = [c['name'] for c in chapters]
        sel_chap = st.selectbox("Sélectionnez", ["Sélectionner..."] + chapter_names, label_visibility="collapsed")
    except:
        st.error("DB Error")
        st.stop()

    st.markdown("<div class='nav-section-title'>Ressources</div>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item'>📚 Bibliothèque de PDF</div>", unsafe_allow_html=True)
    st.markdown("<div class='nav-item'>🏆 Classement</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='position: fixed; bottom: 20px; width: 260px;'>", unsafe_allow_html=True)
    if st.button("👤 " + st.session_state.user_email.split('@')[0], use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- 5. MAIN CHAT & DASHBOARD ---
if sel_chap == "Sélectionner...":
    st.markdown("<div style='height:30vh;'></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#444;'>Comment puis-je t'aider à réviser aujourd'hui ?</h2>", unsafe_allow_html=True)
else:
    chapter_id = next(c['id'] for c in chapters if c['name'] == sel_chap)
    
    # Load Session Data
    res = supabase.table("student_sessions").select("*").eq("user_email", st.session_state.user_email).eq("chapter_id", chapter_id).execute()
    if not res.data:
        supabase.table("student_sessions").insert({"user_email": st.session_state.user_email, "chapter_id": chapter_id, "phase": "assessment"}).execute()
        st.rerun()
    
    curr_sess = res.data[0]
    
    # Layout Split: Chat vs Dashboard
    chat_col, dash_col = st.columns([7, 3])

    with chat_col:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": f"Asslema! On commence **{sel_chap}**. Quel est ton niveau actuel sur ce sujet ?"}]
        
        # Conversation Display
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat Input
        if prompt := st.chat_input("Réponds au tuteur..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                try:
                    chat = groq_client.chat.completions.create(
                        messages=[{"role": "system", "content": f"Tu es un tuteur Tunisien expert. Phase: {curr_sess['phase']}. Utilise LaTeX. Si tu as fini l'évaluation, ajoute [GENERATE_PLAN]."}] + st.session_state.messages[-5:],
                        model="llama-3.3-70b-versatile",
                    )
                    res_text = chat.choices[0].message.content
                except:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    res_text = model.generate_content(prompt).text

                st.markdown(res_text.replace("[GENERATE_PLAN]", ""))
                st.session_state.messages.append({"role": "assistant", "content": res_text})
                
                if "[GENERATE_PLAN]" in res_text:
                    supabase.table("student_sessions").update({"study_plan": res_text, "phase": "learning"}).eq("id", curr_sess['id']).execute()
                    st.toast("Plan d'étude disponible !")

    with dash_col:
        st.markdown("<h4 style='margin-bottom:20px;'>Votre Parcours</h4>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div class='db-card'>", unsafe_allow_html=True)
            st.markdown("**📅 Studying Plan**")
            st.write(curr_sess.get('study_plan') or "Évaluation en cours...")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='db-card'>", unsafe_allow_html=True)
            st.markdown("**📝 Course Resume**")
            st.write(curr_sess.get('course_resume') or "Se génère pendant la leçon.")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='db-card'>", unsafe_allow_html=True)
            st.markdown("**✍️ Notes**")
            st.write(curr_sess.get('notes') or "Remarques personnalisées.")
            st.markdown("</div>", unsafe_allow_html=True)
