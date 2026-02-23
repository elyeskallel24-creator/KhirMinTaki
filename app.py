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
    st.error(f"Setup Error: {e}")

# --- 2. STYLE & BRANDING (ULTIMATE SIDEBAR FIX) ---
st.set_page_config(page_title="KhirMinTaki", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; color: #000000; }
    .stApp { background-color: #ffffff; }
    
    /* THE SIDEBAR BUTTON FIX */
    [data-testid="collapsedControl"] {
        background-color: #f0f2f6 !important;
        border-radius: 0 10px 10px 0 !important;
        left: 0px !important;
        top: 20px !important;
        width: 50px !important;
        height: 50px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 4px 4px 10px rgba(0,0,0,0.2) !important;
        z-index: 1000000 !important;
    }
    [data-testid="collapsedControl"] svg {
        width: 35px !important;
        height: 35px !important;
        fill: #000000 !important;
    }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. TUNISIAN TYPEWRITER ---
def typewriter_effect():
    html_code = """
    <div class="typewriter-container" id="typewriter"></div>
    <script>
        const textElement = document.getElementById("typewriter");
        const words = ["KhirMinTaki", "A9ra khir", "A9ra asra3"];
        let wordIndex = 0; let charIndex = 0; let isDeleting = false;
        function type() {
            const currentWord = words[wordIndex];
            if (isDeleting) { textElement.textContent = currentWord.substring(0, charIndex - 1); charIndex--; }
            else { textElement.textContent = currentWord.substring(0, charIndex + 1); charIndex++; }
            let typeSpeed = isDeleting ? 100 : 150;
            if (!isDeleting && charIndex === currentWord.length) { isDeleting = true; typeSpeed = 2000; }
            else if (isDeleting && charIndex === 0) { isDeleting = false; wordIndex = (wordIndex + 1) % words.length; typeSpeed = 500; }
            setTimeout(type, typeSpeed);
        }
        type();
    </script>
    <style>
        .typewriter-container { font-family: 'Inter', sans-serif; font-weight: 800; font-size: 48px; color: #000000; height: 60px; display: flex; align-items: center; }
    </style>
    """
    components.html(html_code, height=80)

# --- 4. AUTHENTICATION ---
if "user_email" not in st.session_state:
    typewriter_effect()
    st.markdown("<p style='font-family: Inter; font-size: 28px; font-weight: 700;'>Bienvenue. Entrez votre email.</p>", unsafe_allow_html=True)
    email_input = st.text_input("Email", placeholder="exemple@email.com", label_visibility="collapsed")
    if st.button("Commencer", use_container_width=True):
        if email_input:
            try:
                supabase.table("users").upsert({"email": email_input}).execute()
                st.session_state.user_email = email_input
                st.rerun()
            except Exception as e:
                st.error(f"Database Error: {e}")
    st.stop()

# --- 5. SIDEBAR & NAVIGATION ---
st.sidebar.markdown(f"### **KhirMinTaki**")
if st.sidebar.button("Déconnexion"):
    del st.session_state.user_email
    st.rerun()

try:
    chapters_data = supabase.table("chapters").select("*").execute()
    chapter_names = [c['name'] for c in chapters_data.data]
    selected_chapter = st.sidebar.selectbox("Chapitres", ["Sélectionner..."] + chapter_names)
except Exception as e:
    st.error(f"Error loading chapters: {e}")
    st.stop()

# --- 6. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    name = st.session_state.user_email.split('@')[0].capitalize()
    st.write(f"## **Asslema, {name} !**")
    st.info("👈 **Utilise le menu à gauche pour choisir un chapitre.**")
    st.warning("Si le menu est caché, clique sur le carré gris avec la flèche ( > ) tout en haut à gauche.")
    try:
        stats = supabase.table("student_sessions").select("id").eq("user_email", st.session_state.user_email).execute()
        st.metric("Chapitres explorés", len(stats.data))
    except:
        st.metric("Chapitres explorés", 0)

else:
    chapter_id = next(c['id'] for c in chapters_data.data if c['name'] == selected_chapter)
    
    # Mastery Progress
    score_res = supabase.table("quiz_scores").select("score").eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).order("created_at", desc=True).limit(1).execute()
    latest_score = score_res.data[0]['score'] if score_res.data else 0
    st.write(f"**Maîtrise du chapitre : {latest_score}%**")
    st.progress(latest_score / 100)

    # Load Study Data
    session_res = supabase.table("student_sessions").select("*").eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).execute()
    study_plan = session_res.data[0].get('study_plan') if session_res.data else None
    course_resume = session_res.data[0].get('course_resume') if session_res.data else None

    tab1, tab2, tab3, tab4 = st.tabs(["💬 Conversation", "📚 Documents", "📷 Analyse Photo", "📝 Quiz Express"])

    with tab1:
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"].replace("[PHASE_PLAN]", ""))
        
        if prompt := st.chat_input("Posez votre question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Tuteur expert. LaTeX.")
                response = model.generate_content(prompt)
                st.markdown(response.text.replace("[PHASE_PLAN]", ""))
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                if "[PHASE_PLAN]" in response.text and not study_plan:
                    plan = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Plan d'étude pour {selected_chapter}").text
                    supabase.table("student_sessions").upsert({"chapter_id": chapter_id, "user_email": st.session_state.user_email, "study_plan": plan}).execute()
                    st.rerun()

    with tab2:
        if study_plan:
            st.subheader("Plan d'étude")
            st.markdown(study_plan)
            if course_resume:
                st.divider()
                st.subheader("Résumé")
                st.markdown(course_resume)
            elif st.button("Générer un résumé"):
                with st.spinner("Rédaction..."):
                    resume = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Résumé LaTeX pour {selected_chapter}").text
                    supabase.table("student_sessions").update({"course_resume": resume}).eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).execute()
                    st.rerun()
            
            # PDF Generation
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"KhirMinTaki - {selected_chapter}", ln=True, align='C')
            clean_text = study_plan.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, txt=clean_text)
            st.download_button(label="Télécharger PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"{selected_chapter}.pdf")
        else:
            st.info("Lancez la conversation pour débloquer les documents.")

    with tab3:
        img_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"])
        if img_file:
            st.image(Image.open(img_file), width=400)
            if st.button("Analyser"):
                res = genai.GenerativeModel("gemini-1.5-flash").generate_content([f"Corrige ce travail. LaTeX.", Image.open(img_file)])
                st.markdown(res.text)

    with tab4:
        if st.button("Générer un Quiz"):
            with st.spinner("Chargement..."):
                q_prompt = f"Génère 3 questions MCQ sur {selected_chapter}. Format JSON: [{{'question':'','options':['','',''],'answer':'','explication':''}}]"
                raw = genai.GenerativeModel("gemini-1.5-flash").generate_content(q_prompt).text
                st.session_state.current_quiz = json.loads(raw.replace('```json','').replace('```',''))
        
        if "current_quiz" in st.session_state:
            score = 0
            for i, q in enumerate(st.session_state.current_quiz):
                ans = st.radio(q['question'], q['options'], key=f"qz_{i}")
                if st.button("Valider", key=f"v_{i}"):
                    if ans == q['answer']: 
                        st.success("Correct")
                        supabase.table("quiz_scores").insert({"user_email": st.session_state.user_email, "chapter_id": chapter_id, "score": 100}).execute()
