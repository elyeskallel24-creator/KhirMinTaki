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
st.set_page_config(page_title="KhirMinTaki", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; color: #000000; }
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
    #MainMenu, footer, header {visibility: hidden;}
    .main-header { font-size: 32px; font-weight: 800; margin-bottom: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
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
    st.markdown("<p style='font-family: Inter; font-size: 24px; font-weight: 700;'>Entrez votre email pour commencer.</p>", unsafe_allow_html=True)
    email_input = st.text_input("Email", placeholder="exemple@email.com", label_visibility="collapsed")
    if st.button("Commencer", use_container_width=True):
        if email_input:
            st.session_state.user_email = email_input
            try:
                supabase.table("users").upsert({"email": email_input}).execute()
                st.rerun()
            except: st.rerun()
    st.stop()

# --- 5. TOP NAVIGATION ---
col_logo, col_nav, col_out = st.columns([2, 4, 1])
with col_logo: st.markdown("<div class='main-header'>KhirMinTaki</div>", unsafe_allow_html=True)

try:
    chapters_data = supabase.table("chapters").select("*").execute()
    chapter_names = [c['name'] for c in chapters_data.data]
    with col_nav:
        selected_chapter = st.selectbox("📚 Chapitres", ["Sélectionner..."] + chapter_names, label_visibility="collapsed")
except:
    st.error("Erreur base de données")
    st.stop()

with col_out:
    if st.button("Sortir"):
        st.session_state.clear()
        st.rerun()

st.divider()

# --- 6. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    name = st.session_state.user_email.split('@')[0].capitalize()
    st.write(f"## **Asslema, {name} !**")
    st.info("Utilise la liste déroulante en haut pour choisir un cours.")
else:
    chapter_id = next((c['id'] for c in chapters_data.data if c['name'] == selected_chapter), None)

    tab1, tab2, tab3, tab4 = st.tabs(["💬 Conversation", "📚 Documents", "📷 Analyse Photo", "📝 Quiz Express"])

    with tab1:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Posez votre question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                try:
                    # RE-INITIALIZE MODEL INSIDE CHAT
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction="Tu es un tuteur expert. Réponds de façon concise. Utilise LaTeX pour les formules."
                    )
                    response = model.generate_content(prompt)
                    
                    if response.text:
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    else:
                        st.error("L'IA n'a pas pu générer de texte.")
                except Exception as e:
                    st.error(f"Erreur IA : {str(e)}")

    with tab2: st.info("Bientôt disponible : Plans d'étude et résumés.")
    with tab3: st.file_uploader("Prendre une photo de l'exercice", type=["jpg","png","jpeg"])
    with tab4: st.button("Lancer le Quiz")
