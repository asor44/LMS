from turtle import st

from models_deprecated import Inventory, EquipmentAssignment, User

st.subheader("Gestion des équipements")

# Récupérer tous les équipements une seule fois
items = Inventory.get_all()

tab3_1, tab3_2, tab3_3 = st.tabs(["Mouvements de stock", "Affecter équipement", "Équipements affectés"])

with tab3_1:
    # Mouvements de stock
    with st.form("stock_movement"):
        if items:
            item = st.selectbox(
                "Article",
                items,
                format_func=lambda x: f"{x.item_name} (Stock actuel: {x.quantity} {x.unit})",
                key="stock_movement_item"
            )
            movement_type = st.selectbox("Type de mouvement", ["Entrée", "Sortie"])
            quantity = st.number_input("Quantité", min_value=1)

            if st.form_submit_button("Enregistrer"):
                new_quantity = item.quantity + quantity if movement_type == "Entrée" else item.quantity - quantity
                if new_quantity >= 0:
                    if Inventory.update_quantity(item.id, new_quantity):
                        st.success("Mouvement enregistré!")
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'enregistrement du mouvement")
                else:
                    st.error("Stock insuffisant pour cette sortie")
        else:
            st.warning("Aucun article en stock")

with tab3_2:
    # Affecter équipement
    with st.form("assign_equipment"):
        # Sélection de l'utilisateur
        users = User.get_all()
        selected_user = st.selectbox(
            "Utilisateur",
            users,
            format_func=lambda x: f"{x.name} ({x.status})",
            key="assignment_user"
        )

        # Sélection de l'équipement
        if items:
            available_items = [item for item in items if item.quantity > 0]
            if available_items:
                selected_item = st.selectbox(
                    "Équipement",
                    available_items,
                    format_func=lambda x: f"{x.item_name} (Disponible: {x.quantity} {x.unit})",
                    key="assignment_item"
                )

                quantity = st.number_input(
                    "Quantité à affecter",
                    min_value=1,
                    max_value=selected_item.quantity,
                    value=min(1, selected_item.quantity),
                    key=f"qty_assignment"
                )

                if st.form_submit_button("Affecter"):
                    try:
                        EquipmentAssignment.assign_to_user(
                            selected_item.id,
                            selected_user.id,
                            quantity
                        )
                        st.success(f"Équipement affecté à {selected_user.name}")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Erreur lors de l'affectation: {str(e)}")
            else:
                st.warning("Aucun équipement disponible en stock")
                st.form_submit_button("Affecter", disabled=True)
        else:
            st.warning("Aucun équipement enregistré")
            st.form_submit_button("Affecter", disabled=True)

with tab3_3:
    # Équipements affectés
    if 'user' in st.session_state and st.session_state.user:
        user = st.session_state.user

        # Permettre aux administrateurs de voir les équipements de tous les utilisateurs
        if user.status == 'administration' or is_storekeeper:
            users = User.get_all()
            # Créer une liste avec l'utilisateur connecté en premier, puis les autres
            user_list = [user] + [u for u in users if u.id != user.id]

            # Champ de recherche pour filtrer les utilisateurs
            search_query = st.text_input("Rechercher un utilisateur", "")

            # Filtrer les utilisateurs en fonction de la recherche
            if search_query:
                filtered_users = [u for u in user_list if search_query.lower() in u.name.lower()]
            else:
                filtered_users = user_list

            # Sélection de l'utilisateur
            selected_user = st.selectbox(
                "Voir les équipements de",
                filtered_users,
                format_func=lambda x: f"{x.name} ({x.status})",
                index=0
            )

            # Afficher les équipements de l'utilisateur sélectionné
            assignments = EquipmentAssignment.get_user_assignments(selected_user.id)
            if assignments:
                st.write(f"Équipements affectés à : {selected_user.name}")
                items = Inventory.get_all()  # Pour avoir les détails des items
                for assignment in assignments:
                    item = next((i for i in items if i.id == assignment.inventory_id), None)
                    if item:
                        with st.expander(f"{item.item_name} - {assignment.quantity} {item.unit}"):
                            st.write(f"**Catégorie:** {item.category}")
                            st.write(f"**Quantité assignée:** {assignment.quantity} {item.unit}")
                            st.write(
                                f"**Date d'assignation:** {assignment.assigned_at.strftime('%d/%m/%Y')}")

                            # Option de retour pour les administrateurs/magasiniers
                            if st.button("Retourner", key=f"return_{assignment.id}"):
                                if assignment.return_equipment():
                                    st.success("Équipement retourné avec succès!")
                                    st.rerun()
                                else:
                                    st.error("Erreur lors du retour de l'équipement")
            else:
                st.info(f"Aucun équipement n'est actuellement assigné à {selected_user.name}")

        # Pour les autres utilisateurs (cadet, AMC), afficher uniquement leurs équipements
        else:
            st.write(f"Équipements affectés à : {user.name}")
            assignments = EquipmentAssignment.get_user_assignments(user.id)

            if assignments:
                items = Inventory.get_all()  # Pour avoir les détails des items
                for assignment in assignments:
                    item = next((i for i in items if i.id == assignment.inventory_id), None)
                    if item:
                        with st.expander(f"{item.item_name} - {assignment.quantity} {item.unit}"):
                            st.write(f"**Catégorie:** {item.category}")
                            st.write(f"**Quantité assignée:** {assignment.quantity} {item.unit}")
                            st.write(
                                f"**Date d'assignation:** {assignment.assigned_at.strftime('%d/%m/%Y')}")

                            # Option de retour d'équipement
                            if st.button("Retourner", key=f"return_{assignment.id}"):
                                if assignment.return_equipment():
                                    st.success("Équipement retourné avec succès!")
                                    st.rerun()
                                else:
                                    st.error("Erreur lors du retour de l'équipement")
            else:
                st.info("Aucun équipement ne vous est actuellement assigné")
    else:
        st.warning("Veuillez vous connecter pour voir vos équipements assignés")
