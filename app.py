import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client

# --- 1. INITIAL SETUP ---
st.set_page_config(page_title="KhirMinTaki", layout="centered")

# Initialize Session States
if "step" not in st.session_state:
    st.session_state.step = "login"
if "user_data" not in st.session_state:
    st.session_state.user_data = {}

# --- 2. STYLING (THE CLEAN LOOK) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Hide native menu */
    header, footer { visibility: hidden; }
    
    /* Box Styling for Dashboard */
    .nav-box {
        border: 1px solid #eee;
        padding: 40px 20px;
        border-radius: 15px;
        text-align: center;
        transition: 0.3s;
        background: #fdfdfd;
        cursor: pointer;
    }
    .nav-box:hover { border-color: #10a37f; background: #f9fbf9; }
    .locked { opacity: 0.5; cursor: not-allowed; background: #f5f5f5; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. PAGE FUNCTIONS ---

def show_login():
    st.markdown("<h1 style='text-align:center;'>KhirMinTaki</h1>", unsafe_allow_html=True)
    with st.container():
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter", use_container_width=True):
            if email and password:
                st.session_state.user_data["email"] = email
                st.session_state.step = "bac_selection"
                st.rerun()

def show_bac_selection():
    st.markdown("## Choisissez votre section Bac")
    options = ["Mathématiques", "Sciences Expérimentales", "Lettres", "Sciences Économiques et Gestion"]
    for opt in options:
        if st.button(opt, use_container_width=True):
            st.session_state.user_data["bac_type"] = opt
            st.session_state.step = "level_audit"
            st.rerun()

def show_level_audit():
    st.markdown(f"## Niveau : {st.session_state.user_data['bac_type']}")
    st.write("Indiquez votre niveau pour chaque matière :")
    
    subjects = ["Mathématiques", "Physique", "Sciences", "Anglais", "Français"]
    levels = {}
    
    for sub in subjects:
        levels[sub] = st.select_slider(f"{sub}", options=["Faible", "Intermédiaire", "Excellent"], value="Intermédiaire")
    
    if st.button("Suivant", use_container_width=True):
        st.session_state.user_data["levels"] = levels
        st.session_state.step = "philosophy"
        st.rerun()

def show_philosophy():
    st.markdown("## Votre style d'apprentissage")
    st.write("Comment voulez-vous que votre tuteur vous enseigne ?")
    style = st.text_area("Décrivez votre préférence (ex: patient, rigoureux, utilise beaucoup d'exemples...)", height=150)
    
    if st.button("Enregistrer mon profil", use_container_width=True):
        st.session_state.user_data["style"] = style
        # Here we would save to Supabase
        st.session_state.step = "dashboard"
        st.rerun()

def show_dashboard():
    st.markdown(f"## Bienvenue, {st.session_state.user_data['email'].split('@')[0]}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 AI Professor", use_container_width=True, help="Commencer à étudier"):
            st.session_state.step = "subject_hub"
            st.rerun()
        st.button("📄 Résumés (Verrouillé)", disabled=True, use_container_width=True)
    
    with col2:
        st.button("📝 Exercices (Verrouillé)", disabled=True, use_container_width=True)
        st.button("📅 Plans (Verrouillé)", disabled=True, use_container_width=True)

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
