# Ajouter un nouvel article
from turtle import st

from models_deprecated import InventoryCategory, Inventory

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
                    ["Aucune photo", "Utiliser une URL"],
                    # , "Télécharger une image"
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
                                        st.error(
                                            "Impossible de supprimer l'article. Il est peut-être utilisé dans une activité ou assigné à un utilisateur.")
        else:
            st.info("Aucun article en stock. Utilisez le formulaire ci-dessus pour ajouter des articles.")