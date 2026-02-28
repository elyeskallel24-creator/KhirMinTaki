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
            # 1. Ensure user_data is a dictionary even if "data" was empty
            db_data = user_entry.get("data", {})
            
            # 2. Use .update() to merge database info into the current session 
            # without deleting what's already there
            st.session_state.user_data.update(db_data)
            
            # 3. Explicitly set the email to ensure it's always present
            st.session_state.user_data["email"] = email_log
            
            # 4. Check profile status and redirect
            if user_entry.get("profile_complete"):
                st.session_state.step = "dashboard"
            else:
                st.session_state.step = "curriculum_selection"
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
    
    # Displaying the Tunisian Bac sections
    for opt in CORE_MAPPING.keys():
        if st.button(opt, use_container_width=True):
            st.session_state.user_data["bac_type"] = opt
            st.session_state.step = "option_selection"
            st.rerun()
    
    # Visual separator for the back action
    st.markdown("---")
    
    if st.button("← Retour au choix du système", key="back_to_curr"):
        # This allows the user to switch back to the French Bac if needed
        st.session_state.step = "curriculum_selection"
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
    st.write("Sélectionnez votre classe actuelle pour adapter le programme.")

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Première", use_container_width=True):
            # Enregistre le niveau
            st.session_state.user_data["fr_level"] = "Première"
            # Direction le choix de la voie (Générale ou Techno)
            st.session_state.step = "fr_voie_selection"
            st.rerun()
            
    with col2:
        if st.button("Terminale", use_container_width=True):
            # Enregistre le niveau
            st.session_state.user_data["fr_level"] = "Terminale"
            # Direction le choix de la voie (Générale ou Techno)
            st.session_state.step = "fr_voie_selection"
            st.rerun()

    st.markdown("---")
    if st.button("← Retour au choix du curriculum"):
        st.session_state.step = "curriculum_selection"
        st.rerun()
def show_fr_voie_selection():
    # Récupération du niveau (Première ou Terminale) pour l'affichage
    level = st.session_state.user_data.get('fr_level', '')
    st.markdown(f"## 🛣️ Sélectionnez votre voie ({level})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Voie Générale", use_container_width=True):
            st.session_state.user_data["fr_voie"] = "Générale"
            # Les élèves en voie générale doivent choisir leurs spécialités
            st.session_state.step = "fr_specialites_selection"
            st.rerun()
            
    with col2:
        if st.button("Voie Technologique", use_container_width=True):
            st.session_state.user_data["fr_voie"] = "Technologique"
            # C'est ici que l'on redirige vers le choix de la série (STMG, STI2D, etc.)
            st.session_state.step = "fr_serie_selection"
            st.rerun()

    if st.button("← Retour"):
        st.session_state.step = "fr_level_selection"
        st.rerun()

def show_fr_serie_selection():
    st.markdown("## 🔬 Choisissez votre série")
    
    # On définit la liste des séries
    series = ["STMG", "STI2D", "STL", "ST2S", "STD2A", "STHR"]
    
    # On crée un bouton pour chaque série de la liste
    for s in series:
        if st.button(s, use_container_width=True):
            # Enregistre exactement le nom de la série (ex: "ST2S")
            st.session_state.user_data["fr_serie"] = s
            
            # Redirige vers l'audit
            st.session_state.step = "level_audit"
            
            # Relance pour appliquer les changements
            st.rerun()

def show_fr_specialites_selection():
    level = st.session_state.user_data.get("fr_level")
    # Définit la limite selon le niveau choisi précédemment
    limit = 3 if level == "Première" else 2
    
    st.markdown(f"## 🧪 Les spécialités ({level})")
    st.info(f"Veuillez choisir exactement **{limit}** spécialités.")
    
    specs = [
        "Mathématiques", "Physique-Chimie", "Sciences de la Vie et de la Terre",
        "Sciences Économiques et Sociales", "HGGSP", "Numérique et Sciences Informatiques",
        "Humanités, Littérature et Philosophie", "Langues étrangères approfondies"
    ]
    
    # Création des cases à cocher
    selected = []
    for spec in specs:
        if st.checkbox(spec, key=f"check_{spec}"):
            selected.append(spec)
    
    st.markdown("---") # Séparateur visuel

    # --- LE BLOC DE REDIRECTION ---
    if st.button("Confirmer mes spécialités", use_container_width=True):
        if len(selected) == limit:
            # Enregistre les choix dans les données utilisateur
            st.session_state.user_data["fr_specialites"] = selected
            
            # Change l'étape du routeur pour afficher l'audit des matières
            st.session_state.step = "level_audit"
            
            # Relance l'application pour afficher la nouvelle page
            st.rerun()
        else:
            # Message d'erreur si le compte n'est pas bon
            st.error(f"Attention : vous devez sélectionner exactement {limit} spécialités (actuellement : {len(selected)}).")

def show_option_selection():
    st.markdown("## ✨ Choisissez votre Option")
    options = {"Allemand": "🇩🇪", "Espagnol": "🇪🇸", "Italien": "🇮🇹", "Russe": "🇷🇺", "Chinois": "🇨🇳", "Dessin": "🎨"}
    for opt, emoji in options.items():
        if st.button(f"{emoji} {opt}", use_container_width=True):
            st.session_state.user_data["selected_option"] = opt
            st.session_state.step = "level_audit"
            st.rerun()

def get_full_subject_list():
    curriculum = st.session_state.user_data.get("curriculum")
    
    # 1. FLUX TUNISIEN
    if curriculum == "Tunisien":
        bac = st.session_state.user_data.get("bac_type")
        subjects = CORE_MAPPING.get(bac, []).copy()
        opt = st.session_state.user_data.get("selected_option")
        if opt: 
            subjects.append(opt)
        return subjects

    # 2. FLUX FRANÇAIS
    elif curriculum == "Français":
        level = st.session_state.user_data.get("fr_level")
        voie = st.session_state.user_data.get("fr_voie")
        serie = st.session_state.user_data.get("fr_serie")

        # --- CAS : STHR (Hôtellerie et Restauration) ---
        if voie == "Technologique" and serie == "STHR":
            return [
                "Français" if level == "Première" else "Philosophie",
                "Histoire-Géographie",
                "Mathématiques",
                "Langue Vivante A",
                "Langue Vivante B",
                "EPS (Sport)",
                "Enseignement Moral et Civique (EMC)",
                "Sciences et Technologies de l’Hôtellerie et de la Restauration (STHR)",
                "Cuisine et Service / Travaux Pratiques",
                "Gestion et Mercatique appliquée à l’Hôtellerie",
                "Projet professionnel / atelier pratique"
            ]

        # --- CAS : STD2A (Design) ---
        elif voie == "Technologique" and serie == "STD2A":
            return [
                "Français" if level == "Première" else "Philosophie",
                "Histoire-Géographie",
                "Mathématiques",
                "Langue Vivante A",
                "Langue Vivante B",
                "EPS (Sport)",
                "Enseignement Moral et Civique (EMC)",
                "Création et Culture Design (CCD)",
                "Arts Appliqués et Projet Artistique",
                "Technologie et Méthodologie de Projet",
                "Travaux pratiques / Atelier"
            ]

        # --- CAS : ST2S (Santé-Social) ---
        elif voie == "Technologique" and serie == "ST2S":
            return [
                "Français" if level == "Première" else "Philosophie",
                "Histoire-Géographie",
                "Mathématiques",
                "Langue Vivante A",
                "Langue Vivante B",
                "EPS (Sport)",
                "Enseignement Moral et Civique (EMC)",
                "Sciences et Techniques Sanitaires et Sociales",
                "Biologie et Physiopathologie Humaines",
                "Psychologie / Sociologie appliquée",
                "Travaux pratiques / projets santé-social"
            ]

        # --- CAS : STL (Laboratoire) ---
        elif voie == "Technologique" and serie == "STL":
            return [
                "Français" if level == "Première" else "Philosophie",
                "Histoire-Géographie",
                "Mathématiques",
                "Langue Vivante A",
                "Langue Vivante B",
                "EPS (Sport)",
                "Enseignement Moral et Civique (EMC)",
                "Sciences Physiques et Chimiques",
                "Biotechnologies ou SPCL"
            ]

        # --- CAS : STI2D (Industrie) ---
        elif voie == "Technologique" and serie == "STI2D":
            return [
                "Français" if level == "Première" else "Philosophie",
                "Histoire-Géographie",
                "Mathématiques",
                "Langue Vivante A",
                "Langue Vivante B",
                "Physique-Chimie",
                "Innovation Technologique",
                "Ingénierie et Développement Durable",
                "EPS",
                "Enseignement Moral et Civique",
                "Sciences Physiques et Mathématiques appliquées"
            ]

        # --- CAS : STMG (Gestion) ---
        elif voie == "Technologique" and serie == "STMG":
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

        # --- CAS : VOIE GÉNÉRALE (Spécialités) ---
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
            
    return []
def show_level_audit():
    user_info = st.session_state.user_data
    curr = user_info.get("curriculum", "Tunisien")
    
    # 1. Détermination dynamique du titre
    if curr == "Tunisien":
        # Pour les Tunisiens, on affiche la section (ex: Mathématiques)
        level_display = user_info.get("bac_type", "Baccalauréat")
    else:
        # Pour les Français :
        # On récupère le niveau (1re/Term)
        level = user_info.get('fr_level', '')
        # On récupère la série (STMG, etc.) ou la voie (Générale) si la série n'existe pas
        branch = user_info.get('fr_serie', user_info.get('fr_voie', ''))
        level_display = f"{level} {branch}"

    st.markdown(f"## 📊 Niveau : {level_display}")
    
    # 2. Récupération de la liste des matières
    subjects = get_full_subject_list()
    
    if not subjects:
        st.error("Erreur : Impossible de charger les matières. Veuillez recommencer la sélection.")
        if st.button("Retour au menu"):
            st.session_state.step = "curriculum_selection"
            st.rerun()
        return

    # 3. Affichage des Sliders d'évaluation
    assessment_levels = ["Insuffisant", "Fragile", "Satisfaisant", "Bien", "Très bien", "Excellent"]
    levels = {}
    
    st.info("Évaluez honnêtement votre niveau actuel dans chaque matière pour que l'IA puisse s'adapter.")
    
    for sub in subjects:
        levels[sub] = st.select_slider(
            f"Votre niveau en **{sub}**",
            options=assessment_levels,
            value="Satisfaisant",
            key=f"aud_{sub}"
        )
        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        
    # 4. Bouton de validation
    if st.button("Confirmer mon profil", use_container_width=True):
        st.session_state.user_data["levels"] = levels
        st.session_state.step = "philosophy"
        st.rerun()

def show_philosophy():
    st.markdown("## 🧠 Votre philosophie d'apprentissage")
    st.write("Décrivez en détail comment vous souhaitez que votre professeur IA interagisse avec vous.")

    # 1. Logic to sync text and character count instantly
    if "temp_philosophy" not in st.session_state:
        st.session_state.temp_philosophy = ""

    # This function is triggered every time a key is pressed (if supported) 
    # or the widget loses focus. 
    # To get "real-time" in Streamlit, we ensure the value is tracked.
    user_philosophy = st.text_area(
        "Ma méthode préférée...",
        value=st.session_state.temp_philosophy,
        placeholder="Soyez précis : 'Je veux quelqu'un qui me donne des astuces pour gagner du temps et qui m'encourage...'",
        height=150,
        key="philosophy_area"
    )

    # Update the internal state
    st.session_state.temp_philosophy = user_philosophy
    
    # 2. Character Count and Progress Bar
    char_count = len(user_philosophy)
    progress = min(char_count / 80, 1.0)
    
    # Visual feedback
    st.progress(progress)
    
    if char_count < 80:
        remaining = 80 - char_count
        st.warning(f"✍️ Encore {remaining} caractères pour débloquer la suite.")
    else:
        st.success("✅ Parfait ! Votre profil est complet.")

    # 3. Validation Button
    if st.button("Confirmer et accéder au Dashboard", 
                 use_container_width=True, 
                 disabled=(char_count < 80)):
        
        st.session_state.user_data["philosophy"] = user_philosophy
        st.session_state.user_data["profile_complete"] = True
        st.session_state.step = "dashboard"
        st.balloons()
        st.rerun()

    if st.button("← Retour"):
        st.session_state.step = "level_audit"
        st.rerun()
# --- MAIN DASHBOARD & FEATURES ---

def show_dashboard():
    # Safely get the email; if not found, default to "Étudiant"
    user_email = st.session_state.user_data.get('email', 'Étudiant@taki.com')
    
    # Extract the name before the '@' symbol
    display_name = user_email.split('@')[0]
    
    st.markdown(f"## Bienvenue, {display_name}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👨‍🏫 AI Professor", use_container_width=True):
            st.session_state.step = "subject_hub"
            st.rerun()
        st.button("📄 Résumés (🔒)", disabled=True, use_container_width=True)
        
    with col2:
        st.button("📝 Exercices (🔒)", disabled=True, use_container_width=True)
        plan_ready = st.session_state.user_data.get("plan_ready")
        if st.button("📅 Plans" if plan_ready else "📅 Plans (🔒)", 
                     disabled=not plan_ready, 
                     use_container_width=True):
            st.session_state.step = "view_plan"
            st.rerun()
            
    st.markdown("<hr>", unsafe_allow_html=True)
    
    if st.button("⭐ Abonnement", use_container_width=True):
        st.session_state.step = "subscription"
        st.rerun()
        
    if st.button("Déconnexion"):
        # Clear sensitive data and return to landing
        st.session_state.user_data = {}
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
    # Bouton de retour au tableau de bord
    if st.button("← Dashboard"):
        st.session_state.step = "dashboard"
        st.rerun()
        
    st.markdown(f"## 👨‍🏫 AI Professor")
    
    # Récupère dynamiquement la liste des matières selon le profil utilisateur
    subjects = get_full_subject_list()
    
    # --- DICTIONNAIRE COMPLET DES EMOJIS ---
    subject_emojis = {
        # Tronc Commun & Tunisien
        "Mathématiques": "📐", "Physique": "⚛️", "Physique-Chimie": "🧪", 
        "SVT": "🧬", "Informatique": "💻", "Philosophie": "📜",
        "Arabe": "🇹🇳", "Français": "🇫🇷", "Anglais": "🇬🇧", "Allemand": "🇩🇪", "Espagnol": "🇪🇸", "Italien": "🇮🇹", "Russe": "🇷🇺", "Chinois": "🇨🇳",
        "Économie": "📈", "Gestion": "💼", "Histoire-Géographie": "🌍", 
        "LVA (Anglais)": "🇬🇧", "LVB": "🌍", "EPS": "🏃", "EPS (Sport)": "🏃",
        "Enseignement Moral et Civique (EMC)": "🗳️", "Enseignement Scientifique": "🧬",

        # Spécificités STHR (Hôtellerie-Restauration)
        "Sciences et Technologies de l’Hôtellerie et de la Restauration (STHR)": "🏨",
        "Cuisine et Service / Travaux Pratiques": "👨‍🍳",
        "Gestion et Mercatique appliquée à l’Hôtellerie": "📊",
        "Projet professionnel / atelier pratique": "💼",

        # Autres Séries Technologiques (STI2D, STMG, ST2S, STD2A, STL)
        "Management": "🏢", 
        "Sciences de Gestion et Numérique": "📊", 
        "Droit et Économie": "⚖️",
        "Innovation Technologique": "🛠️", 
        "Ingénierie et Développement Durable": "🌱",
        "Sciences Physiques et Mathématiques appliquées": "🔬",
        "Sciences et Techniques Sanitaires et Sociales": "🏥",
        "Biologie et Physiopathologie Humaines": "🫀",
        "Création et Culture Design (CCD)": "🎨",
        "Arts Appliqués et Projet Artistique": "🖌️",
        "Technologie et Méthodologie de Projet": "📐",
        "Travaux pratiques / Atelier": "🏗️",
        "Sciences Physiques et Chimiques": "🧪",
        "Biotechnologies ou SPCL": "🧪"
    }
    
    # Affichage en grille de 3 colonnes
    cols = st.columns(3)
    for i, sub in enumerate(subjects):
        # Récupère l'émoji correspondant ou un livre bleu par défaut
        emoji = subject_emojis.get(sub, "📘")
        
        with cols[i % 3]:
            # Création du bouton pour chaque matière
            if st.button(f"{emoji} {sub}", key=f"sub_{sub}", use_container_width=True):
                # Configuration de la session pour le diagnostic IA
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

def show_view_plan():
    st.markdown("## 📅 Votre Plan de Révision")
    st.write("Voici votre programme personnalisé basé sur le diagnostic.")
    
    # Optional: Check if the user actually has a plan
    if st.session_state.user_data.get("plan_ready"):
        st.success("Votre plan est prêt ! Voici vos prochaines étapes...")
        # You can add more details here later
    else:
        st.info("Complétez un diagnostic avec l'AI Professor pour générer votre plan.")

    if st.button("← Retour au Dashboard", use_container_width=True):
        st.session_state.step = "dashboard"
        st.rerun()

# --- ROUTER ---
# This dictionary maps the step name to the corresponding function.
# Ensure all these functions are defined above this block.
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
    "chat_diagnose": show_chat_diagnose,
    "view_plan": show_view_plan,
}

# 1. Get the current step safely (defaults to "landing" if not set)
current_step = st.session_state.get("step", "landing")

# 2. Check if the current step exists in our mapping
if current_step in pages:
    # 3. Call the function associated with the step
    pages[current_step]()
else:
    # 4. Fallback UI if a step is misspelled or missing
    st.error(f"⚠️ Erreur de navigation : L'étape '{current_step}' est introuvable.")
    st.info("La session a peut-être expiré ou une redirection est mal configurée.")
    
    if st.button("Retour à l'accueil", use_container_width=True):
        st.session_state.step = "landing"
        st.rerun()
