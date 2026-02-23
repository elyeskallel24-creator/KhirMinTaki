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

# --- 2. STYLE & BRANDING ---
st.set_page_config(page_title="KhirMinTaki", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; color: #000000; }
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #f0f0f0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Make the sidebar toggle button slightly more visible by adding a background */
    [data-testid="collapsedControl"] {
        background-color: #f0f2f6;
        border-radius: 0 10px 10px 0;
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

# --- 5. SIDEBAR ---
st.sidebar.markdown(f"### **KhirMinTaki**")
if st.sidebar.button("Déconnexion"):
    del st.session_state.user_email
    st.rerun()

try:
    chapters_data = supabase.table("chapters").select("*").execute()
    chapter_names = [c['name'] for c in chapters_data.data]
    selected_chapter = st.sidebar.selectbox("Chapitres", ["Sélectionner..."] + chapter_names)
except Exception as e:
    st.error(f"Error loading chapters: {e}")
    st.stop()

# --- 6. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    name = st.session_state.user_email.split('@')[0].capitalize()
    st.write(f"## **Asslema, {name} !**")
    
    # CLEAR INSTRUCTION FOR THE SIDEBAR
    st.info("👈 **Utilisez le menu à gauche pour choisir un chapitre.**")
    st.warning("Si vous ne voyez pas le menu, cliquez sur la petite flèche ( **>** ) tout en haut à gauche de votre écran.")
    
    try:
        stats = supabase.table("student_sessions").select("id").eq("user_email", st.session_state.user_email).execute()
        st.metric("Chapitres explorés", len(stats.data))
    except:
        st.metric("Chapitres explorés", 0)

else:
    chapter_id = next(c['id'] for c in chapters_data.data if c['name'] == selected_chapter)
    
    # Progress
    score_res = supabase.table("quiz_scores").select("score").eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).order("created_at", desc=True).limit(1).execute()
    latest_score = score_res.data[0]['score'] if score_res.data else 0
    st.write(f"**Maîtrise du chapitre : {latest_score}%**")
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
        st.write("Vos documents s'afficheront ici après avoir discuté avec le tuteur.")

    with tab3:
        img_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
        if img_file:
            st.image(Image.open(img_file), width=400)

    with tab4:
        if st.button("Générer un Quiz"):
            st.write("Génération en cours...")
