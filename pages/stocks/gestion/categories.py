from turtle import st

from models_deprecated import InventoryCategory, CategoryField

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
                field_name = st.text_input(f"Nom du champ {i + 1}")
            with col2:
                field_type = st.selectbox(
                    f"Type {i + 1}",
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
                                    st.error(
                                        f"Un champ nommé '{new_field_name}' existe déjà dans cette catégorie")
                                    st.stop()

                            st.success("Catégorie mise à jour avec succès!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de la mise à jour: {str(e)}")
