import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
import streamlit.components.v1 as components
import json

# --- 1. SETUP ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Configuration Error: {e}")

# --- 2. STYLE & BRANDING ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #ffffff; }
    .stApp { background-color: #ffffff; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
    #MainMenu, footer, header {visibility: hidden;}
    .main-header { font-size: 32px; font-weight: 800; color: #000000; border-bottom: 2px solid #f0f0f0; margin-bottom: 20px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f8f9fa; border-radius: 5px; padding: 10px 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. TUNISIAN TYPEWRITER ---
def typewriter_effect():
    html_code = """
    <div id="typewriter" style="font-weight:800; font-size:48px; height:60px; color:#000000;"></div>
    <script>
        const words = ["KhirMinTaki", "A9ra khir", "A9ra asra3"];
        let i = 0, j = 0, del = false;
        function type() {
            let cur = words[i];
            document.getElementById("typewriter").textContent = del ? cur.substring(0, j--) : cur.substring(0, j++);
            if (!del && j > cur.length) { del = true; setTimeout(type, 2000); }
            else if (del && j === 0) { del = false; i = (i+1)%words.length; setTimeout(type, 500); }
            else { setTimeout(type, del ? 50 : 150); }
        }
        type();
    </script>
    """
    components.html(html_code, height=80)

# --- 4. AUTHENTICATION ---
if "user_email" not in st.session_state:
    typewriter_effect()
    email = st.text_input("Email", placeholder="votre@email.com", label_visibility="collapsed")
    if st.button("Commencer", use_container_width=True):
        if email:
            st.session_state.user_email = email
            try: supabase.table("users").upsert({"email": email}).execute()
            except: pass
            st.rerun()
    st.stop()

# --- 5. NAVIGATION ---
col_logo, col_nav, col_out = st.columns([2, 4, 1])
with col_logo: st.markdown("<div class='main-header'>KhirMinTaki</div>", unsafe_allow_html=True)

try:
    chapters = supabase.table("chapters").select("*").execute().data
    names = [c['name'] for c in chapters]
    with col_nav:
        sel_chap = st.selectbox("Chapitres", ["Sélectionner..."] + names, label_visibility="collapsed")
except:
    st.error("Erreur Base de données")
    st.stop()

with col_out:
    if st.button("Sortir"):
        st.session_state.clear()
        st.rerun()

st.divider()

# --- 6. MAIN LOGIC ---
if sel_chap == "Sélectionner...":
    st.write(f"## **Asslema, {st.session_state.user_email.split('@')[0].capitalize()} !**")
    st.info("Choisissez un chapitre pour commencer ton évaluation personnalisée.")
else:
    chapter_id = next(c['id'] for c in chapters if c['name'] == sel_chap)
    
    # Load session data for this chapter
    session_data = supabase.table("student_sessions").select("*").eq("user_email", st.session_state.user_email).eq("chapter_id", chapter_id).execute()
    
    if not session_data.data:
        # Create initial session if none exists
        supabase.table("student_sessions").insert({
            "user_email": st.session_state.user_email,
            "chapter_id": chapter_id,
            "phase": "assessment"
        }).execute()
        st.rerun()
    
    curr_session = session_data.data[0]
    phase = curr_session.get('phase', 'assessment')

    # TABS STRUCTURE
    t1, t2, t3, t4, t5 = st.tabs(["💬 Tutorat", "📅 Study Plan", "📝 Resume", "✍️ Notes", "🎯 Exercises"])

    with t1:
        if "messages" not in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": f"Asslema! On commence le chapitre {sel_chap}. Pour t'aider au mieux, dis-moi : quel est ton niveau actuel et qu'est-ce que tu trouves difficile ici ?"}]
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Réponds au tuteur..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                # System instructions based on current phase
                sys_prompt = f"""Tu es un tuteur expert du programme tunisien (Mathématiques). 
                Phase actuelle : {phase}.
                Si la phase est assessment, pose des questions pour évaluer le niveau. 
                Dès que tu as assez d'infos, génère un plan d'étude et termine ton message par [GENERATE_PLAN].
                Si la phase est learning, explique le cours et termine par [UPDATE_RESUME] après chaque section.
                Utilise LaTeX pour les maths."""
                
                try:
                    chat = groq_client.chat.completions.create(
                        messages=[{"role": "system", "content": sys_prompt}] + st.session_state.messages[-5:],
                        model="llama-3.3-70b-versatile",
                    )
                    res_text = chat.choices[0].message.content
                except:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    res_text = model.generate_content(prompt).text

                st.markdown(res_text.replace("[GENERATE_PLAN]", "").replace("[UPDATE_RESUME]", ""))
                st.session_state.messages.append({"role": "assistant", "content": res_text})

                # AUTOMATION TRIGGERS
                if "[GENERATE_PLAN]" in res_text:
                    new_plan = "Plan d'étude personnalisé généré basé sur ton profil..." # In reality, call AI to format a plan
                    supabase.table("student_sessions").update({"study_plan": res_text, "phase": "learning"}).eq("id", curr_session['id']).execute()
                    st.success("Plan d'étude créé dans l'onglet dédié !")
                
                if "[UPDATE_RESUME]" in res_text:
                    # Update summary column in DB
                    supabase.table("student_sessions").update({"course_resume": res_text}).eq("id", curr_session['id']).execute()

    with t2:
        if curr_session.get('study_plan'): st.markdown(curr_session['study_plan'])
        else: st.warning("Le plan sera généré après l'évaluation initiale dans le Chat.")

    with t3:
        if curr_session.get('course_resume'): st.markdown(curr_session['course_resume'])
        else: st.warning("Le résumé se construira au fur et à mesure de tes leçons.")

    with t4:
        st.info("Ici s'affichent tes remarques personnalisées et points d'attention.")

    with t5:
        st.write("Section Exercices & Maîtrise")
