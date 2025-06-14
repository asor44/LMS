import streamlit as st
import database
from models import User
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration de la page
st.set_page_config(
    page_title="Gestion des présences - Cadets de la défense de Nantes",
    page_icon="📋",
    layout="wide"
)

def check_authentication():
    """Vérifie si l'utilisateur est authentifié"""
    if 'user' not in st.session_state or not st.session_state.user:
        st.warning("Vous devez être connecté pour accéder à cette page.")
        st.stop()
    return True

def main():
    try:
        # Vérifier l'authentification
        check_authentication()
        
        # Titre de la page
        st.title("📋 Gestion des présences")
        
        # Interface pour scanner les QR codes ou saisir manuellement
        st.markdown("## Scanner un QR Code de présence")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Scanner via la caméra")
            st.info("Cette fonctionnalité nécessite l'accès à votre caméra pour scanner les QR codes.")
            if st.button("Activer la caméra", key="activate_camera"):
                st.markdown("🎥 Caméra activée, veuillez scanner un QR code.")
                # Ici, il faudrait implémenter la logique de scan de QR code avec OpenCV et pyzbar
                st.error("Fonctionnalité de scan en cours de développement.")
        
        with col2:
            st.markdown("### Saisie manuelle du code")
            with st.form("manual_code_form"):
                qr_code = st.text_input("Code QR", placeholder="Entrez le code QR manuellement")
                submit = st.form_submit_button("Valider")
                
                if submit and qr_code:
                    # Logique de traitement du code QR
                    st.success(f"Code '{qr_code}' validé avec succès!")
        
        # Historique des présences
        st.markdown("## Historique des présences")
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        with col1:
            date_filter = st.date_input("Date")
        with col2:
            # Exemple de filtre par activité (à remplacer par les vraies activités)
            activity_filter = st.selectbox(
                "Activité", 
                ["Toutes les activités", "Formation militaire", "Sport", "Activité culturelle"]
            )
        with col3:
            # Exemple de filtre par statut (à remplacer par les vrais statuts)
            status_filter = st.selectbox(
                "Statut", 
                ["Tous les statuts", "Présent", "Absent", "Retard"]
            )
            
        # Tableau d'exemple (à remplacer par les données réelles)
        st.markdown("### Liste des participants")
        
        # Exemple de données (à remplacer par les vraies données de la DB)
        example_data = [
            {"name": "Jean Dupont", "status": "Présent", "check_in": "09:15", "check_out": "17:30"},
            {"name": "Marie Martin", "status": "Absent", "check_in": "-", "check_out": "-"},
            {"name": "Pierre Durand", "status": "Retard", "check_in": "10:45", "check_out": "17:30"},
            {"name": "Sophie Petit", "status": "Présent", "check_in": "09:00", "check_out": "17:25"}
        ]
        
        # Affichage du tableau
        if example_data:
            st.table(example_data)
        else:
            st.info("Aucune donnée de présence disponible pour les filtres sélectionnés.")
            
    except Exception as e:
        logger.error(f"Error in presence page: {e}")
        st.error("Une erreur est survenue lors du chargement de la page de présence")

if __name__ == "__main__":
    main()