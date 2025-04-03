from datetime import time

import streamlit as st
from utils.authentification import check_authentication

from models.Activities import Activity
from models.Inventory import Inventory


def main():
    check_authentication()

    st.title("Gestion des Activités")

    if st.session_state.user.status == 'administration' or st.session_state.user.has_role('animateur'):
        with st.expander("Ajouter une nouvelle activité"):
            with st.form("new_activity"):
                name = st.text_input("Nom de l'activité")
                description = st.text_area("Description")
                location = st.text_input("Lieu de l'activité")
                date = st.date_input("Date")
                start_time = st.time_input("Heure de début", value=time(9, 0))
                end_time = st.time_input("Heure de fin", value=time(17, 0))
                max_participants = st.number_input("Nombre maximum de participants", min_value=1)

                # Options de repas
                col1, col2 = st.columns(2)
                with col1:
                    lunch_included = st.checkbox("Repas du midi inclus")
                with col2:
                    dinner_included = st.checkbox("Repas du soir inclus")

                # Équipement requis
                st.subheader("Équipement requis")
                equipment_list = []
                inventory_items = Inventory.get_all()

                if inventory_items:
                    for item in inventory_items:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            selected = st.checkbox(f"{item.item_name} (Disponible: {item.quantity} {item.unit})", 
                                               key=f"eq_{item.id}")
                        with col2:
                            if selected:
                                quantity = st.number_input(f"Quantité", 
                                                         min_value=1,
                                                         max_value=item.quantity,
                                                         key=f"qty_{item.id}")
                                equipment_list.append((item.id, quantity))

                if st.form_submit_button("Créer l'activité"):
                    try:
                        activity = Activity.create(
                            name=name,
                            description=description,
                            date=date,
                            start_time=start_time,
                            end_time=end_time,
                            max_participants=max_participants,
                            location=location,
                            lunch_included=lunch_included,
                            dinner_included=dinner_included
                        )
                        if equipment_list:
                            activity.update_equipment(equipment_list)
                        st.success("Activité créée avec succès!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de la création: {str(e)}")

    # Affichage des activités
    st.subheader("Activités à venir")
    activities = Activity.get_all()

    for activity in activities:
        with st.expander(f"{activity.name} - {activity.date.strftime('%d/%m/%Y')}"):
            # Affichage des détails de l'activité
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Description:** {activity.description}")
                st.write(f"**Lieu:** {activity.location or 'Non spécifié'}")
                st.write(f"**Date:** {activity.date.strftime('%d/%m/%Y')}")
                st.write(f"**Horaires:** {activity.start_time.strftime('%H:%M')} - {activity.end_time.strftime('%H:%M')}")

                # Affichage des options de repas
                repas = []
                if activity.lunch_included:
                    repas.append("Repas du midi")
                if activity.dinner_included:
                    repas.append("Repas du soir")
                if repas:
                    st.write("**Repas inclus:** " + ", ".join(repas))
                else:
                    st.write("**Repas:** Aucun repas inclus")

            with col2:
                attendance_list = activity.get_attendance_list()
                st.write(f"**Participants:** {len(attendance_list)}/{activity.max_participants}")

                # Affichage de l'équipement requis
                equipment = activity.get_required_equipment()
                if equipment:
                    st.write("**Équipement requis:**")
                    for eq in equipment:
                        st.write(f"- {eq[1]} ({eq[3]} {eq[4]})")

            # Options de modification/suppression pour les utilisateurs autorisés
            if st.session_state.user.status == 'administration' or st.session_state.user.has_role('animateur'):
                # Formulaire de modification
                with st.form(f"edit_activity_{activity.id}"):
                    st.subheader("Modifier l'activité")
                    new_name = st.text_input("Nom", value=activity.name)
                    new_description = st.text_area("Description", value=activity.description)
                    new_location = st.text_input("Lieu", value=activity.location or "")
                    new_date = st.date_input("Date", value=activity.date)
                    new_start_time = st.time_input("Heure de début", value=activity.start_time)
                    new_end_time = st.time_input("Heure de fin", value=activity.end_time)
                    new_max_participants = st.number_input(
                        "Nombre maximum de participants",
                        min_value=len(attendance_list),
                        value=activity.max_participants
                    )

                    # Options de repas
                    new_lunch = st.checkbox("Repas du midi inclus", value=activity.lunch_included)
                    new_dinner = st.checkbox("Repas du soir inclus", value=activity.dinner_included)

                    # Équipement requis
                    st.subheader("Équipement requis")
                    new_equipment_list = []
                    current_equipment = {eq[0]: eq[3] for eq in equipment}  # id: quantity

                    inventory_items = Inventory.get_all()
                    if inventory_items:
                        for item in inventory_items:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                selected = st.checkbox(
                                    f"{item.item_name} (Disponible: {item.quantity} {item.unit})",
                                    value=item.id in current_equipment,
                                    key=f"edit_eq_{activity.id}_{item.id}"
                                )
                            with col2:
                                if selected:
                                    quantity = st.number_input(
                                        f"Quantité",
                                        min_value=1,
                                        max_value=item.quantity,
                                        value=current_equipment.get(item.id, 1),
                                        key=f"edit_qty_{activity.id}_{item.id}"
                                    )
                                    new_equipment_list.append((item.id, quantity))

                    if st.form_submit_button("Mettre à jour"):
                        try:
                            if activity.update(
                                name=new_name,
                                description=new_description,
                                location=new_location,
                                date=new_date,
                                start_time=new_start_time,
                                end_time=new_end_time,
                                max_participants=new_max_participants,
                                lunch_included=new_lunch,
                                dinner_included=new_dinner
                            ):
                                activity.update_equipment(new_equipment_list)
                                st.success("Activité mise à jour avec succès!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur lors de la mise à jour: {str(e)}")

                # Bouton de suppression en dehors du formulaire
                st.markdown("---")  # Séparateur visuel
                col_delete_1, col_delete_2, col_delete_3 = st.columns([2, 1, 1])
                with col_delete_2:
                    # Stockage de l'état de la confirmation dans session_state
                    delete_key = f"delete_confirm_{activity.id}"
                    if delete_key not in st.session_state:
                        st.session_state[delete_key] = False

                    if not st.session_state[delete_key]:
                        if st.button("🗑️ Supprimer", key=f"delete_{activity.id}"):
                            st.session_state[delete_key] = True
                            st.rerun()
                    else:
                        if st.button("❌ Annuler", key=f"cancel_{activity.id}"):
                            st.session_state[delete_key] = False
                            st.rerun()
                with col_delete_3:
                    if st.session_state[delete_key]:
                        if st.button("✅ Confirmer", key=f"confirm_{activity.id}", type="primary"):
                            if Activity.delete(activity.id):
                                st.success("Activité supprimée avec succès!")
                                st.session_state[delete_key] = False
                                st.rerun()
                            else:
                                st.error("Erreur lors de la suppression de l'activité")
                                st.session_state[delete_key] = False

if __name__ == "__main__":
    main()