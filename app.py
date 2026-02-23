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

st.set_page_config(page_title="KhirMinTaki", layout="wide")

# --- 2. CUSTOM UI ENGINE (MODERN CHATGPT STYLE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    
    /* Force hide any sidebars */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    header, footer, #MainMenu { visibility: hidden; }

    /* Right Dashboard Panel */
    .dashboard-panel {
        background-color: #f9f9f9;
        border-left: 1px solid #ececec;
        padding: 24px;
        height: 100vh;
        position: fixed;
        right: 0;
        top: 0;
        overflow-y: auto;
    }

    /* Modern Cards */
    .glass-card {
        background: white;
        border: 1px solid #eee;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    
    .section-title {
        font-size: 11px;
        font-weight: 700;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 12px;
    }

    /* Chat Styling */
    .stChatFloatingInputContainer { 
        padding-bottom: 40px !important;
        background-color: transparent !important;
    }
    .stTextInput input {
        border-radius: 12px !important;
        padding: 12px 16px !important;
        border: 1px solid #e5e5e5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if "user_email" not in st.session_state:
    st.markdown("<h1 style='text-align:center; margin-top:100px; font-weight:800;'>KhirMinTaki</h1>", unsafe_allow_html=True)
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

# --- 4. DATA FETCHING ---
try:
    chapters = supabase.table("chapters").select("*").execute().data
    chapter_names = [c['name'] for c in chapters]
except:
    st.error("Database Connection Failed.")
    st.stop()

# --- 5. MAIN LAYOUT (TWO COLUMNS) ---
# Column 1: Spacious Chat | Column 2: Dashboard
chat_area, dash_area = st.columns([7, 3])

with dash_area:
    st.markdown("<div class='dashboard-panel'>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-size:22px; margin-bottom:20px;'>KhirMinTaki</h2>", unsafe_allow_html=True)
    
    # Navigation Section
    st.markdown("<div class='section-title'>Sélection du Cours</div>", unsafe_allow_html=True)
    sel_chap = st.selectbox("Chapitre", ["Sélectionner..."] + chapter_names, label_visibility="collapsed")
    
    if sel_chap != "Sélectionner...":
        chapter_id = next(c['id'] for c in chapters if c['name'] == sel_chap)
        
        # Load or Create Session
        res = supabase.table("student_sessions").select("*").eq("user_email", st.session_state.user_email).eq("chapter_id", chapter_id).execute()
        if not res.data:
            supabase.table("student_sessions").insert({"user_email": st.session_state.user_email, "chapter_id": chapter_id, "phase": "assessment"}).execute()
            st.rerun()
        
        curr_sess = res.data[0]

        # Dynamic Resources Section
        st.markdown("<div style='margin-top:30px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Ton Parcours</div>", unsafe_allow_html=True)
        
        with st.container():
            st.markdown("<div class='glass-card'><b>📅 Studying Plan</b><br><small>" + (curr_sess.get('study_plan') or "En attente d'évaluation...") + "</small></div>", unsafe_allow_html=True)
            st.markdown("<div class='glass-card'><b>📝 Course Resume</b><br><small>" + (curr_sess.get('course_resume') or "S'actualise pendant le cours.") + "</small></div>", unsafe_allow_html=True)
            st.markdown("<div class='glass-card'><b>✍️ Personal Notes</b><br><small>" + (curr_sess.get('notes') or "Remarques à venir.") + "</small></div>", unsafe_allow_html=True)
            st.markdown("<div class='glass-card'><b>🎯 Exercises</b><br><small>Maîtrise: 0%</small></div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
    if st.button("👤 Déconnexion", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with chat_area:
    if sel_chap == "Sélectionner...":
        st.markdown("<div style='height:30vh;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; font-weight:700;'>Asslema, " + st.session_state.user_email.split('@')[0].capitalize() + "!</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#666;'>Choisis un chapitre à droite pour commencer ta révision.</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"### Révision : {sel_chap}")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Je suis prêt. Quel est ton niveau actuel sur ce chapitre ?"}]

        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])

        if prompt := st.chat_input("Écris ton message ici..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                try:
                    chat = groq_client.chat.completions.create(
                        messages=[{"role": "system", "content": "Tu es un tuteur Tunisien expert. Utilise LaTeX. Si l'évaluation est finie, ajoute [GENERATE_PLAN]."}] + st.session_state.messages[-5:],
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
                    st.toast("Nouveau Plan d'étude disponible !")
