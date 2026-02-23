import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
from fpdf import FPDF
import streamlit.components.v1 as components
from PIL import Image
import json

# --- 1. SETUP CONNECTIONS ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Setup Error: {e}")

# --- 2. STYLE & BRANDING (CLEAN TOP-NAV DESIGN) ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; color: #000000; }
    .stApp { background-color: #ffffff; }
    
    /* Hide the sidebar completely to avoid confusion */
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }

    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    .main-header {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 20px;
        border-bottom: 2px solid #f0f0f0;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. TUNISIAN TYPEWRITER ---
def typewriter_effect():
    html_code = """
    <div class="typewriter-container" id="typewriter"></div>
    <script>
        const textElement = document.getElementById("typewriter");
        const words = ["KhirMinTaki", "A9ra khir", "A9ra asra3"];
        let wordIndex = 0; let charIndex = 0; let isDeleting = false;
        function type() {
            const currentWord = words[wordIndex];
            if (isDeleting) { textElement.textContent = currentWord.substring(0, charIndex - 1); charIndex--; }
            else { textElement.textContent = currentWord.substring(0, charIndex + 1); charIndex++; }
            let typeSpeed = isDeleting ? 100 : 150;
            if (!isDeleting && charIndex === currentWord.length) { isDeleting = true; typeSpeed = 2000; }
            else if (isDeleting && charIndex === 0) { isDeleting = false; wordIndex = (wordIndex + 1) % words.length; typeSpeed = 500; }
            setTimeout(type, typeSpeed);
        }
        type();
    </script>
    <style>
        .typewriter-container { font-family: 'Inter', sans-serif; font-weight: 800; font-size: 48px; color: #000000; height: 60px; display: flex; align-items: center; }
    </style>
    """
    components.html(html_code, height=80)

# --- 4. AUTHENTICATION ---
if "user_email" not in st.session_state:
    typewriter_effect()
    st.markdown("<p style='font-family: Inter; font-size: 28px; font-weight: 700;'>Bienvenue. Entrez votre email.</p>", unsafe_allow_html=True)
    email_input = st.text_input("Email", placeholder="exemple@email.com", label_visibility="collapsed")
    if st.button("Commencer", use_container_width=True):
        if email_input:
            try:
                supabase.table("users").upsert({"email": email_input}).execute()
                st.session_state.user_email = email_input
                st.rerun()
            except Exception as e:
                st.error(f"Database Error: {e}")
    st.stop()

# --- 5. TOP NAVIGATION (NEW) ---
col_logo, col_nav, col_out = st.columns([2, 4, 1])
with col_logo:
    st.markdown("<div class='main-header'>KhirMinTaki</div>", unsafe_allow_html=True)

with col_nav:
    try:
        chapters_data = supabase.table("chapters").select("*").execute()
        chapter_names = [c['name'] for c in chapters_data.data]
        selected_chapter = st.selectbox("📚 Choisis ton chapitre :", ["Sélectionner..."] + chapter_names, label_visibility="collapsed")
    except Exception as e:
        st.error("Erreur de chargement")
        st.stop()

with col_out:
    if st.button("Sortir"):
        del st.session_state.user_email
        st.rerun()

st.divider()

# --- 6. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    name = st.session_state.user_email.split('@')[0].capitalize()
    st.write(f"## **Asslema, {name} !**")
    st.info("Utilise la liste déroulante en haut pour choisir un cours et commencer à réviser.")
    
    try:
        stats = supabase.table("student_sessions").select("id").eq("user_email", st.session_state.user_email).execute()
        st.metric("Chapitres explorés", len(stats.data))
    except:
        st.metric("Chapitres explorés", 0)

else:
    # Logic for Chapter...
    chapter_id = next(c['id'] for c in chapters_data.data if c['name'] == selected_chapter)
    
    score_res = supabase.table("quiz_scores").select("score").eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).order("created_at", desc=True).limit(1).execute()
    latest_score = score_res.data[0]['score'] if score_res.data else 0
    st.write(f"### Chapitre : {selected_chapter}")
    st.write(f"**Maîtrise : {latest_score}%**")
    st.progress(latest_score / 100)

    tab1, tab2, tab3, tab4 = st.tabs(["💬 Conversation", "📚 Documents", "📷 Analyse Photo", "📝 Quiz Express"])

    with tab1:
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        if prompt := st.chat_input("Posez votre question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

    with tab2:
        st.info("Discute avec l'IA pour générer tes documents.")

    with tab3:
        st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])

    with tab4:
        st.button("Générer un Quiz")
