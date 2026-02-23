import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
from fpdf import FPDF
import streamlit.components.v1 as components
from PIL import Image

# --- 1. SETUP CONNECTIONS ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Connection Error: Check Secrets.")

# --- 2. THE CUSTOM FONT & MINIMALIST CSS ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #ffffff;
        color: #000000;
    }

    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #f0f0f0; }
    [data-testid="stSidebar"] * { color: #000000 !important; font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .typewriter-container {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 24px;
        color: #000000;
        height: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ROTATING TYPEWRITER COMPONENT ---
def typewriter_effect():
    html_code = """
    <div class="typewriter-container" id="typewriter"></div>
    <script>
        const textElement = document.getElementById("typewriter");
        const words = ["KhirMinTaki", "A9ra khir", "A9ra asra3"];
        let wordIndex = 0;
        let charIndex = 0;
        let isDeleting = false;
        let typeSpeed = 150;

        function type() {
            const currentWord = words[wordIndex];
            if (isDeleting) {
                textElement.textContent = currentWord.substring(0, charIndex - 1);
                charIndex--;
                typeSpeed = 100;
            } else {
                textElement.textContent = currentWord.substring(0, charIndex + 1);
                charIndex++;
                typeSpeed = 150;
            }

            if (!isDeleting && charIndex === currentWord.length) {
                isDeleting = true;
                typeSpeed = 2000;
            } else if (isDeleting && charIndex === 0) {
                isDeleting = false;
                wordIndex = (wordIndex + 1) % words.length;
                typeSpeed = 500;
            }

            setTimeout(type, typeSpeed);
        }
        type();
    </script>
    <style>
        .typewriter-container { font-family: 'Inter', sans-serif; font-weight: 600; font-size: 24px; color: #000000; }
    </style>
    """
    components.html(html_code, height=50)

# --- 4. LOGIN GATE ---
if "user_email" not in st.session_state:
    typewriter_effect()
    st.write("Bienvenue. Veuillez entrer votre email pour accéder à votre espace d'apprentissage.")
    
    email_input = st.text_input("Email", placeholder="exemple@email.com")
    if st.button("Commencer"):
        if email_input:
            try:
                supabase.table("users").upsert({"email": email_input}).execute()
                st.session_state.user_email = email_input
                st.rerun()
            except Exception as e:
                st.error("Erreur de connexion.")
        else:
            st.error("Veuillez entrer un email valide.")
    st.stop()

# --- 5. NAVIGATION & LOGOUT ---
st.sidebar.markdown("### **KhirMinTaki**") 
st.sidebar.caption(f"Connecté: {st.session_state.user_email}")

if st.sidebar.button("Déconnexion"):
    del st.session_state.user_email
    st.rerun()

chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Chapitres", ["Sélectionner..."] + chapter_names)

num_mastered = 0
try:
    all_sessions = supabase.table("student_sessions").select("id").eq("user_email", st.session_state.user_email).execute()
    num_mastered = len(all_sessions.data)
except:
    num_mastered = 0

# --- 6. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    user_display_name = st.session_state.user_email.split('@')[0].capitalize()
    st.write(f"### **Bienvenue, {user_display_name}**") 
    st.write("Sélectionnez un module pour commencer.")
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("Niveau")
        st.write(f"**{'Expert' if num_mastered > 2 else 'Apprenti'}**")
    with c2:
        st.write("Progression")
        st.write(f"**{num_mastered} chapitres**")
    with c3:
        st.write("Total Points")
        st.write(f"**{num_mastered * 100}**")

else:
    chapter_id = chapters_data.data[chapter_names.index(selected_chapter)]['id']
    existing = supabase.table("student_sessions").select("*").eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).execute()
    
    if "messages" not in st.session_state: st.session_state.messages = []
    
    if existing.data:
        st.session_state.study_plan = existing.data[0].get('study_plan')
        st.session_state.resume = existing.data[0].get('course_resume')
    else:
        st.session_state.study_plan = st.session_state.get('study_plan', None)
        st.session_state.resume = st.session_state.get('resume', None)

    st.write(f"## {selected_chapter}")
    tab1, tab2, tab3 = st.tabs(["Conversation", "Documents", "Analyse Photo"])
    
    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"].replace("[PHASE_PLAN]", ""))
        
        if prompt := st.chat_input("Posez votre question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Tuteur de maths. Style minimaliste. Pas d'emojis. Utilise LaTeX.")
                chat = model.start_chat(history=[{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
                response = chat.send_message(prompt)
                st.markdown(response.text.replace("[PHASE_PLAN]", ""))
                st.session_state.messages.append({"role": "assistant", "content": response.text})

    with tab2:
        if st.session_state.get('study_plan'):
            st.write("### Plan d'étude")
            st.markdown(st.session_state.study_plan)
            if st.session_state.get('resume'):
                st.divider()
                st.write("### Résumé")
                st.markdown(st.session_state.resume)

    with tab3:
        st.write("### **Analyse de votre travail**")
        st.write("Prenez une photo de votre exercice pour obtenir une correction instantanée.")
        uploaded_file = st.file_uploader("Importer une photo", type=["jpg", "jpeg", "png"])
        
        if uploaded_file:
            img = Image.open(uploaded_file)
            st.image(img, caption="Document détecté", use_container_width=True)
            
            if st.button("Analyser et Corriger"):
                with st.spinner("KhirMinTaki examine votre écriture..."):
                    try:
                        vision_model = genai.GenerativeModel("gemini-1.5-flash")
                        vision_prompt = f"Tuteur de maths expert. Analyse cette photo d'exercice sur: {selected_chapter}. Transcris en LaTeX, vérifie les calculs et explique les erreurs avec pédagogie. Style minimaliste, pas d'emojis."
                        response = vision_model.generate_content([vision_prompt, img])
                        
                        st.divider()
                        st.write("### Feedback de l'IA")
                        st.markdown(response.text)
                        
                        if st.button("Ajouter à la conversation"):
                            st.session_state.messages.append({"role": "user", "content": "Peux-tu m'expliquer davantage cette correction ?"})
                            st.session_state.messages.append({"role": "assistant", "content": response.text})
                            st.success("C'est fait !")
                    except Exception as e:
                        st.error("Erreur d'analyse. Assurez-vous que l'image est claire.")
