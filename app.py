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
        "test@taki.com": {"pwd": "password123", "profile_complete": True, "data": {"bac_type": "Mathématiques", "is_premium": False}}
    }

# --- 2. DYNAMIC CSS (STRICTLY MATCHING YOURS) ---
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
    .success-text { color: #28a745; }
    
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
            st.session_state.mock_db[email] = {"pwd": pwd, "profile_complete": False, "data": {"is_premium": False}}
            st.session_state.step = "login"
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

# --- PROFILE FLOW (STRICTLY YOURS) ---
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
    style = st.text_area("Comment voulez-vous que votre tuteur vous enseigne ?", height=150, key="style_input")
    if st.button("Enregistrer mon profil", use_container_width=True):
        st.session_state.user_data["style"] = style
        email = st.session_state.user_data["email"]
        st.session_state.mock_db[email]["profile_complete"] = True
        st.session_state.mock_db[email]["data"] = st.session_state.user_data
        st.session_state.step = "dashboard"
        st.rerun()

# --- DASHBOARD & HUB (STRICTLY YOURS) ---

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
        st.session_state.user_data["is_premium"] = True
        st.success("Passé en Premium !")
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
                st.session_state.msg_count = 0
                st.session_state.diag_step = "get_chapter"
                st.rerun()

# --- THE SMART, PERSISTENT CHAT ---

def show_chat_diagnose():
    if st.button("← Quitter le chat"):
        st.session_state.step = "subject_hub"
        st.rerun()

    st.markdown(f"### 👨‍🏫 Tuteur : {st.session_state.selected_subject}")
    
    # DB LOAD logic inside your structure
    if not st.session_state.get("messages"):
        try:
            res = supabase.table("chat_history").select("*").eq("email", st.session_state.user_data["email"]).eq("subject", st.session_state.selected_subject).order("created_at").execute()
            if res.data:
                st.session_state.messages = [{"role": r["role"], "content": r["content"]} for r in res.data]
            else:
                intro = f"Asslema! Je suis ton tuteur en {st.session_state.selected_subject}. Quel chapitre étudions-nous ?"
                st.session_state.messages = [{"role": "assistant", "content": intro}]
        except:
            st.session_state.messages = [{"role": "assistant", "content": "Prêt pour le cours !"}]

    is_premium = st.session_state.user_data.get("is_premium", False)
    limit_reached = not is_premium and st.session_state.msg_count >= 3

    if st.session_state.get("diag_step") == "questioning":
        st.progress(st.session_state.q_count / 10, text=f"Diagnostic : {st.session_state.q_count}/10")
    
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if limit_reached:
        st.warning("Limite atteinte ! Passe au Premium pour continuer.")
        if st.button("⭐ Voir Premium"):
            st.session_state.step = "subscription"
            st.rerun()
    else:
        if prompt := st.chat_input("Réponds ici..."):
            if st.session_state.get("diag_step") == "learning":
                st.session_state.msg_count += 1
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                with st.spinner("Analyse en cours..."):
                    try:
                        profile = f"Prof tunisien. Elève: {st.session_state.user_data.get('bac_type')}. Mix Français/Darija."
                        
                        if is_premium:
                            model = genai.GenerativeModel('gemini-1.5-pro')
                            response_text = model.generate_content(f"{profile}\n\nUser: {prompt}").text
                        else:
                            res = groq_client.chat.completions.create(
                                messages=[{"role": "system", "content": profile}, {"role": "user", "content": prompt}],
                                model="llama3-8b-8192"
                            )
                            response_text = res.choices[0].message.content
                        
                        # PERSIST
                        supabase.table("chat_history").insert({"email": st.session_state.user_data["email"], "subject": st.session_state.selected_subject, "role": "user", "content": prompt}).execute()
                        supabase.table("chat_history").insert({"email": st.session_state.user_data["email"], "subject": st.session_state.selected_subject, "role": "assistant", "content": response_text}).execute()

                        # Step Management
                        if st.session_state.diag_step == "get_chapter":
                            st.session_state.diag_step = "questioning"
                            st.session_state.q_count = 1
                        elif st.session_state.diag_step == "questioning":
                            st.session_state.q_count += 1
                            if st.session_state.q_count >= 10:
                                st.session_state.diag_step = "learning"
                                st.session_state.user_data["plan_ready"] = True

                        st.markdown(response_text)
                        st.session_state.messages.append({"role": "assistant", "content": response_text})
                    except Exception as e:
                        st.error(f"API Error: {e}")
            st.rerun()

# --- ROUTER ---
pages = {
    "landing": show_landing, "signup": show_signup, "login": show_login,
    "bac_selection": show_bac_selection, "option_selection": show_option_selection,
    "level_audit": show_level_audit, "philosophy": show_philosophy,
    "dashboard": show_dashboard, "subscription": show_subscription,
    "subject_hub": show_subject_hub, "chat_diagnose": show_chat_diagnose
}

if st.session_state.step in pages:
    pages[st.session_state.step]()
