import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
from fpdf import FPDF
import streamlit.components.v1 as components
from PIL import Image
import json

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
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; color: #000000; }
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #f0f0f0; }
    [data-testid="stSidebar"] * { color: #000000 !important; font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .typewriter-container { font-family: 'Inter', sans-serif; font-weight: 600; font-size: 24px; color: #000000; height: 40px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ROTATING TYPEWRITER COMPONENT ---
def typewriter_effect():
    html_code = """
    <div class="typewriter-container" id="typewriter"></div>
    <script>
        const textElement = document.getElementById("typewriter");
        const words = ["KhirMinTaki", "A9ra khir", "A9ra asra3"];
        let wordIndex = 0; let charIndex = 0; let isDeleting = false; let typeSpeed = 150;
        function type() {
            const currentWord = words[wordIndex];
            if (isDeleting) { textElement.textContent = currentWord.substring(0, charIndex - 1); charIndex--; typeSpeed = 100; }
            else { textElement.textContent = currentWord.substring(0, charIndex + 1); charIndex++; typeSpeed = 150; }
            if (!isDeleting && charIndex === currentWord.length) { isDeleting = true; typeSpeed = 2000; }
            else if (isDeleting && charIndex === 0) { isDeleting = false; wordIndex = (wordIndex + 1) % words.length; typeSpeed = 500; }
            setTimeout(type, typeSpeed);
        }
        type();
    </script>
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
            except: st.error("Erreur de connexion.")
        else: st.error("Veuillez entrer un email valide.")
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

# --- 6. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    user_display_name = st.session_state.user_email.split('@')[0].capitalize()
    st.write(f"### **Bienvenue, {user_display_name}**") 
    st.write("Sélectionnez un module pour commencer.")
else:
    chapter_id = chapters_data.data[chapter_names.index(selected_chapter)]['id']
    tab1, tab2, tab3, tab4 = st.tabs(["Conversation", "Documents", "Analyse Photo", "Quiz Express"])

    # (Previous Tabs logic omitted for brevity but should stay in your file)
    # [LOGIC FOR TAB 1, 2, 3 REMAINS THE SAME]
    
    with tab4:
        st.write("### **Quiz d'auto-évaluation**")
        st.write("Teste tes connaissances avec 3 questions rapides.")
        
        if st.button("Générer un nouveau Quiz"):
            with st.spinner("Génération des questions..."):
                quiz_prompt = f"""
                Génère 3 questions à choix multiples sur le chapitre : {selected_chapter}.
                Format de réponse attendu : JSON uniquement avec cette structure :
                [
                  {{"question": "texte", "options": ["A", "B", "C"], "answer": "B", "explication": "explication LaTeX"}}
                ]
                Style : Minimaliste, pas d'emojis.
                """
                raw_response = genai.GenerativeModel("gemini-1.5-flash").generate_content(quiz_prompt).text
                # Clean the response to ensure it's valid JSON
                clean_json = raw_response.replace('```json', '').replace('```', '').strip()
                st.session_state.current_quiz = json.loads(clean_json)
                st.session_state.quiz_submitted = False
        
        if "current_quiz" in st.session_state:
            score = 0
            user_answers = []
            for i, q in enumerate(st.session_state.current_quiz):
                st.write(f"**Q{i+1}: {q['question']}**")
                choice = st.radio(f"Sélectionnez une réponse pour Q{i+1}", q['options'], key=f"q{i}")
                user_answers.append(choice)
            
            if st.button("Valider mes réponses"):
                st.session_state.quiz_submitted = True
                
            if st.session_state.get('quiz_submitted'):
                for i, q in enumerate(st.session_state.current_quiz):
                    if user_answers[i] == q['answer']:
                        st.success(f"Q{i+1}: Correct !")
                        score += 1
                    else:
                        st.error(f"Q{i+1}: Incorrect. La réponse était {q['answer']}")
                        st.info(f"Explication : {q['explication']}")
                
                final_score = int((score / 3) * 100)
                st.write(f"### Ton score : {final_score}%")
                
                # SAVE TO SUPABASE
                supabase.table("quiz_scores").insert({
                    "user_email": st.session_state.user_email,
                    "chapter_id": chapter_id,
                    "score": final_score
                }).execute()
