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
    st.error("Connection Error: Check your Streamlit Secrets.")

# --- 2. STYLE & BRANDING ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; color: #000000; }
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #f0f0f0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. TUNISIAN TYPEWRITER (BIG & BOLD) ---
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
        .typewriter-container { 
            font-family: 'Inter', sans-serif; 
            font-weight: 800; 
            font-size: 48px; 
            color: #000000; 
            height: 60px;
            display: flex;
            align-items: center;
        }
    </style>
    """
    components.html(html_code, height=80)

# --- 4. AUTHENTICATION ---
if "user_email" not in st.session_state:
    typewriter_effect()
    st.write("Bienvenue. Entrez votre email pour commencer.")
    email_input = st.text_input("Email", placeholder="exemple@email.com")
    if st.button("Commencer"):
        if email_input:
            supabase.table("users").upsert({"email": email_input}).execute()
            st.session_state.user_email = email_input
            st.rerun()
    st.stop()

# --- 5. SIDEBAR & NAVIGATION ---
st.sidebar.markdown(f"### **KhirMinTaki**")
st.sidebar.caption(f"Connecté: {st.session_state.user_email}")
if st.sidebar.button("Déconnexion"):
    del st.session_state.user_email
    st.rerun()

chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Chapitres", ["Sélectionner..."] + chapter_names)

# --- 6. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    name = st.session_state.user_email.split('@')[0].capitalize()
    st.write(f"### **Bienvenue, {name}**")
    st.write("Prêt pour une session d'apprentissage ? Choisissez un module à gauche.")
    
    stats = supabase.table("student_sessions").select("id").eq("user_email", st.session_state.user_email).execute()
    st.metric("Chapitres explorés", len(stats.data))

else:
    chapter_id = chapters_data.data[chapter_names.index(selected_chapter)]['id']
    
    # PROGRESS TRACKER
    score_res = supabase.table("quiz_scores").select("score").eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).order("created_at", desc=True).limit(1).execute()
    if score_res.data:
        latest_score = score_res.data[0]['score']
        st.write(f"**Maîtrise du chapitre : {latest_score}%**")
        st.progress(latest_score / 100)
    else:
        st.write("**Maîtrise du chapitre : 0%**")
        st.progress(0.0)

    # Load Course Data
    res = supabase.table("student_sessions").select("*").eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).execute()
    if res.data:
        st.session_state.study_plan = res.data[0].get('study_plan')
        st.session_state.resume = res.data[0].get('course_resume')
    else:
        st.session_state.study_plan = None
        st.session_state.resume = None

    tab1, tab2, tab3, tab4 = st.tabs(["💬 Conversation", "📚 Documents", "📷 Analyse Photo", "📝 Quiz Express"])

    # TAB 1: CHAT
    with tab1:
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"].replace("[PHASE_PLAN]", ""))
        
        if prompt := st.chat_input("Posez votre question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Tuteur expert. Style minimaliste. Pas d'emojis. Utilise LaTeX.")
                response = model.generate_content(prompt)
                st.markdown(response.text.replace("[PHASE_PLAN]", ""))
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                if "[PHASE_PLAN]" in response.text and not st.session_state.study_plan:
                    plan_res = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Plan d'étude pour {selected_chapter}").text
                    supabase.table("student_sessions").insert({"chapter_id": chapter_id, "user_email": st.session_state.user_email, "study_plan": plan_res}).execute()
                    st.session_state.study_plan = plan_res
                    st.rerun()

    # TAB 2: DOCUMENTS + PDF EXPORT
    with tab2:
        if st.session_state.study_plan:
            st.subheader("Plan d'étude")
            st.markdown(st.session_state.study_plan)
            if st.session_state.resume:
                st.divider()
                st.subheader("Résumé")
                st.markdown(st.session_state.resume)
            else:
                if st.button("Générer un résumé"):
                    with st.spinner("Rédaction..."):
                        resume_text = genai.GenerativeModel("gemini-1.5-flash").generate_content(f"Résumé LaTeX pour {selected_chapter}").text
                        supabase.table("student_sessions").update({"course_resume": resume_text}).eq("chapter_id", chapter_id).eq("user_email", st.session_state.user_email).execute()
                        st.session_state.resume = resume_text
                        st.rerun()

            if st.button("Télécharger le cours en PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"KhirMinTaki - {selected_chapter}", ln=True, align='C')
                pdf.ln(10)
                if st.session_state.study_plan:
                    pdf.multi_cell(0, 10, txt="--- PLAN D'ETUDE ---")
                    pdf.multi_cell(0, 10, txt=st.session_state.study_plan.encode('latin-1', 'replace').decode('latin-1'))
                if st.session_state.resume:
                    pdf.ln(10)
                    pdf.multi_cell(0, 10, txt="--- RESUME DU COURS ---")
                    pdf.multi_cell(0, 10, txt=st.session_state.resume.encode('latin-1', 'replace').decode('latin-1'))
                pdf_output = pdf.output(dest='S').encode('latin-1')
                st.download_button(label="Cliquer ici pour télécharger", data=pdf_output, file_name=f"{selected_chapter}.pdf", mime="application/pdf")
        else:
            st.info("Lancez la conversation pour débloquer les documents.")

    # TAB 3: PHOTO ANALYSIS
    with tab3:
        img_file = st.file_uploader("Upload", type=["jpg", "png", "jpeg"])
        if img_file:
            img = Image.open(img_file)
            st.image(img, width=400)
            if st.button("Analyser mon travail"):
                with st.spinner("Analyse..."):
                    res = genai.GenerativeModel("gemini-1.5-flash").generate_content([f"Corrige ce travail sur {selected_chapter}. LaTeX.", img])
                    st.markdown(res.text)

    # TAB 4: QUIZ EXPRESS
    with tab4:
        if st.button("Générer un Quiz"):
            with st.spinner("Chargement..."):
                q_prompt = f"Génère 3 questions MCQ sur {selected_chapter}. Format JSON: [{{'question':'','options':['','',''],'answer':'','explication':''}}]"
                raw = genai.GenerativeModel("gemini-1.5-flash").generate_content(q_prompt).text
                st.session_state.current_quiz = json.loads(raw.replace('```json','').replace('```',''))
                st.session_state.quiz_done = False

        if "current_quiz" in st.session_state:
            score = 0
            u_answers = []
            for i, q in enumerate(st.session_state.current_quiz):
                u_answers.append(st.radio(q['question'], q['options'], key=f"qz_{i}"))
            
            if st.button("Valider"):
                st.session_state.quiz_done = True
                for i, q in enumerate(st.session_state.current_quiz):
                    if u_answers[i] == q['answer']:
                        st.success(f"Q{i+1} Correct!"); score += 1
                    else: st.error(f"Q{i+1} Faux. C'était {q['answer']}. {q['explication']}")
                
                final = int((score/3)*100)
                st.write(f"### Score: {final}%")
                supabase.table("quiz_scores").insert({"user_email": st.session_state.user_email, "chapter_id": chapter_id, "score": final}).execute()
