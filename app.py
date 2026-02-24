import streamlit as st
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
    st.session_state.step = "login"
if "user_data" not in st.session_state:
    st.session_state.user_data = {}

# SUBJECT MAPPING (The Brain of the Curriculum)
BAC_MAPPING = {
    "Mathématiques": [
        "Mathématiques", "Physique", "SVT", "Informatique", 
        "Philosophie", "Arabe", "Français", "Anglais", 
        "Dessin", "Allemand 🇩🇪", "Espagnol 🇪🇸", "Italien 🇮🇹"
    ],
    "Sciences Expérimentales": [
        "SVT", "Physique", "Mathématiques", "Informatique", 
        "Philosophie", "Arabe", "Français", "Anglais", 
        "Dessin", "Allemand 🇩🇪", "Espagnol 🇪🇸", "Italien 🇮🇹"
    ],
    "Sciences Économiques et Gestion": [
        "Économie", "Gestion", "Mathématiques", "Informatique", 
        "Histoire-Géographie", "Philosophie", "Arabe", "Français", 
        "Anglais", "Dessin", "Allemand 🇩🇪", "Espagnol 🇪🇸", "Italien 🇮🇹"
    ],
    "Lettres": [
        "Arabe", "Philosophie", "Histoire-Géographie", "Français", 
        "Anglais", "Allemand 🇩🇪", "Espagnol 🇪🇸", "Italien 🇮🇹", "Dessin"
    ]
}

# --- 2. STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    header, footer { visibility: hidden; }
    .main-title { text-align: center; font-weight: 800; font-size: 40px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PAGE FUNCTIONS ---

def show_login():
    st.markdown("<h1 class='main-title'>KhirMinTaki</h1>", unsafe_allow_html=True)
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter", use_container_width=True):
        if email and password:
            st.session_state.user_data["email"] = email
            st.session_state.step = "bac_selection"
            st.rerun()

def show_bac_selection():
    st.markdown("## Choisissez votre section Bac")
    for opt in BAC_MAPPING.keys():
        if st.button(opt, use_container_width=True):
            st.session_state.user_data["bac_type"] = opt
            st.session_state.step = "level_audit"
            st.rerun()

def show_level_audit():
    st.markdown(f"## Niveau : {st.session_state.user_data['bac_type']}")
    st.write("Indiquez votre niveau pour **chaque** matière :")
    
    current_bac = st.session_state.user_data['bac_type']
    subjects_to_audit = BAC_MAPPING.get(current_bac, [])
    
    levels = {}
    for sub in subjects_to_audit:
        levels[sub] = st.select_slider(
            f"Niveau en **{sub}**", 
            options=["Faible", "Intermédiaire", "Excellent"], 
            value="Intermédiaire",
            key=f"audit_{sub}"
        )
        st.markdown("---")
    
    if st.button("Confirmer mon profil", use_container_width=True):
        st.session_state.user_data["levels"] = levels
        st.session_state.step = "philosophy"
        st.rerun()

def show_philosophy():
    st.markdown("## Votre style d'apprentissage")
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
        st.button("📄 Résumés (Verrouillé)", disabled=True, use_container_width=True)
    with col2:
        st.button("📝 Exercices (Verrouillé)", disabled=True, use_container_width=True)
        st.button("📅 Plans (Verrouillé)", disabled=True, use_container_width=True)

def show_subject_hub():
    if st.button("← Retour au Dashboard"):
        st.session_state.step = "dashboard"
        st.rerun()
    st.markdown(f"## AI Professor: {st.session_state.user_data['bac_type']}")
    
    subs = BAC_MAPPING.get(st.session_state.user_data['bac_type'], [])
    cols = st.columns(3)
    for i, sub in enumerate(subs):
        with cols[i % 3]:
            if st.button(f"📘 {sub}", key=f"sub_{sub}", use_container_width=True):
                st.session_state.selected_subject = sub
                st.session_state.step = "chat_diagnose"
                st.session_state.messages = []
                st.rerun()

def show_chat_diagnose():
    st.markdown(f"### 👨‍🏫 Tuteur de {st.session_state.selected_subject}")
    if not st.session_state.get("messages"):
        intro = f"Asslema! Je suis ton tuteur en {st.session_state.selected_subject}. Quel chapitre étudions-nous ?"
        st.session_state.messages = [{"role": "assistant", "content": intro}]

    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if prompt := st.chat_input("Réponds ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

# --- 4. THE STEP ROUTER ---
if st.session_state.step == "login":
    show_login()
elif st.session_state.step == "bac_selection":
    show_bac_selection()
elif st.session_state.step == "level_audit":
    show_level_audit()
elif st.session_state.step == "philosophy":
    show_philosophy()
elif st.session_state.step == "dashboard":
    show_dashboard()
elif st.session_state.step == "subject_hub":
    show_subject_hub()
elif st.session_state.step == "chat_diagnose":
    show_chat_diagnose()
