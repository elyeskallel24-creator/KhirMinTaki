def show_chat_diagnose():
    # 1. SETUP SESSION VARIABLES FOR TRACKING
    if "diag_step" not in st.session_state:
        st.session_state.diag_step = "get_chapter"
    if "q_count" not in st.session_state:
        st.session_state.q_count = 0
    
    st.markdown(f"### 👨‍🏫 Tuteur de {st.session_state.selected_subject}")
    
    # Header showing progress
    if st.session_state.diag_step == "questioning":
        progress = st.session_state.q_count / 10
        st.progress(progress, text=f"Diagnostic: Question {st.session_state.q_count}/10")

    # 2. INITIAL INTRO
    if not st.session_state.get("messages"):
        intro = f"Asslema! Je suis ton tuteur en {st.session_state.selected_subject}. Quel chapitre souhaites-tu maîtriser aujourd'hui ?"
        st.session_state.messages = [{"role": "assistant", "content": intro}]

    # 3. DISPLAY CHAT
    for m in st.session_state.messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # 4. CHAT INPUT & AI LOGIC
    if prompt := st.chat_input("Réponds ici..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Determine the AI's next move
        with st.chat_message("assistant"):
            # System Prompt with User DNA
            dna_context = (
                f"Tu es un tuteur expert en {st.session_state.selected_subject} pour le Bac {st.session_state.user_data['bac_type']}. "
                f"L'élève a un niveau {st.session_state.user_data['levels'].get(st.session_state.selected_subject)} "
                f"et veut un style {st.session_state.user_data['style']}. "
            )

            if st.session_state.diag_step == "get_chapter":
                st.session_state.current_chapter = prompt
                response = f"Parfait, le chapitre **{prompt}**. Commençons le diagnostic de 10 questions pour créer ton plan personnalisé. \n\n **Question 1:** ..."
                st.session_state.diag_step = "questioning"
                st.session_state.q_count = 1
            
            elif st.session_state.diag_step == "questioning":
                if st.session_state.q_count < 10:
                    st.session_state.q_count += 1
                    # Logic to call Groq/Gemini for the next question
                    try:
                        chat_completion = groq_client.chat.completions.create(
                            messages=[{"role": "system", "content": dna_context + "Pose la question suivante pour évaluer le chapitre."}] + st.session_state.messages[-3:],
                            model="llama-3.3-70b-versatile",
                        )
                        response = chat_completion.choices[0].message.content
                    except:
                        response = f"Question {st.session_state.q_count}: (Simulation) Peux-tu m'expliquer le concept de base de ce chapitre ?"
                else:
                    response = "Merci ! J'ai terminé l'évaluation. Je génère maintenant ton **Plan d'étude personnalisé** dans la section 'Plans'. Prêt à commencer ?"
                    st.session_state.diag_step = "finished"
                    # Update database/state for Box 4 (Plans)
                    st.session_state.user_data["plan_ready"] = True
            
            else:
                response = "Ton plan est prêt ! Rend-toi dans la section 'Plans' du Dashboard pour commencer la première leçon."

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
