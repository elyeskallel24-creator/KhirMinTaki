import streamlit as st
import google.generativeai as genai
from groq import Groq
from supabase import create_client
import streamlit.components.v1 as components

# --- 1. SETUP CONNECTIONS ---
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

# --- 5. TOP NAVIGATION ---
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

# --- 6. MAIN INTERFACE ---
if sel_chap == "Sélectionner...":
    st.write(f"## **Asslema, {st.session_state.user_email.split('@')[0].capitalize()} !**")
    st.info("Choisissez un cours en haut pour commencer.")
else:
    t1, t2, t3, t4 = st.tabs(["💬 Chat", "📚 Docs", "📷 Photo", "📝 Quiz"])

    with t1:
        if "messages" not in st.session_state: st.session_state.messages = []
        for m in st.session_state.messages:
            with st.chat_message(m["role"]): st.markdown(m["content"])
        
        if prompt := st.chat_input("Pose ta question ici..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            
            with st.chat_message("assistant"):
                res_text = ""
                # PRIMARY: GROQ (Much higher rate limits for free tier)
                try:
                    chat = groq_client.chat.completions.create(
                        messages=[{"role": "system", "content": "Tu es un tuteur expert. Réponds en Français/Tunisien."},
                                  {"role": "user", "content": prompt}],
                        model="llama-3.3-70b-versatile",
                    )
                    res_text = chat.choices[0].message.content
                except Exception as e:
                    # BACKUP: GEMINI
                    try:
                        model = genai.GenerativeModel("gemini-1.5-flash")
                        res_text = model.generate_content(prompt).text
                    except:
                        st.error("Service temporairement surchargé. Réessayez dans 30 secondes.")

                if res_text:
                    st.markdown(res_text)
                    st.session_state.messages.append({"role": "assistant", "content": res_text})

    with t2: st.info("Générer un résumé via le chat.")
    with t3: st.file_uploader("Upload", type=["jpg","png","jpeg"])
    with t4: st.button("Lancer Quiz")
