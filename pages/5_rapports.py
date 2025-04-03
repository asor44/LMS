import streamlit as st
from utils.pdf import PDFGenerator
from datetime import datetime, timedelta

def check_authentication():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("Veuillez vous connecter")
        st.stop()

    # Vérifier si l'utilisateur est un parent
    if st.session_state.user.status == 'parent':
        st.error("Accès non autorisé. Cette page est réservée au personnel administratif.")
        st.stop()

def main():
    check_authentication()
    
    st.title("Rapports et Statistiques")
    
    report_type = st.selectbox(
        "Type de rapport",
        ["Présences", "Activités", "Stocks", "Communications"]
    )
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Date de début",
            value=datetime.now() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input(
            "Date de fin",
            value=datetime.now()
        )
    
    if st.button("Générer le rapport"):
        # TODO: Récupérer les vraies données depuis la base de données
        data = [
            "Ligne 1 du rapport",
            "Ligne 2 du rapport",
            "Ligne 3 du rapport"
        ]
        
        pdf = PDFGenerator.generate_pdf_report(data, report_type)
        
        st.download_button(
            "Télécharger le rapport PDF",
            pdf,
            f"rapport_{report_type}_{datetime.now().strftime('%Y%m%d')}.pdf",
            "application/pdf"
        )
    
    # Affichage des statistiques
    st.subheader("Statistiques")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total présences", "150")
    with col2:
        st.metric("Activités réalisées", "12")
    with col3:
        st.metric("Messages envoyés", "45")
    
    # Graphique exemple
    chart_data = {
        'dates': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
        'présences': [25, 30, 28, 32, 35]
    }
    
    st.line_chart(chart_data)

if __name__ == "__main__":
    main()