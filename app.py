in that code i just gave you can you teach me how to Replace your show_signup() function with this one without corrupting or changing anything else: 
def show_signup():
    st.markdown("## Créer un compte")
    email = st.text_input("Email", key="signup_email")
    email_valid = is_valid_email(email) if email else None
    email_exists = email in st.session_state.mock_db
    
    if email:
        if email_exists:
            st.markdown("<p class='validation-msg error-text'>Cet email est déjà utilisé</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Email']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)
        elif email_valid:
            st.markdown("<p class='validation-msg success-text'>Email valide</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Email']) div[data-baseweb='input'] { border: 2px solid #28a745 !important; }</style>", unsafe_allow_html=True)

    pwd = st.text_input("Mot de passe", type="password", key="signup_pwd")
    
    # --- PASSWORD VALIDATION LOGIC ---
    pwd_valid = len(pwd) >= 8 if pwd else None
    if pwd:
        if not pwd_valid:
            st.markdown("<p class='validation-msg error-text'>Le mot de passe doit contenir au moins 8 caractères</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Mot de passe']) div[data-baseweb='input'] { border: 2px solid #dc3545 !important; }</style>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='validation-msg success-text'>Longueur valide</p>", unsafe_allow_html=True)
            st.markdown("<style>div[data-testid='stTextInput']:has(input[aria-label='Mot de passe']) div[data-baseweb='input'] { border: 2px solid #28a745 !important; }</style>", unsafe_allow_html=True)
    # ---------------------------------

    pwd_conf = st.text_input("Confirmez votre mot de passe", type="password", key="signup_pwd_conf")
    match_valid = (pwd == pwd_conf) if pwd_conf else None
    
    if pwd_conf:
        if match_valid:
            st.markdown("<p class='validation-msg success-text'>Les mots de passe correspondent</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='validation-msg error-text'>Les mots de passe ne correspondent pas</p>", unsafe_allow_html=True)

    if st.button("Créer mon compte", use_container_width=True):
        if email_valid and not email_exists and pwd_valid and match_valid:
            st.session_state.mock_db[email] = {"pwd": pwd, "profile_complete": False, "data": {}}
            st.session_state.step = "login"
            st.rerun()
    
    if st.button("Retour", key="back_signup"):
        st.session_state.step = "landing"
        st.rerun()
