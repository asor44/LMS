from turtle import st

from models_deprecated import EquipmentAssignment, Inventory, EquipmentRequest


def affichage_cadets(user):
    st.subheader("Mes équipements")

    # Nouvel onglet pour les demandes et les équipements
    tab1, tab2 = st.tabs(["Mes équipements", "Demande d'équipement"])

    with tab1:
        assignments = EquipmentAssignment.get_user_assignments(user.id)

        if assignments:
            items = Inventory.get_all()  # Pour avoir les détails des items
            for assignment in assignments:
                item = next((i for i in items if i.id == assignment.inventory_id), None)
                if item:
                    with st.expander(f"{item.item_name} - {assignment.quantity} {item.unit}"):
                        st.write(f"**Catégorie:** {item.category}")
                        st.write(f"**Quantité assignée:** {assignment.quantity} {item.unit}")
                        st.write(f"**Date d'assignation:** {assignment.assigned_at.strftime('%d/%m/%Y')}")

                        # Ajouter un bouton pour demander un changement pour cet équipement
                        if st.button("Demander un changement", key=f"change_req_{assignment.id}"):
                            st.session_state.selected_item_for_change = item
                            st.session_state.change_mode = "modification"
                            st.rerun()
        else:
            st.info("Aucun équipement ne vous est actuellement assigné")

    with tab2:
        st.subheader("Faire une demande d'équipement")

        # Initialiser le mode de demande
        if 'change_mode' not in st.session_state:
            st.session_state.change_mode = "nouveau"
        if 'selected_item_for_change' not in st.session_state:
            st.session_state.selected_item_for_change = None

        with st.form("equipment_request"):
            # Type de demande
            request_type = st.selectbox(
                "Type de demande",
                [
                    "Nouvel équipement",
                    "Remplacement (cassé)",
                    "Changement de taille",
                    "Autre"
                ]
            )

            # Si c'est une modification, afficher l'équipement concerné
            if st.session_state.change_mode == "modification" and st.session_state.selected_item_for_change:
                st.write(f"Équipement concerné: {st.session_state.selected_item_for_change.item_name}")
                equipment_id = st.session_state.selected_item_for_change.id
            else:
                # Pour une nouvelle demande, permettre de choisir l'équipement
                items = Inventory.get_all()
                equipment = st.selectbox(
                    "Équipement souhaité",
                    items,
                    format_func=lambda x: f"{x.item_name} ({x.category})"
                )
                equipment_id = equipment.id if equipment else None

            quantity = st.number_input("Quantité souhaitée", min_value=1, value=1)
            reason = st.text_area(
                "Raison de la demande",
                help="Expliquez pourquoi vous avez besoin de cet équipement ou pourquoi vous souhaitez le changer"
            )

            if st.form_submit_button("Envoyer la demande"):
                try:
                    # TODO: Implement EquipmentRequest.create() in models_deprecated.py
                    EquipmentRequest.create(
                        user_id=user.id,
                        equipment_id=equipment_id,
                        request_type=request_type,
                        quantity=quantity,
                        reason=reason,
                        status="pending"  # Les magasiniers devront valider
                    )
                    st.success("Votre demande a été envoyée aux magasiniers pour validation")
                    st.session_state.change_mode = "nouveau"
                    st.session_state.selected_item_for_change = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur lors de l'envoi de la demande: {str(e)}")

        # Bouton pour annuler une modification en cours
        if st.session_state.change_mode == "modification":
            if st.button("Annuler la demande de changement"):
                st.session_state.change_mode = "nouveau"
                st.session_state.selected_item_for_change = None
                st.rerun()