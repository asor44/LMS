import streamlit as st


def check_authentication():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("Veuillez vous connecter")
        st.stop()
    return True

def main():
    check_authentication()
    user = st.session_state.user

    st.title("Messages et Communications")

    tab1, tab2 = st.tabs(["Nouveau Message", "Boîte de réception"])

    with tab1:
        with st.form("new_message"):
            # Get available recipients based on user's status
            available_recipients = user.get_available_recipients()

            # Create recipient selection with grade and firstname, now using multiselect
            selected_recipients = st.multiselect(
                "Destinataires",
                options=available_recipients,
                format_func=lambda x: f"{x.name} ({x.status})"  # Simplified format without rank and first_name
            )

            subject = st.text_input("Sujet")
            content = st.text_area("Message")

            if st.form_submit_button("Envoyer"):
                if selected_recipients:
                    success_count = 0
                    for recipient in selected_recipients:
                        if user.has_role('manage_communications'):  # Changed from has_permission
                            # TODO: Implement actual message sending here
                            success_count += 1

                    if success_count == len(selected_recipients):
                        st.success(f"Message envoyé à {len(selected_recipients)} destinataire(s)!")
                    elif success_count > 0:
                        st.warning(f"Message envoyé à {success_count}/{len(selected_recipients)} destinataires")
                    else:
                        st.info("Messages envoyés pour validation")
                else:
                    st.error("Veuillez sélectionner au moins un destinataire")

    with tab2:
        st.subheader("Messages reçus")

        # TODO: Récupérer les vrais messages depuis la base de données
        messages = [
            {
                "date": "2024-01-19",
                "sender": "Admin",
                "subject": "Rappel activité",
                "content": "N'oubliez pas l'activité de demain!"
            }
        ]

        for msg in messages:
            with st.expander(f"{msg['subject']} - {msg['date']}"):
                st.write(f"De: {msg['sender']}")
                st.write(msg['content'])

                if user.has_role('manage_communications'):  # Changed from has_permission
                    col1, col2 = st.columns(2)
                    with col1:
                        st.button("Approuver", key=f"approve_{msg['subject']}")
                    with col2:
                        st.button("Rejeter", key=f"reject_{msg['subject']}")

if __name__ == "__main__":
    main()