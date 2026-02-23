import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
import streamlit.components.v1 as components

# --- 1. SETUP CONNECTIONS ---
try:
    # We use the standard configure but we will target the stable v1 endpoint
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except Exception as e:
    st.error(f"Setup Error: {e}")

# --- 2. STYLE & BRANDING ---
st.set_page_config(page_title="KhirMinTaki", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main-header { font-size: 32px; font-weight: 800; margin-bottom: 20px; border-bottom: 2px solid #f0f0f0; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. TUNISIAN TYPEWRITER ---
def typewriter_effect():
    html_code = """
    <div id="typewriter" style="font-weight:800; font-size:48px; height:60px;"></div>
    <script>
        const words = ["KhirMinTaki", "A9ra khir", "A9ra asra3"];
        let i = 0; let j = 0; let cur = ""; let del = false;
        function type() {
            cur = words[i];
            document.getElementById("typewriter").textContent = del ? cur.substring(0, j--) : cur.substring(0, j++);
            if (!del && j > cur.length) { del = true; setTimeout(type, 2000); }
            else if (del && j === 0) { del = false; i = (i + 1) % words.length; setTimeout(type, 500); }
            else { setTimeout(type, del ? 50: 150); }
        }
        type();
    </script>
    """
    components.html(html_code, height=80)

# --- 4. AUTHENTICATION ---
if "user_email" not in st.session_state:
    typewriter_effect()
    email_input = st.text_input("Entrez votre email", placeholder="exemple@email.com")
    if st.button("Commencer"):
        if email_input:
            st.session_state.user_email = email_input
            try:
                supabase.table("users").upsert({"email": email_input}).execute()
            except: pass
            st.rerun()
    st.stop()

# --- 5. TOP NAVIGATION ---
col_logo, col_nav, col_out = st.columns([2, 4, 1])
with col_logo: st.markdown("<div class='main-header'>KhirMinTaki</div>", unsafe_allow_html=True)

try:
    chapters = supabase.table("chapters").select("*").execute().data
    chapter_names = [c['name'] for c in chapters]
    with col_nav:
        selected_chapter = st.selectbox("📚 Chapitres", ["Sélectionner..."] + chapter_names, label_visibility="collapsed")
except:
    st.error("Erreur de connexion base de données.")
    st.stop()

with col_out:
    if st.button("Sortir"):
        st.session_state.clear()
        st.rerun()

st.divider()

# --- 6. MAIN INTERFACE ---
if selected_chapter == "Sélectionner...":
    st.write(f"## **Asslema, {st.session_state.user_email.split('@')[0].capitalize()} !**")
    st.info("Sélectionne un chapitre en haut pour commencer l'étude.")
else:
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Conversation", "📚 Documents", "📷 Analyse Photo", "📝 Quiz"])

    with tab1:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Posez votre question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                try:
                    # UPDATED FOR 2026 STABILITY
                    # Use the GA (General Availability) model name
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    # We send the request without forcing v1beta
                    response = model.generate_content(prompt)
                    
                    if response.text:
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                except Exception as e:
                    # SECOND ATTEMPT WITH THE NEWEST 2026 NAMING
                    try:
                        model = genai.GenerativeModel("gemini-2.0-flash")
                        response = model.generate_content(prompt)
                        st.markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    except Exception as final_e:
                        st.error(f"Désolé, l'IA est indisponible : {str(final_e)}")

    with tab2: st.info("Résumés bientôt disponibles.")
    with tab3: st.file_uploader("Prendre une photo", type=["jpg","jpeg","png"])
    with tab4: st.button("Démarrer le Quiz")
