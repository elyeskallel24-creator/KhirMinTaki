import streamlit as st
import re
import google.generativeai as genai
from groq import Groq
from supabase import create_client

# --- 1. INITIAL SETUP & CONNECTIONS ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Erreur de configuration : {e}")

st.set_page_config(page_title="KhirMinTaki", layout="centered")

# Initialize Session State
if "step" not in st.session_state: st.session_state.step = "landing"
if "user_data" not in st.session_state: st.session_state.user_data = {}
if "mock_db" not in st.session_state:
    st.session_state.mock_db = {
        "test@taki.com": {"pwd": "password123", "profile_complete": True, "data": {"bac_type": "Mathématiques", "is_premium": False}}
    }

# --- 2. STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    header, footer { visibility: hidden; }
    .main-title { text-align: center; font-weight: 800; font-size: 40px; margin-bottom: 20px; color: #10a37f; }
    .sub-card { background-color: #f8f9fa; padding: 30px; border-radius: 15px; border: 1px solid #eee; text-align: center; margin-bottom: 25px; }
    .sub-title { color: #10a37f; font-weight: 800; font-size: 24px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

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
    email = st.text_input("Email")
    pwd = st.text_input("Mot de passe", type="password")
    pwd_conf = st.text_input("Confirmez le mot de passe", type="password")
    if st.button("S'inscrire", use_container_width=True):
        if email and len(pwd) >= 8 and pwd == pwd_conf:
            st.session_state.mock_db[email] = {"pwd": pwd, "profile_complete": False, "data": {"is_premium": False}}
            st.session_state.step = "login"
            st.rerun()
    if st.button("Retour"):
        st.session_state.step = "landing"
        st.rerun()

def show_login():
    st.markdown("<h1 class='main-title'>Connexion</h1>", unsafe_allow_html=True)
    email_log = st.text_input("Email")
    pwd_log = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter", use_container_width=True):
        user = st.session_state.mock_db.get(email_log)
        if user and user["pwd"] == pwd_log:
            st.session_state.user_data = user["data"]
            st.session_state.user_data["email"] = email_log
            st.session_state.step = "dashboard" if user["profile_complete"] else "bac_selection"
            st.rerun()
        else: st.error("Identifiants incorrects")
    if st.button("Retour"):
        st.session_state.step = "landing"
        st.rerun()

# --- PROFILE & DASHBOARD ---
CORE_MAPPING = {"Mathématiques": ["Maths", "Physique"], "Sciences": ["SVT", "Physique"]}

def show_bac_selection():
    st.markdown("## 🎓 Ta section Bac")
    for opt in CORE_MAPPING.keys():
        if st.button(opt, use_container_width=True):
            st.session_state.user_data["bac_type"] = opt
            st.session_state.user_data["levels"] = {sub: "Satisfaisant" for sub in CORE_MAPPING[opt]}
            st.session_state.user_data["style"] = "Pédagogique"
            st.session_state.mock_db[st.session_state.user_data["email"]]["profile_complete"] = True
            st.session_state.step = "dashboard"
            st.rerun()

def show_dashboard():
    st.markdown(f"## Bienvenue, {st.session_state.user_data.get('email', 'Étudiant')}")
    if st.button("👨‍🏫 AI Professor", use_container_width=True):
        st.session_state.step = "subject_hub"
        st.rerun()
    if st.button("⭐ Abonnement", use_container_width=True):
        st.session_state.step = "subscription"
        st.rerun()
    if st.button("Déconnexion"):
        st.session_state.step = "landing"
        st.rerun()

def show_subscription():
    st.markdown("## 💎 Premium")
    st.markdown('<div class="sub-card"><div class="sub-title">Plan Premium</div><p>Accès illimité et IA avancée</p></div>', unsafe_allow_html=True)
    if st.button("Devenir Premium", use_container_width=True):
        st.session_state.user_data["is_premium"] = True
        st.success("Félicitations !")
        st.session_state.step = "dashboard"
        st.rerun()
    if st.button("Retour"):
        st.session_state.step = "dashboard"
        st.rerun()

def show_subject_hub():
    st.markdown("## 📚 Matières")
    subjects = CORE_MAPPING.get(st.session_state.user_data.get("bac_type", "Mathématiques"), ["Maths"])
    for s in subjects:
        if st.button(s, use_container_width=True):
            st.session_state.selected_subject = s
            st.session_state.messages = [] # Will be populated from DB
            st.session_state.msg_count = 0
            st.session_state.diag_step = "get_chapter"
            st.session_state.step = "chat_diagnose"
            st.rerun()
    if st.button("Retour"):
        st.session_state.step = "dashboard"
        st.rerun()

# --- THE PERSISTENT SMART CHAT ---

def show_chat_diagnose():
    if st.button("← Quitter"):
        st.session_state.step = "subject_hub"
        st.rerun()

    st.markdown(f"### 👨‍🏫 Tuteur : {st.session_state.selected_subject}")
    
    # 1. LOAD FROM SUPABASE
    if not st.session_state.get("messages"):
        try:
            res = supabase.table("chat_history").select("*").eq("email", st.session_state.user_data["email"]).eq("subject", st.session_state.selected_subject).order("created_at").execute()
            if res.data:
                st.session_state.messages = [{"role": r["role"], "content": r["content"]} for r in res.data]
            else:
                st.session_state.messages = [{"role": "assistant", "content": f"Asslema! Quel chapitre de {st.session_state.selected_subject} étudions-nous ?"}]
        except: st.session_state.messages = [{"role": "assistant", "content": "Prêt à commencer !"}]

    is_premium = st.session_state.user_data.get("is_premium", False)
    limit_reached = not is_premium and st.session_state.msg_count >= 3

    # Display History
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    if limit_reached:
        st.warning("Limite gratuite atteinte. Passez au Premium !")
        if st.button("⭐ Voir Offres"):
            st.session_state.step = "subscription"
            st.rerun()
    else:
        if prompt := st.chat_input("Réponds ici..."):
            if st.session_state.get("diag_step") == "learning": st.session_state.msg_count += 1
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("assistant"):
                with st.spinner("Réflexion..."):
                    # SYSTEM PROMPT
                    profile = f"Prof tunisien. Elève: {st.session_state.user_data.get('bac_type')}. Mix Français/Darija."
                    
                    # API ROUTING
                    if is_premium:
                        model = genai.GenerativeModel('gemini-1.5-pro')
                        response_text = model.generate_content(f"{profile}\n\nUser: {prompt}").text
                    else:
                        res = groq_client.chat.completions.create(
                            messages=[{"role": "system", "content": profile}, {"role": "user", "content": prompt}],
                            model="llama3-8b-8192"
                        )
                        response_text = res.choices[0].message.content
                    
                    # PERSIST TO SUPABASE
                    supabase.table("chat_history").insert({"email": st.session_state.user_data["email"], "subject": st.session_state.selected_subject, "role": "user", "content": prompt}).execute()
                    supabase.table("chat_history").insert({"email": st.session_state.user_data["email"], "subject": st.session_state.selected_subject, "role": "assistant", "content": response_text}).execute()

                    # Logic transitions
                    if st.session_state.diag_step == "get_chapter": st.session_state.diag_step = "learning"

                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()

# --- ROUTER ---
pages = {
    "landing": show_landing, "signup": show_signup, "login": show_login,
    "bac_selection": show_bac_selection, "dashboard": show_dashboard,
    "subscription": show_subscription, "subject_hub": show_subject_hub,
    "chat_diagnose": show_chat_diagnose
}
pages[st.session_state.step]()
