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

# --- 2. SUPER MINIMALIST CSS ---
st.set_page_config(page_title="KhirMinTaki", layout="wide", page_icon="⚪")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #1a1a1a; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #ececec; }
    [data-testid="stSidebar"] * { color: #1a1a1a !important; }
    .stButton>button {
        border-radius: 2px;
        background-color: #ffffff;
        color: #1a1a1a;
        border: 1px solid #1a1a1a;
        transition: 0.2s;
    }
    .stButton>button:hover { background-color: #1a1a1a; color: #ffffff; }
    .stats-container { padding: 10px 0; border-bottom: 1px solid #1a1a1a; margin-bottom: 20px; }
    .stChatMessage { background-color: transparent !important; border-bottom: 1px solid #f0f0f0; border-radius: 0px; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
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
    clean_content = content.replace("$$", "").replace("**", "").replace("$", "")
    pdf.multi_cell(0, 10, clean_content.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# --- 4. NAVIGATION & STATS ---
st.sidebar.title("KHIRMINTAKI")
st.sidebar.caption("Pure Learning.")

chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("CHAPITRE", ["Sélectionner..."] + chapter_names)

num_mastered = 0
try:
    all_sessions = supabase.table("student_sessions").select("id").execute()
    num_mastered = len(all_sessions.data)
except:
    num_mastered = 0

# --- 5. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    st.title("TABLEAU DE BORD")
    col1, col2, col3 = st.columns(3)
    with col1: st.markdown(f"<div class='stats-container'><h4>Points</h4><h2>{num_mastered * 100}</h2></div>", unsafe_allow_html=True)
    with col2: st.markdown(f"<div class='stats-container'><h4>Chapitres</h4><h2>{num_mastered}</h2></div>", unsafe_allow_html=True)
    with col3: st.markdown(f"<div class='stats-container'><h4>Statut</h4><h2>Actif</h2></div>", unsafe_allow_html=True)
    st.write("Sélectionnez un chapitre pour commencer.")

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

    st.title(selected_chapter.upper())
    tab1, tab2 = st.tabs(["DIAGNOSTIC", "RESSOURCES"])
    
    with tab1:
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"].replace("[PHASE_PLAN]", ""))
        
        if prompt := st.chat_input("..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                # System instruction updated for minimal style
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction="Professeur de mathématiques. Français Académique. Style direct et minimaliste. [PHASE_PLAN] après 3 questions.")
                chat = model.start_chat(history=[{"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]} for m in st.session_state.messages[:-1]])
                response = chat.send_message(prompt)
                st.markdown(response.text.replace("[PHASE_PLAN]", ""))
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                if "[PHASE_PLAN]" in response.text and not st.session_state.get('study_plan'):
                    # Personalized AI logic remains
                    plan_prompt = f"Analyse cette conversation : {str(st.session_state.messages)}. Crée un plan de 4 étapes personnalisé pour {selected_chapter}."
                    plan = genai.GenerativeModel("gemini-1.5-flash").generate_content(plan_prompt).text
                    supabase.table("student_sessions").insert({"chapter_id": chapter_id, "study_plan": plan}).execute()
                    st.session_state.study_plan = plan
                    st.rerun() # No balloons for minimalist look

    with tab2:
        if st.session_state.get('study_plan'):
            st.markdown("### PLAN D'ÉTUDE")
            st.markdown(st.session_state.study_plan)
            
            if st.session_state.get('resume'):
                st.divider()
                st.markdown("### RÉSUMÉ DU COURS")
                st.markdown(st.session_state.resume)
                pdf = create_pdf(f"Resume: {selected_chapter}", st.session_state.resume)
                st.download_button("TÉLÉCHARGER PDF", data=pdf, file_name="resume.pdf")
            else:
                if st.button("GÉNÉRER LE RÉSUMÉ"):
                    res_prompt = f"""
                    Basé sur cette discussion : {str(st.session_state.messages)}, 
                    rédige un résumé LaTeX pour {selected_chapter}. 
                    Insiste sur les points faibles identifiés. Français Académique.
                    """
                    content = genai.GenerativeModel("gemini-1.5-flash").generate_content(res_prompt).text
                    supabase.table("student_sessions").update({"course_resume": content}).eq("chapter_id", chapter_id).execute()
                    st.session_state.resume = content
                    st.rerun()
        else:
            st.warning("Terminez le diagnostic pour débloquer votre plan.")
