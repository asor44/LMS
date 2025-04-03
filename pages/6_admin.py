import streamlit as st

from models_deprecated import User, Role, Permission
from utils import validate_email


def check_admin():
    """Verify admin access rights"""
    if not st.session_state.user:
        st.error("Veuillez vous connecter")
        st.stop()

    # Check if user has admin status or manage_roles permission
    user = st.session_state.user
    if user.status != 'administration' and not any(perm in ['manage_roles', 'manage_users'] 
                                                    for perm in user.get_permissions()):
        st.error("Accès non autorisé")
        st.stop()

def main():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("Veuillez vous connecter")
        st.stop()

    check_admin()

    st.title("Administration")

    tabs = st.tabs(["Gestion des Utilisateurs", "Import Utilisateurs", "Rôles et Permissions", "Associations Parent-Enfant"])

    with tabs[0]:
        st.subheader("Utilisateurs existants")
        users = User.get_all()

        # Sélection multiple pour suppression en bloc
        selected_users = st.multiselect(
            "Sélectionner des utilisateurs à supprimer",
            options=users,
            format_func=lambda x: f"{x.name} ({x.email})",
            key="users_to_delete"
        )

        if selected_users and st.button("Supprimer les utilisateurs sélectionnés"):
            if st.warning("Êtes-vous sûr de vouloir supprimer ces utilisateurs ?"):
                deleted, errors = User.bulk_delete([u.id for u in selected_users])
                if errors:
                    st.error("\n".join(errors))
                if deleted:
                    st.success(f"{deleted} utilisateur(s) supprimé(s)")
                    st.rerun()

        st.divider()
        st.subheader("Modifier un utilisateur")

        for user in users:
            with st.expander(f"{user.name} ({user.email})"):
                with st.form(f"edit_user_{user.id}"):
                    new_name = st.text_input("Nom", user.name)
                    new_first_name = st.text_input("Prénom", user.first_name)
                    new_rank = st.text_input("Grade", user.rank)
                    new_email = st.text_input("Email", user.email)
                    new_status = st.selectbox(
                        "Statut",
                        ["parent", "cadet", "AMC", "animateur", "administration"],
                        index=["parent", "cadet", "AMC", "animateur", "administration"].index(user.status)
                    )
                    new_password = st.text_input("Nouveau mot de passe (laisser vide pour ne pas changer)", type="password")

                    available_roles = [role.name for role in Role.get_all()]
                    new_roles = st.multiselect(
                        "Rôles",
                        available_roles,
                        default=user.get_roles(),
                        key=f"edit_user_roles_{user.id}"
                    )

                    if st.form_submit_button("Mettre à jour"):
                        success = user.update(
                            name=new_name,
                            first_name=new_first_name,
                            rank=new_rank,
                            email=new_email,
                            status=new_status,
                            roles=new_roles,
                            password=new_password if new_password else None
                        )
                        if success:
                            st.success("Utilisateur mis à jour avec succès!")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la mise à jour")

        st.divider()
        st.subheader("Créer un nouvel utilisateur")

        with st.form("new_user"):
            email = st.text_input("Email")
            name = st.text_input("Nom")
            first_name = st.text_input("Prénom")
            rank = st.text_input("Grade")
            password = st.text_input("Mot de passe", type="password")
            status = st.selectbox(
                "Statut",
                ["parent", "cadet", "AMC", "animateur", "administration"]
            )

            available_roles = [role.name for role in Role.get_all()]
            selected_roles = st.multiselect(
                "Rôles",
                available_roles,
                key="new_user_roles"
            )

            if st.form_submit_button("Créer l'utilisateur"):
                if not validate_email(email):
                    st.error("Email invalide")
                elif not password or len(password) < 6:
                    st.error("Le mot de passe doit contenir au moins 6 caractères")
                else:
                    try:
                        User.create(
                            email=email, 
                            password=password, 
                            status=status, 
                            name=name,
                            first_name=first_name,
                            rank=rank,
                            roles=selected_roles
                        )
                        st.success("Utilisateur créé avec succès!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de la création: {str(e)}")

    with tabs[1]:
        st.subheader("Import d'utilisateurs en bloc")
        st.markdown("""
        Téléchargez un fichier CSV avec les colonnes suivantes:
        ```
        email,nom,statut,mot_de_passe,roles
        user@example.com,Nom Utilisateur,parent,password123,role1|role2
        ```
        Note: La colonne 'roles' est optionnelle. Utilisez | pour séparer plusieurs rôles.
        """)

        uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv")

        if uploaded_file:
            csv_data = uploaded_file.getvalue().decode('utf-8')
            if st.button("Importer les utilisateurs"):
                users, errors = User.bulk_create_from_csv(csv_data)
                if errors:
                    st.error("Erreurs lors de l'import:")
                    for error in errors:
                        st.error(error)
                if users:
                    st.success(f"{len(users)} utilisateur(s) importé(s) avec succès!")
                    st.rerun()

        # Template de fichier CSV
        csv_template = """email,nom,statut,mot_de_passe,roles
user@example.com,Nom Utilisateur,parent,password123,role1|role2"""

        st.download_button(
            "Télécharger le template CSV",
            csv_template,
            "template_utilisateurs.csv",
            "text/csv"
        )

    with tabs[2]:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Créer un nouveau rôle")
            with st.form("new_role"):
                role_name = st.text_input("Nom du rôle")
                role_description = st.text_area("Description")
                available_permissions = [perm.name for perm in Permission.get_all()]
                selected_permissions = st.multiselect(
                    "Permissions",
                    available_permissions,
                    key="new_role_permissions"
                )

                if st.form_submit_button("Créer le rôle"):
                    if not role_name:
                        st.error("Le nom du rôle est requis")
                    else:
                        try:
                            Role.create(role_name, role_description, selected_permissions)
                            st.success("Rôle créé avec succès!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur lors de la création: {str(e)}")

        with col2:
            st.subheader("Modifier les rôles existants")
            roles = Role.get_all()
            for role in roles:
                with st.expander(role.name):
                    st.write(f"Description: {role.description}")
                    current_permissions = role.get_permissions()
                    st.write("Permissions actuelles:", ", ".join(current_permissions))

                    available_permissions = [perm.name for perm in Permission.get_all()]
                    new_permissions = st.multiselect(
                        "Modifier les permissions",
                        available_permissions,
                        default=current_permissions,
                        key=f"edit_role_{role.name}"
                    )

                    if st.button("Mettre à jour", key=f"update_{role.name}"):
                        try:
                            role.update_permissions(new_permissions)
                            st.success("Permissions mises à jour avec succès!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur lors de la mise à jour: {str(e)}")

    with tabs[3]:
        st.subheader("Association Parent-Enfant")

        # Filtrer les parents et les enfants
        parents = [u for u in users if u.status == "parent"]
        children = [u for u in users if u.status in ["cadet", "AMC"]]

        with st.form("parent_child_association"):
            parent = st.selectbox(
                "Sélectionner un parent",
                parents,
                format_func=lambda x: f"{x.name} ({x.email})",
                key="parent_select"
            )

            child = st.selectbox(
                "Sélectionner un enfant",
                children,
                format_func=lambda x: f"{x.name} ({x.email})",
                key="child_select"
            )

            if st.form_submit_button("Associer"):
                if parent and child:
                    if parent.add_child(child.id):
                        st.success(f"Association créée entre {parent.name} et {child.name}")
                        st.rerun()
                    else:
                        st.error("Erreur lors de l'association")

        # Afficher les associations existantes
        st.subheader("Associations existantes")
        for parent in parents:
            with st.expander(f"Enfants de {parent.name}"):
                children = parent.get_children()
                if children:
                    for child in children:
                        st.write(f"- {child.name} ({child.email})")
                else:
                    st.info("Aucun enfant associé")

if __name__ == "__main__":
    main()