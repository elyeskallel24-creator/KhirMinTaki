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

# --- 2. CUSTOM CSS (BRANDING) ---
st.set_page_config(page_title="KhirMinTaki", layout="wide", page_icon="📚")

st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #f8f9fa;
    }
    /* Professional Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1e3a8a;
        color: white;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    /* Buttons styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #1e3a8a;
        color: white;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #2563eb;
        color: white;
    }
    /* Chat message styling */
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
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
    clean_content = content.replace("$$", "").replace("**", "")
    pdf.multi_cell(0, 10, clean_content)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. AI FUNCTIONS ---
def generate_study_plan(history, chapter):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Analyse ce diagnostic pour {chapter}. Crée un plan de 4 étapes avec des cases à cocher. Français Académique."
    return model.generate_content([prompt, str(history)]).text

def generate_resume(chapter):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Rédige un résumé structuré pour {chapter}. Utilise LaTeX. Français Académique."
    return model.generate_content(prompt).text

# --- 5. NAVIGATION ---
st.sidebar.title("📚 KhirMinTaki")
st.sidebar.write("L'école du futur, aujourd'hui.")

if st.sidebar.button("🔄 Réinitialiser la session"):
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

chapters_data = supabase.table("chapters").select("*").execute()
chapter_names = [c['name'] for c in chapters_data.data]
selected_chapter = st.sidebar.selectbox("Choisir un Chapitre", ["Sélectionner..."] + chapter_names)

# --- 6. STATE & LOADING ---
if "messages" not in st.session_state: st.session_state.messages = []

if selected_chapter != "Sélectionner...":
    chapter_id = chapters_data.data[chapter_names.index(selected_chapter)]['id']
    existing = supabase.table("studying_plans").select("*").eq("chapter_id", chapter_id).execute()
    
    if existing.data:
        st.session_state.study_plan = existing.data[0].get('content')
        st.session_state.resume = existing.data[0].get('resume')
    else:
        if "study_plan" not in st.session_state: st.session_state.study_plan = None
        if "resume" not in st.session_state: st.session_state.resume = None

# --- 7. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    st.title("Bienvenue sur KhirMinTaki")
    st.subheader("Votre plateforme d'apprentissage intelligente")
    st.write("""
        Pour commencer votre session de révision :
        1. Choisissez un chapitre dans la barre latérale.
        2. Répondez aux questions de diagnostic du professeur.
        3. Obtenez votre plan et résumé personnalisés.
    """)
    st.info("Utilisez le menu à gauche pour sélectionner une leçon de mathématiques.")
else:
    st.title(f"📖 {selected_chapter}")
    
    tab1, tab2 = st.tabs(["💬 Diagnostic & Chat", "📝 Ressources"])
    
    with tab1:
        if st.session_state.get('study_plan'):
            st.success("Plan d'étude disponible dans l'onglet Ressources.")
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"].replace("[PHASE_PLAN]", ""))

    with tab2:
        if st.session_state.get('study_plan'):
            st.subheader("✅ Votre Plan Personnalisé")
            st.markdown(st.session_state.study_plan)
            st.divider()
            
            if st.session_state.get('resume'):
                st.subheader("📝 Résumé du Cours")
                st.markdown(st.session_state.resume)
                pdf = create_pdf(f"Resume: {selected_chapter}", st.session_state.resume)
                st.download_button("📥 Télécharger PDF", data=pdf, file_name="resume.pdf")
            else:
                if st.button("Générer le Résumé"):
                    content = generate_resume(selected_chapter)
                    supabase.table("studying_plans").update({"resume": content}).eq("chapter_id", chapter_id).execute()
                    st.session_state.resume = content
                    st.rerun()
        else:
            st.warning("Complétez le diagnostic dans l'onglet Chat pour débloquer les ressources.")

    # Chat logic
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
                plan = generate_study_plan(st.session_state.messages, selected_chapter)
                supabase.table("studying_plans").insert({"chapter_id": chapter_id, "content": plan}).execute()
                st.session_state.study_plan = plan
                st.rerun()
