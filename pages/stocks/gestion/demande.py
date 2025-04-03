from turtle import st

from models_deprecated import Inventory, User, EquipmentRequest

st.subheader("Demandes d'équipement en attente")

# Récupérer toutes les demandes en attente
pending_requests = EquipmentRequest.get_pending_requests()

if pending_requests:
    for request in pending_requests:
        # Récupérer les informations de l'utilisateur et de l'équipement
        user = User.get_by_id(request.user_id)
        equipment = next((item for item in Inventory.get_all() if item.id == request.equipment_id), None)

        if user and equipment and request.created_at:  # Add check for created_at
            with st.expander(f"Demande de {user.name} - {equipment.item_name}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.write(f"**Type de demande:** {request.request_type}")
                    st.write(f"**Équipement:** {equipment.item_name}")
                    st.write(f"**Quantité demandée:** {request.quantity}")
                    st.write(f"**Raison:** {request.reason}")
                    if request.created_at:  # Double-check before using strftime
                        st.write(f"**Date de la demande:** {request.created_at.strftime('%d/%m/%Y %H:%M')}")
                    else:
                        st.write("**Date de la demande:** Non disponible")

                with col2:
                    # Formulaire pour approuver/refuser la demande
                    with st.form(key=f"request_action_{request.id}"):
                        action = st.radio(
                            "Action",
                            ["Approuver", "Refuser"],
                            key=f"action_{request.id}"
                        )
                        reason = st.text_area(
                            "Raison du refus",
                            key=f"reason_{request.id}",
                            disabled=action == "Approuver"
                        )

                        if st.form_submit_button("Valider"):
                            if action == "Approuver":
                                success, message = request.approve()
                            else:
                                if not reason:
                                    st.error("Veuillez indiquer la raison du refus")
                                    st.stop()
                                success, message = request.reject(reason)

                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
        else:
            st.warning("Certaines informations de la demande sont manquantes")
else:
    st.info("Aucune demande en attente")