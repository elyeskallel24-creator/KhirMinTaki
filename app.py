import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
from fpdf import FPDF

# --- 1. SETUP CONNECTIONS ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error("Connection Error: Check if your Secrets are set up correctly!")

# --- 2. CUSTOM CSS ---
st.set_page_config(page_title="KhirMinTaki", layout="wide", page_icon="🎓")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    [data-testid="stSidebar"] { background-color: #1e3a8a; }
    [data-testid="stSidebar"] * { color: white !important; }
    .badge-card {
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        border-left: 5px solid #1e3a8a;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. UTILITY FUNCTIONS ---
def create_pdf(title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(40, 10, title)
    pdf.ln(20)
    pdf.set_font("Arial", size=12)
    # Cleaning text for PDF compatibility
    clean_content = content.replace("$$", "").replace("**", "").replace("$", "")
    pdf.multi_cell(0, 10, clean_content.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- 4. NAVIGATION & GLOBAL STATS ---
st.sidebar.title("📚 KhirMinTaki")

# Fetch chapters
chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Choisir un Chapitre", ["Sélectionner..."] + chapter_names)

# Stats for Dashboard
num_mastered = 0
try:
    all_sessions = supabase.table("student_sessions").select("id").execute()
    num_mastered = len(all_sessions.data)
except:
    num_mastered = 0

level = "Apprenti"
if num_mastered > 2: level = "Expert"
if num_mastered > 5: level = "Maître des Maths"

# --- 5. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    st.title("Tableau de Bord")
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f"<div class='badge-card'><h3>Niveau</h3><h2>{level}</h2></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='badge-card'><h3>Chapitres</h3><h2>{num_mastered}</h2></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='badge-card'><h3>Points</h3><h2>{num_mastered * 100}</h2></div>", unsafe_allow_html=True)
    st.divider()
    st.info("Sélectionnez un chapitre dans la barre latérale pour commencer votre diagnostic !")

else:
    chapter_id = chapters_data.data[chapter_names.index(selected_chapter)]['id']
    existing = supabase.table("student_sessions").select("*").eq("chapter_id", chapter_id).execute()
    
    if "messages" not in st.session_state: st.session_state.messages = []
    
    if existing.data:
        st.session_state.study_plan = existing.data[0].get('study_plan')
        st.session_state.resume = existing.data[0].get('course_resume')
    else:
        if "study_plan" not in st.session_state: st.session_state.study_plan = None
        if "resume" not in st.session_state: st.session_state.resume = None

    st.title(f"📖 {selected_chapter}")
    tab1, tab2 = st.tabs(["💬 Diagnostic & Chat", "📝 Ressources"])
    
    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"].replace("[PHASE_PLAN]", ""))
        
        if prompt := st.chat_input("Répondez ici..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Prof de maths tunisien. Français Académique. Socratique. Termine par [PHASE_PLAN] après 3 questions.")
                chat = model.start_chat(history=[{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
                response = chat.send_message(prompt)
                st.markdown(response.text.replace("[PHASE_PLAN]", ""))
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                if "[PHASE_PLAN]" in response.text and not st.session_state.get('study_plan'):
                    # PERSONALIZED PLAN LOGIC
                    plan_prompt = f"Analyse cette conversation : {str(st.session_state.messages)}. Crée un plan de 4 étapes personnalisé pour {selected_chapter}. Français Académique."
                    plan = genai.GenerativeModel("gemini-1.5-flash").generate_content(plan_prompt).text
                    supabase.table("student_sessions").insert({"chapter_id": chapter_id, "study_plan": plan}).execute()
                    st.session_state.study_plan = plan
                    st.balloons()
                    st.rerun()

    with tab2:
        if st.session_state.get('study_plan'):
            st.markdown("### ✅ Votre Plan d'Étude Personnalisé")
            st.markdown(st.session_state.study_plan)
            
            if st.session_state.get('resume'):
                st.divider()
                st.markdown("### 📝 Résumé du Cours")
                st.markdown(st.session_state.resume)
                pdf = create_pdf(f"Resume: {selected_chapter}", st.session_state.resume)
                st.download_button("📥 Télécharger PDF", data=pdf, file_name="resume.pdf")
            else:
                if st.button("Générer le Résumé"):
                    # PERSONALIZED RESUME LOGIC
                    res_prompt = f"Basé sur cette discussion : {str(st.session_state.messages)}, rédige un résumé LaTeX pour {selected_chapter}. Ins
