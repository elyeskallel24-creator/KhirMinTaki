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
    # Adding a default user for testing: test@taki.com / password123
    st.session_state.mock_db = {"test@taki.com": "password123"}

# --- 2. DYNAMIC CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    header, footer { visibility: hidden; }
    .main-title { text-align: center; font-weight: 800; font-size: 40px; margin-bottom: 20px; color: #10a37f; }
    
    div[data-testid="InputInstructions"] { display: none; }
    
    /* Remove focus glow */
    div[data-baseweb="input"] { border: 1px solid #ccc !important; box-shadow: none !important; }
    div[data-baseweb="input"]:focus-within { border: 1px solid #ccc !important; box-shadow: none !important; }

    .validation-msg { font-size: 13px; margin-top: -15px; margin-bottom: 10px; font-weight: 500; }
    .error-text { color: #dc3545; }
    .success-text { color: #28a745; }
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
    email = st.text_input("Email", key="signup_email")
    email_valid = is_valid_email(email) if email else None
    email_exists = email in st.session_state.mock_db
    
    if email:
        if email_exists:
            st.markdown("<p class='validation-msg error-text'>Cet email est déjà utilisé</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Email']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)
        elif email_valid:
            st.markdown("<p class='validation-msg success-text'>Email valide</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Email']) div[data-baseweb='input'] { border: 2px solid #28a745 !important; }</style>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='validation-msg error-text'>Format invalide</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Email']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)
    
    pwd = st.text_input("Mot de passe", type="password", key="signup_pwd")
    pwd_valid = len(pwd) >= 8 if pwd else None
    if pwd:
        if pwd_valid:
            st.markdown("<p class='validation-msg success-text'>Longueur valide</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Mot de passe']) div[data-baseweb='input'] { border: 2px solid #28a745 !important; }</style>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='validation-msg error-text'>Minimum 8 caractères</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Mot de passe']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)

    pwd_conf = st.text_input("Confirmez votre mot de passe", type="password", key="signup_pwd_conf")
    match_valid = (pwd == pwd_conf) if pwd_conf else None
    if pwd_conf:
        if match_valid:
            st.markdown("<p class='validation-msg success-text'>Les mots de passe correspondent</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Confirmez votre mot de passe']) div[data-baseweb='input'] { border: 2px solid #28a745 !important; }</style>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='validation-msg error-text'>Ne correspond pas</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Confirmez votre mot de passe']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)

    if st.button("Créer mon compte", use_container_width=True):
        if email_valid and not email_exists and pwd_valid and match_valid:
            st.session_state.mock_db[email] = pwd
            st.session_state.step = "login"
            st.rerun()
    
    if st.button("Retour", key="back_signup"):
        st.session_state.step = "landing"
        st.rerun()

def show_login():
    st.markdown("<h1 class='main-title'>Connexion</h1>", unsafe_allow_html=True)
    
    email_log = st.text_input("Email", key="login_email")
    pwd_log = st.text_input("Mot de passe", type="password", key="login_pwd")
    
    # Validation Logic for Login
    account_exists = email_log in st.session_state.mock_db
    correct_pwd = st.session_state.mock_db.get(email_log) == pwd_log if email_log else False

    if st.button("Se connecter", use_container_width=True):
        if account_exists and correct_pwd:
            st.session_state.user_data["email"] = email_log
            st.session_state.step = "bac_selection"
            st.rerun()
        else:
            # Inline error styling if login fails
            st.markdown("<p class='validation-msg error-text'>Email ou mot de passe incorrect</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)

    if st.button("Retour", key="back_login"):
        st.session_state.step = "landing"
        st.rerun()

# --- REMAINING APP LOGIC (Bac, Options, Audit, Dashboard, Chat) ---
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
    st.markdown(f"## 📊 Niveau : {st.session_state.user_data['bac_type']}")
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
    style = st.text_area("Comment voulez-vous que votre tuteur vous enseigne ?", height=150)
    if st.button("Enregistrer mon profil", use_container_width=True):
        st.session_state.user_data["style"] = style
        st.session_state.step = "dashboard"
        st.rerun()

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

def show_subject_hub():
    if st.button("← Dashboard"):
        st.session_state.step = "dashboard"
        st.rerun()
    st.markdown(f"## 👨‍🏫 AI Professor")
    subjects = get_full_subject_list()
    subject_emojis = {"Mathématiques": "📐", "Physique": "⚛️", "SVT": "🧬", "Informatique": "💻", "Philosophie": "📜", "Arabe": "🇹🇳", "Français": "🇫🇷", "Anglais": "🇬🇧", "Économie": "📈", "Gestion": "💼", "Histoire-Géographie": "🌍", "Dessin": "🎨", "Allemand": "🇩🇪", "Espagnol": "🇪🇸", "Italien": "🇮🇹", "Russe": "🇷🇺", "Chinois": "🇨🇳"}
    cols = st.columns(3)
    for i, sub in enumerate(subjects):
        emoji = subject_emojis.get(sub, "📘")
        with cols[i % 3]:
            if st.button(f"{emoji} {sub}", key=f"sub_{sub}", use_container_width=True):
                st.session_state.selected_subject = sub
                st.session_state.step = "chat_diagnose"
                st.session_state.messages = []
                st.session_state.q_count = 0
                st.session_state.diag_step = "get_chapter"
                st.rerun()

def show_chat_diagnose():
    st.markdown(f"### 👨‍🏫 Tuteur : {st.session_state.selected_subject}")
    if st.session_state.get("diag_step") == "questioning":
        st.progress(st.session_state.q_count / 10, text=f"Diagnostic : {st.session_state.q_count}/10")
    if not st.session_state.get("messages"):
        intro = f"Asslema! Je suis ton tuteur en {st.session_state.selected_subject}. Quel chapitre étudions-nous ?"
        st.session_state.messages = [{"role": "assistant", "content": intro}]
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if prompt := st.chat_input("Réponds ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant"):
            if st.session_state.diag_step == "get_chapter":
                st.session_state.current_chapter = prompt
                st.session_state.diag_step = "questioning"
                st.session_state.q_count = 1
                response = f"D'accord, le chapitre **{prompt}**. Question 1: ..."
            elif st.session_state.q_count < 10:
                st.session_state.q_count += 1
                response = f"Question {st.session_state.q_count}: [Analyse...]"
            else:
                response = "Diagnostic terminé !"
                st.session_state.user_data["plan_ready"] = True
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

# --- ROUTER ---
pages = {
    "landing": show_landing, "signup": show_signup, "login": show_login,
    "bac_selection": show_bac_selection, "option_selection": show_option_selection,
    "level_audit": show_level_audit, "philosophy": show_philosophy,
    "dashboard": show_dashboard, "subject_hub": show_subject_hub,
    "chat_diagnose": show_chat_diagnose
}

if st.session_state.step in pages:
    pages[st.session_state.step]()
