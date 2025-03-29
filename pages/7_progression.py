import streamlit as st
from models import User, Badge, EvaluationType
from datetime import datetime, timedelta
import plotly.graph_objs as go

def check_authentication():
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("Veuillez vous connecter")
        st.stop()

def create_level_progress_chart(points, level):
    # Calculate points needed for next level
    points_for_current_level = (level * 10) ** 2
    points_for_next_level = ((level + 1) * 10) ** 2
    points_needed = points_for_next_level - points_for_current_level
    current_level_points = points - points_for_current_level
    progress = (current_level_points / points_needed) * 100

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=progress,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#2b86d9"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 100], 'color': 'lightgray'}
            ]
        },
        title={'text': f"Progression Niveau {level}", 'font': {'size': 24}}
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    return fig

def main():
    check_authentication()
    user = st.session_state.user

    st.title("🏆 Tableau de Progression")

    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Progression & Badges", "Notes & Appréciations", "Configuration Évaluations"])

    with tab1:
        # Get user points and level
        progress = user.get_points()
        points = progress["points"]
        level = progress["level"]

        # Display main stats in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Niveau", level)
        with col2:
            st.metric("Points Total", points)
        with col3:
            badges = user.get_badges()
            st.metric("Badges Gagnés", len(badges))

        # Show level progress chart
        st.plotly_chart(create_level_progress_chart(points, level))

        # Display badges
        st.subheader("🎖️ Mes Badges")
        badge_cols = st.columns(4)
        for idx, badge in enumerate(badges):
            with badge_cols[idx % 4]:
                st.markdown(f"""
                <div style='text-align: center; padding: 10px; margin: 5px; background-color: #f0f2f6; border-radius: 10px;'>
                    <h3>{badge.icon_name}</h3>
                    <p><strong>{badge.name}</strong></p>
                    <p><small>{badge.description}</small></p>
                </div>
                """, unsafe_allow_html=True)

        # Show available badges to unlock
        st.subheader("🎯 Badges à Débloquer")
        all_badges = Badge.get_all()
        unlocked_badge_ids = {b.id for b in badges}

        available_badges = [b for b in all_badges if b.id not in unlocked_badge_ids]
        if available_badges:
            badge_cols = st.columns(4)
            for idx, badge in enumerate(available_badges):
                with badge_cols[idx % 4]:
                    st.markdown(f"""
                    <div style='text-align: center; padding: 10px; margin: 5px; background-color: #f0f2f6; border-radius: 10px; opacity: 0.6;'>
                        <h3>❓</h3>
                        <p><strong>{badge.name}</strong></p>
                        <p><small>{badge.points_required} points requis</small></p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Félicitations ! Vous avez débloqué tous les badges disponibles !")

    with tab2:
        if user.status in ['administration', 'animateur']:
            # Interface pour ajouter/modifier des notes
            st.subheader("Ajouter une note")

            # Sélection du cadet/AMC
            cadets = User.get_all_by_status(['cadet', 'AMC'])
            selected_cadet = st.selectbox(
                "Sélectionner un cadet/AMC",
                cadets,
                format_func=lambda x: f"{x.name} ({x.status})"
            )

            if selected_cadet:
                with st.form("add_note"):
                    note_date = st.date_input("Date", value=datetime.now())
                    note_type = st.selectbox(
                        "Type d'évaluation",
                        ["Comportement", "Participation", "Leadership", "Technique", "Autre"]
                    )
                    rating = st.slider("Note", 1, 5, 3)
                    appreciation = st.text_area("Appréciation")

                    if st.form_submit_button("Enregistrer"):
                        try:
                            selected_cadet.add_note(
                                date=note_date,
                                note_type=note_type,
                                rating=rating,
                                appreciation=appreciation,
                                evaluator_id=user.id
                            )
                            st.success("Note enregistrée avec succès!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur lors de l'enregistrement: {str(e)}")

            # Affichage des notes existantes
            st.subheader("Notes existantes")
            date_filter = st.date_input(
                "Filtrer par date",
                value=(datetime.now() - timedelta(days=30), datetime.now())
            )

            if len(date_filter) == 2:
                start_date, end_date = date_filter
                notes = selected_cadet.get_notes(start_date, end_date)

                for note in notes:
                    with st.expander(f"{note['date'].strftime('%d/%m/%Y')} - {note['type']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Note:** {'⭐' * note['rating']}")
                            st.write(f"**Type:** {note['type']}")
                        with col2:
                            st.write(f"**Évaluateur:** {note['evaluator_name']}")
                            st.write(f"**Date:** {note['date'].strftime('%d/%m/%Y')}")
                        st.write("**Appréciation:**")
                        st.write(note['appreciation'])

                        if user.id == note['evaluator_id']:
                            if st.button("Supprimer", key=f"delete_note_{note['id']}"):
                                if selected_cadet.delete_note(note['id']):
                                    st.success("Note supprimée!")
                                    st.rerun()

        elif user.status in ['cadet', 'AMC']:
            # Interface pour voir ses propres notes
            st.subheader("Mes notes")
            date_filter = st.date_input(
                "Filtrer par date",
                value=(datetime.now() - timedelta(days=30), datetime.now())
            )

            if len(date_filter) == 2:
                start_date, end_date = date_filter
                notes = user.get_notes(start_date, end_date)

                for note in notes:
                    with st.expander(f"{note['date'].strftime('%d/%m/%Y')} - {note['type']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Note:** {'⭐' * note['rating']}")
                            st.write(f"**Type:** {note['type']}")
                        with col2:
                            st.write(f"**Évaluateur:** {note['evaluator_name']}")
                            st.write(f"**Date:** {note['date'].strftime('%d/%m/%Y')}")
                        st.write("**Appréciation:**")
                        st.write(note['appreciation'])

        elif user.status == 'parent':
            # Interface pour voir les notes de ses enfants
            st.subheader("Notes de vos enfants")
            children = user.get_children()

            if children:
                selected_child = st.selectbox(
                    "Sélectionner un enfant",
                    children,
                    format_func=lambda x: x.name
                )

                date_filter = st.date_input(
                    "Filtrer par date",
                    value=(datetime.now() - timedelta(days=30), datetime.now())
                )

                if len(date_filter) == 2:
                    start_date, end_date = date_filter
                    notes = selected_child.get_notes(start_date, end_date)

                    for note in notes:
                        with st.expander(f"{note['date'].strftime('%d/%m/%Y')} - {note['type']}"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Note:** {'⭐' * note['rating']}")
                                st.write(f"**Type:** {note['type']}")
                            with col2:
                                st.write(f"**Évaluateur:** {note['evaluator_name']}")
                                st.write(f"**Date:** {note['date'].strftime('%d/%m/%Y')}")
                            st.write("**Appréciation:**")
                            st.write(note['appreciation'])
            else:
                st.warning("Aucun enfant associé à votre compte")

    # Add some test badges if none exist
    if not all_badges:
        with st.expander("Administration - Ajouter des badges de test"):
            if st.button("Créer des badges de test"):
                test_badges = [
                    ("Première Présence", "Participez à votre première activité", "🌟", 10),
                    ("Expert", "Atteignez 100 points", "🏅", 100),
                    ("Super Participant", "Participez à 10 activités", "🌈", 200),
                    ("Maître", "Atteignez le niveau 5", "👑", 500),
                ]
                for name, desc, icon, points in test_badges:
                    Badge.create(name, desc, icon, points)
                st.success("Badges de test créés !")
                st.rerun()

    with tab3:
        if user.status == 'administration':
            st.subheader("Gestion des Types d'Évaluation")

            # Liste des types existants
            eval_types = EvaluationType.get_all(active_only=False)
            if eval_types:
                st.write("Types d'évaluation existants:")
                for eval_type in eval_types:
                    with st.expander(f"{eval_type.name} {'(Inactif)' if not eval_type.active else ''}"):
                        with st.form(f"edit_type_{eval_type.id}"):
                            new_name = st.text_input("Nom", eval_type.name)
                            new_min = st.number_input("Note minimale", 1, 10, eval_type.min_rating)
                            new_max = st.number_input("Note maximale", new_min, 10, eval_type.max_rating)
                            new_desc = st.text_area("Description", eval_type.description or "")
                            new_active = st.checkbox("Actif", eval_type.active)

                            col1, col2 = st.columns(2)
                            with col1:
                                if st.form_submit_button("Mettre à jour"):
                                    try:
                                        eval_type.update(
                                            name=new_name,
                                            min_rating=new_min,
                                            max_rating=new_max,
                                            description=new_desc,
                                            active=new_active
                                        )
                                        st.success("Type d'évaluation mis à jour!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erreur: {str(e)}")

            # Formulaire pour ajouter un nouveau type
            st.divider()
            st.subheader("Ajouter un nouveau type d'évaluation")
            with st.form("new_eval_type"):
                name = st.text_input("Nom")
                min_rating = st.number_input("Note minimale", 1, 10, 1)
                max_rating = st.number_input("Note maximale", min_rating, 10, 5)
                description = st.text_area("Description")

                if st.form_submit_button("Créer"):
                    try:
                        EvaluationType.create(name, min_rating, max_rating, description)
                        st.success("Type d'évaluation créé!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur: {str(e)}")
        else:
            st.warning("Vous n'avez pas les permissions nécessaires pour accéder à cette section.")

if __name__ == "__main__":
    main()