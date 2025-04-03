import streamlit as st
from models.User import User


class Authentification:
    def __init__(self, user: User):
        self.user = user


def check_authentication():
    user = st.session_state.get("user")

    if not isinstance(user, User):  # Vérifie que user est bien une instance de User
        st.error("Veuillez vous connecter")
        st.stop()
