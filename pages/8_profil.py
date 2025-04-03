import streamlit as st

from models.User import User


def check_authentication():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("Veuillez vous connecter")
        st.stop()

def main():
    check_authentication()
    user = st.session_state.user

    st.title("Mon Profil")

    # Afficher les informations de l'utilisateur
    st.header("Informations")
    st.write(f"**Nom:** {user.name}")
    st.write(f"**Email:** {user.email}")
    st.write(f"**Statut:** {user.status}")
    if user.first_name:
        st.write(f"**Prénom:** {user.first_name}")
    if user.rank:
        st.write(f"**Grade:** {user.rank}")

    # Section pour changer le mot de passe
    st.header("Changer le mot de passe")
    with st.form("change_password"):
        current_password = st.text_input("Mot de passe actuel", type="password")
        new_password = st.text_input("Nouveau mot de passe", type="password")
        confirm_password = st.text_input("Confirmer le nouveau mot de passe", type="password")
        
        submitted = st.form_submit_button("Changer le mot de passe")
        
        if submitted:
            if not user.verify_password(current_password):
                st.error("Le mot de passe actuel est incorrect")
            elif new_password != confirm_password:
                st.error("Les nouveaux mots de passe ne correspondent pas")
            elif len(new_password) < 6:
                st.error("Le nouveau mot de passe doit contenir au moins 6 caractères")
            else:
                # Update user password
                if user.update(
                    name=user.name,
                    email=user.email,
                    status=user.status,
                    roles=user.get_roles(),
                    first_name=user.first_name,
                    rank=user.rank,
                    password=new_password
                ):
                    st.success("Mot de passe changé avec succès")
                    # Update session state
                    st.session_state.user = User.get_by_id(user.id)
                else:
                    st.error("Une erreur est survenue lors du changement de mot de passe")

if __name__ == "__main__":
    main()
