import streamlit as st
from models import User, Activity
from datetime import datetime, date
from utils import generate_qr_code
import database
import cv2
from pyzbar.pyzbar import decode
import numpy as np

def check_authentication():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("Veuillez vous connecter")
        st.stop()

def scan_qr_code():
    """Fonction pour scanner les QR codes via la caméra web"""
    if 'camera_active' not in st.session_state:
        st.session_state.camera_active = False

    if st.button("Activer/Désactiver la caméra"):
        st.session_state.camera_active = not st.session_state.camera_active

    if st.session_state.camera_active:
        img_file_buffer = st.camera_input("Scanner un QR code")
        if img_file_buffer is not None:
            try:
                bytes_data = img_file_buffer.getvalue()
                cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
                qr_codes = decode(cv2_img)

                if qr_codes:
                    for qr_code in qr_codes:
                        data = qr_code.data.decode('utf-8')
                        try:
                            qr_type, activity_id, date_str = data.split('_')
                            activity = Activity.get_by_id(int(activity_id))

                            if activity:
                                if qr_type == "entry":
                                    if activity.record_attendance(st.session_state.user.id, is_entry=True):
                                        st.success("Entrée enregistrée avec succès!")
                                        st.session_state.camera_active = False
                                elif qr_type == "exit":
                                    if activity.record_attendance(st.session_state.user.id, is_entry=False):
                                        st.success("Sortie enregistrée avec succès!")
                                        st.session_state.camera_active = False
                            else:
                                st.error("Activité non trouvée")
                        except ValueError:
                            st.error("Format du QR code invalide")
                        except Exception as e:
                            st.error(f"Erreur lors du scan: {str(e)}")
                else:
                    st.warning("Aucun QR code détecté")
            except Exception as e:
                st.error(f"Erreur lors du traitement de l'image: {str(e)}")

def main():
    check_authentication()
    user = st.session_state.user

    st.title("Gestion des Présences")

    # Créer les onglets principaux
    tab_scanner, tab_admin = st.tabs(["Scanner un QR Code", "Administration"])

    with tab_scanner:
        st.markdown("### Scanner un QR Code")
        scan_qr_code()
        st.markdown("""
        ### Comment enregistrer votre présence :
        1. Cliquez sur le bouton "Activer/Désactiver la caméra"
        2. Autorisez l'accès à votre caméra si demandé
        3. Pointez votre caméra vers le QR code d'entrée à votre arrivée
        4. À la fin de l'activité, scannez le QR code de sortie
        """)

    with tab_admin:
        if user.has_permission('manage_attendance'):
            st.subheader("Administration des Présences")
            admin_tab1, admin_tab2 = st.tabs(["Générer QR Codes", "Gestion Manuelle"])

            with admin_tab1:
                st.markdown("### Générer QR Codes")
                activities = Activity.get_all()

                if activities:
                    selected_activity = st.selectbox(
                        "Sélectionner une activité",
                        activities,
                        format_func=lambda x: f"{x.name} ({x.date.strftime('%d/%m/%Y')})"
                    )

                    if selected_activity:
                        entry_data = f"entry_{selected_activity.id}_{datetime.now().strftime('%Y%m%d')}"
                        entry_qr = generate_qr_code(entry_data)
                        st.markdown("### QR Code d'entrée")
                        st.markdown(f'<img src="data:image/png;base64,{entry_qr}" style="width:300px">', unsafe_allow_html=True)

                        exit_data = f"exit_{selected_activity.id}_{datetime.now().strftime('%Y%m%d')}"
                        exit_qr = generate_qr_code(exit_data)
                        st.markdown("### QR Code de sortie")
                        st.markdown(f'<img src="data:image/png;base64,{exit_qr}" style="width:300px">', unsafe_allow_html=True)

                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                "Télécharger QR Code Entrée",
                                entry_qr,
                                file_name=f"qr_entree_{selected_activity.name}_{datetime.now().strftime('%Y%m%d')}.png",
                                mime="image/png"
                            )
                        with col2:
                            st.download_button(
                                "Télécharger QR Code Sortie",
                                exit_qr,
                                file_name=f"qr_sortie_{selected_activity.name}_{datetime.now().strftime('%Y%m%d')}.png",
                                mime="image/png"
                            )
                else:
                    st.warning("Aucune activité n'est disponible")

            with admin_tab2:
                st.markdown("### Gestion Manuelle")
                activities = Activity.get_all()

                if activities:
                    selected_activity = st.selectbox(
                        "Sélectionner une activité",
                        activities,
                        format_func=lambda x: f"{x.name} ({x.date.strftime('%d/%m/%Y')})",
                        key="manual_activity_select"
                    )

                    if selected_activity:
                        attendance_list = selected_activity.get_attendance_list()

                        if attendance_list:
                            st.write("Présences enregistrées:")
                            for attendance in attendance_list:
                                with st.expander(f"{attendance['name']} ({attendance['status']})"):
                                    st.write(f"**Entrée:** {attendance['entry_time'].strftime('%d/%m/%Y %H:%M') if attendance['entry_time'] else 'Non enregistrée'}")
                                    st.write(f"**Sortie:** {attendance['exit_time'].strftime('%d/%m/%Y %H:%M') if attendance['exit_time'] else 'Non enregistrée'}")

                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("Modifier entrée", key=f"entry_{attendance['user_id']}"):
                                            if selected_activity.record_attendance(attendance['user_id'], is_entry=True):
                                                st.success("Entrée mise à jour")
                                                st.rerun()
                                    with col2:
                                        if st.button("Modifier sortie", key=f"exit_{attendance['user_id']}"):
                                            if selected_activity.record_attendance(attendance['user_id'], is_entry=False):
                                                st.success("Sortie mise à jour")
                                                st.rerun()
                        else:
                            st.info("Aucune présence enregistrée")

                        with st.form("add_attendance"):
                            st.write("Ajouter une présence")
                            users = User.get_all()
                            selected_user = st.selectbox(
                                "Sélectionner un utilisateur",
                                users,
                                format_func=lambda x: f"{x.name} ({x.status})"
                            )

                            action = st.radio(
                                "Action",
                                ["Marquer l'entrée", "Marquer la sortie"]
                            )

                            if st.form_submit_button("Enregistrer"):
                                if action == "Marquer l'entrée":
                                    if selected_activity.record_attendance(selected_user.id, is_entry=True):
                                        st.success(f"Entrée enregistrée pour {selected_user.name}")
                                        st.rerun()
                                else:
                                    if selected_activity.record_attendance(selected_user.id, is_entry=False):
                                        st.success(f"Sortie enregistrée pour {selected_user.name}")
                                        st.rerun()
                else:
                    st.warning("Aucune activité n'est disponible")
        else:
            st.warning("Vous n'avez pas les permissions nécessaires pour accéder à cette section")

if __name__ == "__main__":
    main()