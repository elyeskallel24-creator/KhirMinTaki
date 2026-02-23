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

# --- 2. STYLE & BRANDING (RIGHT-SIDE DASHBOARD) ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    
    /* Force hide any ghost sidebars */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu, footer, header {visibility: hidden;}

    .main-header { font-size: 28px; font-weight: 800; color: #1a1a1a; margin-bottom: 10px; }
    .right-panel {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #eee;
        height: 85vh;
        overflow-y: auto;
    }
    .section-label { font-size: 12px; font-weight: 700; color: #888; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 1px; }
    .status-badge { background: #000; color: #fff; padding: 4px 10px; border-radius: 20px; font-size: 11px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. AUTHENTICATION ---
if "user_email" not in st.session_state:
    st.markdown("<h1 style='text-align: center; margin-top: 80px; font-weight:800;'>KhirMinTaki</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        email = st.text_input("Email", placeholder="votre@email.com", label_visibility="collapsed")
        if st.button("Se connecter", use_container_width=True):
            if email:
                st.session_state.user_email = email
                try: supabase.table("users").upsert({"email": email}).execute()
                except: pass
                st.rerun()
    st.stop()

# --- 4. TOP BAR ---
tcol1, tcol2, tcol3 = st.columns([2, 4, 1])
with tcol1:
    st.markdown("<div class='main-header'>KhirMinTaki</div>", unsafe_allow_html=True)

try:
    chapters = supabase.table("chapters").select("*").execute().data
    names = [c['name'] for c in chapters]
    with tcol2:
        sel_chap = st.selectbox("📚 Cours", ["Sélectionner un chapitre..."] + names, label_visibility="collapsed")
except:
    st.error("Base de données indisponible.")
    st.stop()

with tcol3:
    if st.button("Sortir", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.divider()

# --- 5. MAIN INTERFACE (SPLIT VIEW) ---
if sel_chap == "Sélectionner un chapitre...":
    st.write(f"## **Asslema, {st.session_state.user_email.split('@')[0].capitalize()} !**")
    st.info("Sélectionne un chapitre en haut pour commencer ton parcours personnalisé.")
else:
    chapter_id = next(c['id'] for c in chapters if c['name'] == sel_chap)
    
    # Session Loading
    session_res = supabase.table("student_sessions").select("*").eq("user_email", st.session_state.user_email).eq("chapter_id", chapter_id).execute()
    if not session_res.data:
        supabase.table("student_sessions").insert({"user_email": st.session_state.user_email, "chapter_id": chapter_id, "phase": "assessment"}).execute()
        st.rerun()
    
    curr_session = session_res.data[0]
    
    # LAYOUT: Chat (Left) | Dashboard (Right)
    chat_col, space, dash_col = st.columns([6, 0.5, 3.5])

    with chat_col:
        st.markdown(f"**Chat avec ton Tuteur Expert • {sel_chap}**")
        
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Asslema! Je suis là pour t'accompagner. Pour commencer, parle-moi de tes difficultés avec ce chapitre."}]
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Écris ton message ici..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                phase = curr_session.get('phase', 'assessment')
                sys_prompt = f"Tu es un tuteur expert tunisien. Phase: {phase}. Utilise LaTeX. Si tu as assez d'infos pour le plan, finis par [GENERATE_PLAN]. Pour le résumé, finis par [UPDATE_RESUME]."
                
                try:
                    chat = groq_client.chat.completions.create(
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages[-5:],
                        model="llama-3.3-70b-versatile",
                    )
                    res_text = chat.choices[0].message.content
                except:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    res_text = model.generate_content(prompt).text

                st.markdown(res_text.replace("[GENERATE_PLAN]", "").replace("[UPDATE_RESUME]", ""))
                st.session_state.messages.append({"role": "assistant", "content": res_text})

                if "[GENERATE_PLAN]" in res_text:
                    supabase.table("student_sessions").update({"study_plan": res_text, "phase": "learning"}).eq("id", curr_session['id']).execute()
                    st.toast("Plan d'étude généré !")

    with dash_col:
        st.markdown("<div class='right-panel'>", unsafe_allow_html=True)
        st.markdown(f"<span class='status-badge'>{curr_session['phase'].upper()}</span>", unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        st.markdown("<div class='section-label'>📅 Studying Plan</div>", unsafe_allow_html=True)
        st.write(curr_session.get('study_plan') or "*Sera généré après l'évaluation.*")
        
        st.divider()
        
        st.markdown("<div class='section-label'>📝 Course Resume</div>", unsafe_allow_html=True)
        st.write(curr_session.get('course_resume') or "*Sera créé pendant tes leçons.*")
        
        st.divider()
        
        st.markdown("<div class='section-label'>✍️ Personal Notes</div>", unsafe_allow_html=True)
        st.write(curr_session.get('notes') or "*Remarques à venir.*")
        
        st.markdown("</div>", unsafe_allow_html=True)
