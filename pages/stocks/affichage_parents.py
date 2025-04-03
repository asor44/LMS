from turtle import st

from models_deprecated import Inventory, EquipmentAssignment


def affichage_parents(user):
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