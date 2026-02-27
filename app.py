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

if "step" not in st.session_state:
    st.session_state.step = "landing"
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "mock_db" not in st.session_state:
    st.session_state.mock_db = {
        "test@taki.com": {"pwd": "password123", "profile_complete": True, "data": {"bac_type": "Mathématiques"}}
    }

# --- 2. DYNAMIC CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    header, footer { visibility: hidden; }
    .main-title { text-align: center; font-weight: 800; font-size: 40px; margin-bottom: 20px; color: #10a37f; }
    
    div[data-testid="InputInstructions"] { display: none; }
    
    div[data-baseweb="input"], div[data-baseweb="textarea"] { 
        border: 1px solid #ccc !important; 
        box-shadow: none !important; 
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within { 
        border: 1px solid #ccc !important; 
        box-shadow: none !important; 
    }

    .validation-msg { font-size: 13px; margin-top: -15px; margin-bottom: 10px; font-weight: 500; }
    .error-text { color: #dc3545; }
    
    hr { margin: 15px 0px; border: 0; border-top: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# --- 3. PAGE FUNCTIONS ---

def show_landing():
    st.markdown("<h1 class='main-title'>KhirMinTaki</h1>", unsafe_allow_html=True)
    if st.button("S'inscrire", use_container_width=True):
        st.session_state.step = "signup"
        st.rerun()
    if st.button("Se connecter", use_container_width=True):
        st.session_state.step = "login"
        st.rerun()

def show_signup():
    st.markdown("## Créer un compte")
    
    # Email Validation
    email = st.text_input("Email", key="signup_email")
    email_valid = is_valid_email(email) if email else True
    if email and not email_valid:
        st.markdown("<p class='validation-msg error-text'>Format invalide, doit être : exemple@gmail.com</p>", unsafe_allow_html=True)
        st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Email']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)
    
    # Password Validation
    pwd = st.text_input("Mot de passe", type="password", key="signup_pwd")
    pwd_valid = len(pwd) >= 8 if pwd else True
    if pwd and not pwd_valid:
        st.markdown("<p class='validation-msg error-text'>Longueur invalide, minimum 8 caractères.</p>", unsafe_allow_html=True)
        st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Mot de passe']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)

    pwd_conf = st.text_input("Confirmez votre mot de passe", type="password", key="signup_pwd_conf")

    if st.button("Créer mon compte", use_container_width=True):
        if is_valid_email(email) and len(pwd) >= 8 and pwd == pwd_conf:
            # Save to mock DB
            st.session_state.mock_db[email] = {"pwd": pwd, "profile_complete": False, "data": {}}
            # Auto-Login: Set user data and move directly to profile setup
            st.session_state.user_data = {"email": email}
            st.session_state.step = "bac_selection" # Starting setup immediately
            st.rerun()
    
    if st.button("Retour", key="back_signup"):
        st.session_state.step = "landing"
        st.rerun()

def show_login():
    st.markdown("<h1 class='main-title'>Connexion</h1>", unsafe_allow_html=True)
    email_log = st.text_input("Email", key="login_email")
    pwd_log = st.text_input("Mot de passe", type="password", key="login_pwd")
    
    if st.button("Se connecter", use_container_width=True):
        user_entry = st.session_state.mock_db.get(email_log)
        if user_entry and user_entry["pwd"] == pwd_log:
            st.session_state.user_data = user_entry["data"]
            st.session_state.user_data["email"] = email_log
            st.session_state.step = "dashboard" if user_entry["profile_complete"] else "bac_selection"
            st.rerun()
        else:
            st.error("Email ou mot de passe incorrect")

    if st.button("Retour", key="back_login"):
        st.session_state.step = "landing"
        st.rerun()

# --- PROFILE SETUP FLOW (SWAPPED ORDER) ---

CORE_MAPPING = {
    "Mathématiques": ["Mathématiques", "Physique", "SVT", "Informatique", "Philosophie", "Arabe", "Français", "Anglais"],
    "Sciences Expérimentales": ["SVT", "Physique", "Mathématiques", "Informatique", "Philosophie", "Arabe", "Français", "Anglais"],
    "Sciences Économiques et Gestion": ["Économie", "Gestion", "Mathématiques", "Informatique", "Histoire-Géographie", "Philosophie", "Arabe", "Français", "Anglais"],
    "Lettres": ["Arabe", "Philosophie", "Histoire-Géographie", "Français", "Anglais"]
}

def show_bac_selection():
    st.markdown("## 🎓 Quelle est votre section Bac ?")
    for opt in CORE_MAPPING.keys():
        if st.button(opt, use_container_width=True):
            st.session_state.user_data["bac_type"] = opt
            st.session_state.step = "curriculum_selection" # Moving to curriculum choice next
            st.rerun()

def show_curriculum_selection():
    st.markdown(f"## 🌍 Système pour la section {st.session_state.user_data.get('bac_type')}")
    if st.button("🇹🇳 Baccalauréat Tunisien", use_container_width=True):
        st.session_state.user_data["curriculum"] = "Tunisien"
        st.session_state.step = "option_selection"
        st.rerun()
    
    if st.button("🇫🇷 Baccalauréat Français", use_container_width=True):
        st.session_state.user_data["curriculum"] = "Français"
        st.session_state.step = "option_selection"
        st.rerun()

def show_option_selection():
    st.markdown("## ✨ Choisissez votre Option")
    options = {"Allemand": "🇩🇪", "Espagnol": "🇪🇸", "Italien": "🇮🇹", "Russe": "🇷🇺", "Chinois": "🇨🇳", "Dessin": "🎨"}
    for opt, emoji in options.items():
        if st.button(f"{emoji} {opt}", use_container_width=True):
            st.session_state.user_data["selected_option"] = opt
            st.session_state.step = "level_audit"
            st.rerun()

def get_full_subject_list():
    bac = st.session_state.user_data.get("bac_type")
    opt = st.session_state.user_data.get("selected_option")
    subjects = CORE_MAPPING.get(bac, []).copy()
    if opt: subjects.append(opt)
    return subjects

def show_level_audit():
    st.markdown(f"## 📊 Niveau : {st.session_state.user_data['bac_type']} ({st.session_state.user_data['curriculum']})")
    subjects = get_full_subject_list()
    assessment_levels = ["Insuffisant", "Fragile", "Satisfaisant", "Bien", "Très bien", "Excellent"]
    levels = {}
    for sub in subjects:
        levels[sub] = st.select_slider(f"**{sub}**", options=assessment_levels, value="Satisfaisant", key=f"aud_{sub}")
        st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("Confirmer mon profil", use_container_width=True):
        st.session_state.user_data["levels"] = levels
        st.session_state.step = "philosophy"
        st.rerun()

def show_philosophy():
    st.markdown("## 🧠 Style d'apprentissage")
    style = st.text_area("Comment voulez-vous que votre tuteur vous enseigne ?", height=150, key="style_input")
    if st.button("Enregistrer mon profil", use_container_width=True):
        st.session_state.user_data["style"] = style
        email = st.session_state.user_data["email"]
        # Update mock DB to mark profile as done
        st.session_state.mock_db[email]["profile_complete"] = True
        st.session_state.mock_db[email]["data"] = st.session_state.user_data
        st.session_state.step = "dashboard"
        st.rerun()

# --- REMAINING DASHBOARD FUNCTIONS (DASHBOARD, SUB, ETC.) ---
# (Keeping your original dashboard and chat logic here...)

def show_dashboard():
    st.markdown(f"## Bienvenue, {st.session_state.user_data['email'].split('@')[0]}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 AI Professor", use_container_width=True):
            st.session_state.step = "subject_hub"
            st.rerun()
        st.button("📄 Résumés (🔒)", disabled=True, use_container_width=True)
    with col2:
        st.button("📝 Exercices (🔒)", disabled=True, use_container_width=True)
        plan_ready = st.session_state.user_data.get("plan_ready")
        if st.button("📅 Plans" if plan_ready else "📅 Plans (🔒)", disabled=not plan_ready, use_container_width=True):
            st.session_state.step = "view_plan"
            st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("Déconnexion"):
        st.session_state.step = "landing"
        st.rerun()

def show_subject_hub():
    if st.button("← Dashboard"):
        st.session_state.step = "dashboard"
        st.rerun()
    st.markdown(f"## 👨‍🏫 AI Professor")
    subjects = get_full_subject_list()
    # ... (rest of your subject hub code)
    st.write("Sélectionnez une matière pour commencer le diagnostic.")

# --- ROUTER ---
pages = {
    "landing": show_landing, "signup": show_signup, "login": show_login,
    "bac_selection": show_bac_selection,
    "curriculum_selection": show_curriculum_selection,
    "option_selection": show_option_selection,
    "level_audit": show_level_audit, "philosophy": show_philosophy,
    "dashboard": show_dashboard, "subject_hub": show_subject_hub
}

if st.session_state.step in pages:
    pages[st.session_state.step]()
