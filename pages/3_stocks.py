import streamlit as st
from models import Inventory, InventoryCategory, CategoryField, User, EquipmentAssignment, EquipmentRequest

def check_authentication():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("Veuillez vous connecter")
        st.stop()

def main():
    check_authentication()

    st.title("Gestion des Stocks")
    user = st.session_state.user

    # Vérifier les permissions d'administration et le rôle magasinier
    is_admin = user.status == 'administration'
    is_parent = user.status == 'parent'
    is_storekeeper = user.has_role('magasinier')

    # Si l'utilisateur est un magasinier ou un admin, afficher l'interface complète
    if is_storekeeper or is_admin:
        # Interface d'administration complète
        tab1, tab2, tab3, tab4 = st.tabs(["Inventaire", "Catégories", "Mouvements", "Demandes d'équipement"])

        with tab1:
            # Ajouter un nouvel article
            with st.expander("Ajouter un nouvel article"):
                with st.form("new_item"):
                    item_name = st.text_input("Nom de l'article")
                    categories = InventoryCategory.get_all()
                    if categories:
                        selected_category = st.selectbox(
                            "Catégorie",
                            categories,
                            format_func=lambda x: x.name
                        )
                    quantity = st.number_input("Quantité", min_value=0)
                    unit = st.text_input("Unité (ex: pièces, kg, etc.)")
                    min_quantity = st.number_input("Quantité minimum d'alerte", min_value=0)
                    
                    # Option pour télécharger une photo
                    st.write("Photo de l'article (facultatif)")
                    photo_option = st.radio(
                        "Choisir une méthode",
                        ["Aucune photo", "Télécharger une image", "Utiliser une URL"],
                        horizontal=True
                    )
                    
                    photo_data = None
                    if photo_option == "Télécharger une image":
                        uploaded_file = st.file_uploader("Choisir une image", type=["jpg", "jpeg", "png"])
                        if uploaded_file is not None:
                            # Lire les données binaires de l'image
                            photo_data = uploaded_file.getvalue()
                    elif photo_option == "Utiliser une URL":
                        photo_data = st.text_input("URL de la photo", help="Entrez l'URL complète d'une image")

                    if st.form_submit_button("Ajouter"):
                        try:
                            if not item_name or not unit:
                                st.error("Le nom de l'article et l'unité sont requis")
                            else:
                                category_name = selected_category.name if categories and selected_category else "Non catégorisé"
                                new_item = Inventory.create(
                                    item_name=item_name,
                                    category=category_name,
                                    quantity=quantity,
                                    unit=unit,
                                    min_quantity=min_quantity,
                                    photo_data=photo_data
                                )
                                if new_item:
                                    st.success("Article ajouté avec succès!")
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la création de l'article")
                        except Exception as e:
                            st.error(f"Erreur lors de la création: {str(e)}")

            # Afficher l'inventaire existant
            st.subheader("Articles en stock")
            items = Inventory.get_all()
            if items:
                for item in items:
                    with st.expander(f"{item.item_name} - {item.quantity} {item.unit}"):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**Catégorie:** {item.category}")
                            st.write(f"**Stock actuel:** {item.quantity} {item.unit}")
                            st.write(f"**Seuil d'alerte:** {item.min_quantity} {item.unit}")

                            # Afficher la photo si disponible
                            if hasattr(item, 'photo_url') and item.photo_url:
                                st.image(item.photo_url, caption=item.item_name, width=300)

                            if item.quantity <= item.min_quantity:
                                st.warning("⚠️ Stock bas")

                        if is_admin or is_storekeeper:
                            with col2:
                                with st.form(f"edit_item_{item.id}"):
                                    new_quantity = st.number_input(
                                        "Nouvelle quantité",
                                        min_value=0,
                                        value=item.quantity
                                    )
                                    
                                    # Options pour la photo
                                    st.write("Photo de l'article")
                                    
                                    # Déterminer si une photo existe déjà
                                    has_existing_photo = hasattr(item, 'photo_url') and item.photo_url
                                    
                                    # Afficher la photo actuelle s'il y en a une
                                    if has_existing_photo:
                                        st.image(item.photo_url, caption="Photo actuelle", width=150)
                                    
                                    photo_option = st.radio(
                                        "Modifier la photo",
                                        ["Conserver l'actuelle" if has_existing_photo else "Aucune photo", 
                                         "Télécharger une nouvelle image", 
                                         "Utiliser une URL",
                                         "Supprimer la photo" if has_existing_photo else ""],
                                        horizontal=True,
                                        # Ne pas afficher l'option "Supprimer" s'il n'y a pas de photo
                                        index=0,
                                        label_visibility="visible"
                                    )
                                    
                                    new_photo_data = None
                                    if photo_option == "Télécharger une nouvelle image":
                                        uploaded_file = st.file_uploader(
                                            "Choisir une image", 
                                            type=["jpg", "jpeg", "png"],
                                            key=f"upload_{item.id}"
                                        )
                                        if uploaded_file is not None:
                                            # Lire les données binaires de l'image
                                            new_photo_data = uploaded_file.getvalue()
                                            # Prévisualiser l'image téléchargée
                                            st.image(new_photo_data, caption="Nouvelle photo", width=150)
                                    elif photo_option == "Utiliser une URL":
                                        current_url = item.photo_url if has_existing_photo else ""
                                        new_photo_data = st.text_input(
                                            "URL de la photo", 
                                            value=current_url,
                                            help="Entrez l'URL complète d'une image",
                                            key=f"url_{item.id}"
                                        )
                                    
                                    if st.form_submit_button("Mettre à jour"):
                                        # Mettre à jour la quantité
                                        quantity_updated = Inventory.update_quantity(item.id, new_quantity)
                                        
                                        # Mettre à jour la photo si nécessaire
                                        photo_updated = True
                                        if photo_option == "Supprimer la photo":
                                            # Supprimer la photo
                                            photo_updated = Inventory.remove_photo(item.id)
                                        elif photo_option != "Conserver l'actuelle" and photo_option != "Aucune photo" and photo_option != "":
                                            if new_photo_data:  # Ne mettre à jour que si des données ont été fournies
                                                photo_updated = Inventory.update_photo_url(item.id, new_photo_data)
                                            # Si l'option pour modifier la photo a été choisie mais aucune donnée fournie, on ne fait rien
                                        
                                        if quantity_updated and photo_updated:
                                            st.success("Article mis à jour!")
                                            st.rerun()
                                        else:
                                            st.error("Erreur lors de la mise à jour")

                                # Bouton de suppression
                                if st.button("🗑️ Supprimer", key=f"del_item_{item.id}"):
                                    if st.warning("Êtes-vous sûr de vouloir supprimer cet article ?"):
                                        if Inventory.delete(item.id):
                                            st.success("Article supprimé avec succès!")
                                            st.rerun()
                                        else:
                                            st.error("Impossible de supprimer l'article. Il est peut-être utilisé dans une activité ou assigné à un utilisateur.")
            else:
                st.info("Aucun article en stock. Utilisez le formulaire ci-dessus pour ajouter des articles.")

        with tab2:
            if is_admin or is_storekeeper:
                with st.expander("Créer une nouvelle catégorie"):
                    with st.form("new_category"):
                        category_name = st.text_input("Nom de la catégorie")
                        category_description = st.text_area("Description")

                        st.subheader("Champs personnalisés")
                        num_fields = st.number_input("Nombre de champs", min_value=1, max_value=10, value=1)

                        fields = []
                        for i in range(num_fields):
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                field_name = st.text_input(f"Nom du champ {i+1}")
                            with col2:
                                field_type = st.selectbox(
                                    f"Type {i+1}",
                                    ["text", "number", "date"],
                                    key=f"type_{i}"
                                )
                            with col3:
                                required = st.checkbox(f"Requis", key=f"req_{i}")
                            fields.append((field_name, field_type, required))

                        if st.form_submit_button("Créer"):
                            try:
                                # Créer la catégorie
                                category = InventoryCategory.create(category_name, category_description)

                                # Ajouter les champs
                                for field_name, field_type, required in fields:
                                    if field_name:  # Ne pas créer de champ sans nom
                                        CategoryField.create(
                                            category.id,
                                            field_name,
                                            field_type,
                                            required
                                        )
                                st.success("Catégorie créée avec succès!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur lors de la création: {str(e)}")

                # Afficher et modifier les catégories existantes
                st.subheader("Catégories existantes")
                categories = InventoryCategory.get_all()

                for category in categories:
                    with st.expander(f"{category.name}"):
                        # Bouton de suppression de la catégorie
                        col1, col2 = st.columns([3, 1])
                        with col2:
                            if st.button("🗑️ Supprimer", key=f"del_cat_{category.id}"):
                                if InventoryCategory.delete(category.id):
                                    st.success("Catégorie supprimée avec succès!")
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la suppression de la catégorie")

                        with col1:
                            # Affichage des champs existants et leurs boutons de suppression
                            if category.fields:
                                st.subheader("Champs existants")
                                for field in category.fields:
                                    col1, col2 = st.columns([3, 1])
                                    with col1:
                                        st.write(f"**{field.field_name}** ({field.field_type})")
                                        if field.required:
                                            st.caption("Champ requis")
                                    with col2:
                                        if st.button("🗑️", key=f"del_field_{field.id}"):
                                            if CategoryField.delete(field.id):
                                                st.success("Champ supprimé!")
                                                st.rerun()
                                            else:
                                                st.error("Erreur lors de la suppression du champ")

                            # Formulaire de modification
                            with st.form(f"edit_category_{category.id}"):
                                new_name = st.text_input("Nom", value=category.name)
                                new_description = st.text_area("Description", value=category.description)

                                st.subheader("Modifier les champs existants")
                                updated_fields = []
                                if category.fields:
                                    for field in category.fields:
                                        col1, col2, col3 = st.columns([2, 2, 1])
                                        with col1:
                                            field_name = st.text_input(
                                                "Nom",
                                                value=field.field_name,
                                                key=f"field_name_{field.id}"
                                            )
                                        with col2:
                                            field_type = st.selectbox(
                                                "Type",
                                                ["text", "number", "date"],
                                                index=["text", "number", "date"].index(field.field_type),
                                                key=f"field_type_{field.id}"
                                            )
                                        with col3:
                                            required = st.checkbox(
                                                "Requis",
                                                value=field.required,
                                                key=f"field_req_{field.id}"
                                            )
                                        updated_fields.append((field.id, field_name, field_type, required))

                                st.subheader("Ajouter un nouveau champ")
                                new_field_name = st.text_input("Nom du champ", key=f"new_field_{category.id}")
                                new_field_type = st.selectbox(
                                    "Type du champ",
                                    ["text", "number", "date"],
                                    key=f"new_type_{category.id}"
                                )
                                new_field_required = st.checkbox(
                                    "Champ requis",
                                    key=f"new_req_{category.id}"
                                )

                                if st.form_submit_button("Mettre à jour"):
                                    try:
                                        # Mettre à jour la catégorie
                                        if category.update(new_name, new_description):
                                            # Mettre à jour les champs existants
                                            if category.fields:
                                                for field_id, field_name, field_type, required in updated_fields:
                                                    field = next((f for f in category.fields if f.id == field_id), None)
                                                    if field:
                                                        field.update(field_name, field_type, required)

                                            # Ajouter le nouveau champ si spécifié
                                            if new_field_name:
                                                # Vérifier si le nom existe déjà
                                                existing_names = [f.field_name for f in category.fields]
                                                if new_field_name not in existing_names:
                                                    CategoryField.create(
                                                        category.id,
                                                        new_field_name,
                                                        new_field_type,
                                                        new_field_required
                                                    )
                                                else:
                                                    st.error(f"Un champ nommé '{new_field_name}' existe déjà dans cette catégorie")
                                                    st.stop()

                                            st.success("Catégorie mise à jour avec succès!")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Erreur lors de la mise à jour: {str(e)}")

        with tab3:
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
                                        st.write(f"**Date d'assignation:** {assignment.assigned_at.strftime('%d/%m/%Y')}")

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
                                        st.write(f"**Date d'assignation:** {assignment.assigned_at.strftime('%d/%m/%Y')}")

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

        with tab4:
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

    # Si l'utilisateur est un parent, afficher uniquement les équipements des enfants
    elif is_parent:
        st.subheader("Équipements de vos enfants")
        # Récupérer uniquement les équipements des enfants du parent
        items = Inventory.get_by_parent(user.id)

        if items:
            for item in items:
                with st.expander(f"{item.item_name} - {item.quantity} {item.unit}"):
                    st.write(f"**Catégorie:** {item.category}")
                    st.write(f"**Stock actuel:** {item.quantity} {item.unit}")

                    # Afficher les assignations pour les enfants du parent
                    children = user.get_children()
                    for child in children:
                        assignments = EquipmentAssignment.get_user_assignments(child.id)
                        child_assignments = [a for a in assignments if a.inventory_id == item.id]

                        if child_assignments:
                            st.write(f"**Équipement assigné à {child.name}:**")
                            for assignment in child_assignments:
                                st.write(f"- Quantité: {assignment.quantity} {item.unit}")
                                st.write(f"- Date d'assignation: {assignment.assigned_at.strftime('%d/%m/%Y')}")
        else:
            st.info("Aucun équipement n'est actuellement assigné à vos enfants")

    # Pour tous les autres utilisateurs (cadet, AMC), afficher uniquement leurs équipements
    else:
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
                        # TODO: Implement EquipmentRequest.create() in models.py
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

if __name__ == "__main__":
    main()