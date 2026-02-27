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
    
    /* Remove focus glow and color change for ALL inputs and text areas */
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
    .success-text { color: #28a745; }
    
    /* Subscription Card Styling */
    .sub-card {
        background-color: #f8f9fa;
        padding: 30px;
        border-radius: 15px;
        border: 1px solid #eee;
        text-align: center;
        margin-bottom: 25px;
    }
    .sub-title { color: #10a37f; font-weight: 800; font-size: 24px; margin-bottom: 10px; }
    .sub-desc { color: #555; line-height: 1.6; font-size: 16px; }
    
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
    
    # --- EMAIL FIELD ---
    email = st.text_input("Email", key="signup_email", placeholder="exemple@gmail.com")
    email_valid = is_valid_email(email) if email else True # True when empty to avoid red on start
    
    if email and not email_valid:
        st.markdown("<p class='validation-msg error-text'>Format invalide, doit être : exemple@gmail.com</p>", unsafe_allow_html=True)
        # Injects CSS to turn the border red specifically for the Email input
        st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Email']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)
    elif email and email in st.session_state.mock_db:
        st.markdown("<p class='validation-msg error-text'>Cet email est déjà utilisé</p>", unsafe_allow_html=True)
        st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Email']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)

    # --- PASSWORD FIELD ---
    pwd = st.text_input("Mot de passe", type="password", key="signup_pwd")
    pwd_valid = len(pwd) >= 8 if pwd else True # True when empty to avoid red on start
    
    if pwd and not pwd_valid:
        st.markdown("<p class='validation-msg error-text'>Longueur invalide, minimum 8 caractères.</p>", unsafe_allow_html=True)
        # Injects CSS to turn the border red specifically for the Password input
        st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Mot de passe']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)

    pwd_conf = st.text_input("Confirmez votre mot de passe", type="password", key="signup_pwd_conf")
    match_valid = (pwd == pwd_conf) if pwd_conf else True

    if pwd_conf and not match_valid:
        st.markdown("<p class='validation-msg error-text'>Les mots de passe ne correspondent pas</p>", unsafe_allow_html=True)
        st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Confirmez votre mot de passe']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)

    # --- SUBMIT BUTTON ---
    # Inside show_signup()
    if st.button("Créer mon compte", use_container_width=True):
        if is_valid_email(email) and len(pwd) >= 8 and pwd == pwd_conf:
            st.session_state.mock_db[email] = {"pwd": pwd, "profile_complete": False, "data": {}}
            st.session_state.user_data = {"email": email}
            st.session_state.step = "curriculum_selection" # This is the change
            st.rerun()
        else:
            st.error("Veuillez corriger les erreurs avant de continuer.")
    
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
            if user_entry["profile_complete"]:
                st.session_state.step = "dashboard"
            else:
                st.session_state.step = "bac_selection"
            st.rerun()
        else:
            st.markdown("<p class='validation-msg error-text'>Email ou mot de passe incorrect</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)

    if st.button("Retour", key="back_login"):
        st.session_state.step = "landing"
        st.rerun()

# --- PROFILE SETUP FLOW ---
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
            st.session_state.step = "option_selection" # Continues the flow
            st.rerun()

def show_curriculum_selection():
    st.markdown("## 🌍 Quel est votre système ?")
    
    if st.button("🇹🇳 Baccalauréat Tunisien", use_container_width=True):
        st.session_state.user_data["curriculum"] = "Tunisien"
        st.session_state.step = "bac_selection" # Leads to Bac choice
        st.rerun()
        
    if st.button("🇫🇷 Baccalauréat Français", use_container_width=True):
        st.session_state.user_data["curriculum"] = "Français"
        st.session_state.step = "fr_level_selection" # New starting point
        st.rerun()

def show_fr_level_selection():
    st.markdown("## 📚 Votre niveau (Bac Français)")
    if st.button("Première", use_container_width=True):
        st.session_state.user_data["fr_level"] = "Première"
        st.session_state.step = "fr_voie_selection"
        st.rerun()
    if st.button("Terminale", use_container_width=True):
        st.session_state.user_data["fr_level"] = "Terminale"
        st.session_state.step = "fr_voie_selection"
        st.rerun()

def show_fr_voie_selection():
    st.markdown(f"## 🛣️ Sélectionnez votre voie ({st.session_state.user_data['fr_level']})")
    if st.button("Voie Générale", use_container_width=True):
        st.session_state.user_data["fr_voie"] = "Générale"
        st.session_state.step = "fr_specialites_selection"
        st.rerun()
    if st.button("Voie Technologique", use_container_width=True):
        st.session_state.user_data["fr_voie"] = "Technologique"
        st.session_state.step = "fr_serie_selection"
        st.rerun()

def show_fr_serie_selection():
    st.markdown("## 🔬 Choisissez votre série")
    series = ["STMG", "STI2D", "STL", "ST2S", "STD2A", "STHR"]
    for s in series:
        if st.button(s, use_container_width=True):
            st.session_state.user_data["fr_serie"] = s
            st.session_state.step = "level_audit" # This triggers the subject list we just built
            st.rerun()

def show_fr_specialites_selection():
    level = st.session_state.user_data.get("fr_level")
    limit = 3 if level == "Première" else 2
    
    st.markdown(f"## 🧪 Les spécialités ({level})")
    st.info(f"Veuillez choisir exactement **{limit}** spécialités.")
    
    specs = [
        "Mathématiques", "Physique-Chimie", "Sciences de la Vie et de la Terre",
        "Sciences Économiques et Sociales", "HGGSP", "Numérique et Sciences Informatiques",
        "Humanités, Littérature et Philosophie", "Langues étrangères approfondies"
    ]
    
    # Use checkboxes for multiple selection
    selected = []
    for spec in specs:
        if st.checkbox(spec, key=f"check_{spec}"):
            selected.append(spec)
    
    if st.button("Confirmer mes spécialités", use_container_width=True):
        if len(selected) == limit:
            st.session_state.user_data["fr_specialites"] = selected
            st.session_state.step = "level_audit"
            st.rerun()
        else:
            st.error(f"Vous devez sélectionner exactement {limit} spécialités (actuellement : {len(selected)}).")

def show_option_selection():
    st.markdown("## ✨ Choisissez votre Option")
    options = {"Allemand": "🇩🇪", "Espagnol": "🇪🇸", "Italien": "🇮🇹", "Russe": "🇷🇺", "Chinois": "🇨🇳", "Dessin": "🎨"}
    for opt, emoji in options.items():
        if st.button(f"{emoji} {opt}", use_container_width=True):
            st.session_state.user_data["selected_option"] = opt
            st.session_state.step = "level_audit"
            st.rerun()

FR_CORE_SUBJECTS = [
    "Français (1re)" if "Première" else "Philosophie", 
    "Histoire-Géographie", 
    "LVA (Anglais)", 
    "LVB", 
    "Enseignement Scientifique", 
    "EPS"
]

def get_full_subject_list():
    curriculum = st.session_state.user_data.get("curriculum")
    
    # 1. TUNISIAN FLOW
    if curriculum == "Tunisien":
        bac = st.session_state.user_data.get("bac_type")
        subjects = CORE_MAPPING.get(bac, []).copy()
        opt = st.session_state.user_data.get("selected_option")
        if opt: 
            subjects.append(opt)
        return subjects

    # 2. FRENCH FLOW
    elif curriculum == "Français":
        level = st.session_state.user_data.get("fr_level")
        voie = st.session_state.user_data.get("fr_voie")
        serie = st.session_state.user_data.get("fr_serie")

        # CASE A: STMG (Technologique)
        if voie == "Technologique" and serie == "STMG":
            return [
                "Français" if level == "Première" else "Philosophie",
                "Histoire-Géographie",
                "Mathématiques",
                "Langue Vivante A",
                "Langue Vivante B",
                "Management",
                "Sciences de Gestion et Numérique",
                "Droit et Économie",
                "EPS",
                "Enseignement Moral et Civique"
            ]

        # CASE B: Voie Générale
        elif voie == "Générale":
            subjects = [
                "Français" if level == "Première" else "Philosophie",
                "Histoire-Géographie",
                "LVA (Anglais)",
                "LVB",
                "Enseignement Scientifique",
                "EPS"
            ]
            specs = st.session_state.user_data.get("fr_specialites", [])
            subjects.extend(specs)
            return subjects
            
        # CASE C: Other Technologique series (Placeholder)
        elif voie == "Technologique":
            return [
                "Français" if level == "Première" else "Philosophie",
                "Histoire-Géographie",
                "LVA",
                "LVB",
                "Mathématiques",
                f"Spécialités {serie}",
                "EPS"
            ]
    
    return []

def show_level_audit():
    # 1. Safely determine which level name to display
    user_info = st.session_state.user_data
    curr = user_info.get("curriculum", "Tunisien")
    
    # Use bac_type for Tunisians, fr_level for French
    if curr == "Tunisien":
        level_display = user_info.get("bac_type", "Non défini")
    else:
        level_display = f"{user_info.get('fr_level', '')} {user_info.get('fr_voie', '')}"

    st.markdown(f"## 📊 Niveau : {level_display}")
    
    # 2. Get the subjects list (this uses your updated get_full_subject_list)
    subjects = get_full_subject_list()
    
    if not subjects:
        st.warning("Aucune matière trouvée pour ce profil.")
        if st.button("Retour au début"):
            st.session_state.step = "curriculum_selection"
            st.rerun()
        return

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
    # Added unique key for the text area
    style = st.text_area("Comment voulez-vous que votre tuteur vous enseigne ?", height=150, key="style_input")
    if st.button("Enregistrer mon profil", use_container_width=True):
        st.session_state.user_data["style"] = style
        email = st.session_state.user_data["email"]
        st.session_state.mock_db[email]["profile_complete"] = True
        st.session_state.mock_db[email]["data"] = st.session_state.user_data
        st.session_state.step = "dashboard"
        st.rerun()

# --- MAIN DASHBOARD & FEATURES ---

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
    if st.button("⭐ Abonnement", use_container_width=True):
        st.session_state.step = "subscription"
        st.rerun()
    if st.button("Déconnexion"):
        st.session_state.step = "landing"
        st.rerun()

def show_subscription():
    st.markdown("## 💎 Améliorez votre expérience")
    st.markdown("""
        <div class="sub-card">
            <div class="sub-title">Plan Premium</div>
            <div class="sub-desc">
                Accès étendu à notre modèle d’IA principal (raisonnement plus avancé, meilleure qualité d’apprentissage), 
                messages illimités, davantage de téléversements, mémoire plus longue.
            </div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Acheter", use_container_width=True):
        st.success("Redirection vers le paiement...")
        st.session_state.step = "dashboard"
        st.rerun()
    if st.button("← Retour au Dashboard", use_container_width=True):
        st.session_state.step = "dashboard"
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
    if st.button("← Quitter le chat"):
        st.session_state.step = "subject_hub"
        st.rerun()
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
    "landing": show_landing, 
    "signup": show_signup, 
    "login": show_login,
    "curriculum_selection": show_curriculum_selection,
    "bac_selection": show_bac_selection, 
    "fr_level_selection": show_fr_level_selection,
    "fr_voie_selection": show_fr_voie_selection,
    "fr_serie_selection": show_fr_serie_selection,
    "fr_specialites_selection": show_fr_specialites_selection,
    "option_selection": show_option_selection,
    "level_audit": show_level_audit, 
    "philosophy": show_philosophy,
    "dashboard": show_dashboard, 
    "subscription": show_subscription,
    "subject_hub": show_subject_hub, 
    "chat_diagnose": show_chat_diagnose
}

if st.session_state.step in pages:
    pages[st.session_state.step]()
