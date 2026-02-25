import streamlit as st
import re
import google.generativeai as genai
from groq import Groq
from supabase import create_client

# --- 1. INITIAL SETUP ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Setup Error: {e}")

st.set_page_config(page_title="KhirMinTaki", layout="centered")

# Initialize Session States
if "step" not in st.session_state:
    st.session_state.step = "landing"
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "mock_db" not in st.session_state:
    # Simulated database for testing: {email: password}
    st.session_state.mock_db = {"test@taki.com": "password123"}

# --- 2. STYLING & VALIDATION CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    header, footer { visibility: hidden; }
    .main-title { text-align: center; font-weight: 800; font-size: 40px; margin-bottom: 20px; color: #10a37f; }
    
    /* Validation Border Styles */
    div[data-baseweb="input"] { border-radius: 8px; transition: 0.3s; }
    .valid-input div[data-baseweb="input"] { border: 2px solid #28a745 !important; }
    .invalid-input div[data-baseweb="input"] { border: 2px solid #dc3545 !important; }
    
    hr { margin: 15px 0px; border: 0; border-top: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# Helper for Email Validation
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# --- 3. PAGE FUNCTIONS ---

def show_landing():
    st.markdown("<h1 class='main-title'>KhirMinTaki</h1>", unsafe_allow_html=True)
    st.write("Bienvenue sur votre plateforme de tutorat intelligent.")
    if st.button("S'inscrire", use_container_width=True):
        st.session_state.step = "signup"
        st.rerun()
    if st.button("Se connecter", use_container_width=True):
        st.session_state.step = "login"
        st.rerun()

def show_signup():
    st.markdown("## Créer un compte")
    
    email = st.text_input("Email")
    pwd = st.text_input("Mot de passe", type="password")
    pwd_conf = st.text_input("Confirmez votre mot de passe", type="password")
    
    # Validation Logic
    email_valid = is_valid_email(email)
    pwd_len_valid = len(pwd) >= 8
    match_valid = pwd == pwd_conf and len(pwd) > 0

    # Show validation hints
    if email:
        st.markdown(f"<div class='{'valid-input' if email_valid else 'invalid-input'}'></div>", unsafe_allow_html=True)
    
    if st.button("Créer mon compte", use_container_width=True):
        if not email_valid:
            st.error("Format d'email invalide.")
        elif not pwd_len_valid:
            st.error("Le mot de passe doit faire au moins 8 caractères.")
        elif not match_valid:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            st.session_state.mock_db[email] = pwd
            st.success("Compte créé avec succès ! Veuillez vous connecter.")
            st.session_state.step = "login"
            st.rerun()
    
    if st.button("Retour", key="back_signup"):
        st.session_state.step = "landing"
        st.rerun()

def show_login():
    st.markdown("<h1 class='main-title'>Connexion</h1>", unsafe_allow_html=True)
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter", use_container_width=True):
        if email in st.session_state.mock_db and st.session_state.mock_db[email] == password:
            st.session_state.user_data["email"] = email
            st.session_state.step = "bac_selection"
            st.rerun()
        else:
            st.error("Email ou mot de passe incorrect.")

    if st.button("Retour", key="back_login"):
        st.session_state.step = "landing"
        st.rerun()

# --- REUSING PREVIOUS LOGIC (Curriculum, Audit, Hub, Chat) ---
# [Note: All core logic from previous steps remains below]

def show_bac_selection():
    st.markdown("## 🎓 Quelle est votre section Bac ?")
    options = ["Mathématiques", "Sciences Expérimentales", "Sciences Économiques et Gestion", "Lettres"]
    for opt in options:
        if st.button(opt, use_container_width=True):
            st.session_state.user_data["bac_type"] = opt
            st.session_state.step = "option_selection"
            st.rerun()

# ... (Include show_option_selection, show_level_audit, show_philosophy, show_dashboard, show_subject_hub, show_chat_diagnose here as per previous code) ...

# --- 4. THE STEP ROUTER ---
pages = {
    "landing": show_landing,
    "signup": show_signup,
    "login": show_login,
    "bac_selection": show_bac_selection,
    # (Other pages added here)
}

# (Due to length, ensure you maintain the rest of the functions from the previous response)
if st.session_state.step in pages:
    pages[st.session_state.step]()
else:
    # This catches the hub, audit, and chat if not in the small 'pages' dict above
    import sys
    current_module = sys.modules[__name__]
    func_name = f"show_{st.session_state.step}"
    if hasattr(current_module, func_name):
        getattr(current_module, func_name)()
