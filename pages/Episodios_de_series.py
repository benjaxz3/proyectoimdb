# pages/03_Episodios_por_Temporada.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

data_path = os.path.join(os.path.dirname(__file__), "..", "data")
im1 = pd.read_csv(os.path.join(data_path, "imdb_episodios_parte1.csv"))
im2 = pd.read_csv(os.path.join(data_path, "imdb_episodios_parte2.csv"))
im3 = pd.read_csv(os.path.join(data_path, "imdb_episodios_parte3.csv"))
im4 = pd.read_csv(os.path.join(data_path, "imdb_episodios_parte4.csv"))
im5 = pd.read_csv(os.path.join(data_path, "imdb_episodios_parte5.csv"))
# Unir todos los DataFrames en uno solo
imdb_episodios = pd.concat([im1, im2, im3, im4, im5], ignore_index=True)

ep1 = pd.read_csv(os.path.join(data_path, "title_parte1.tsv"))
ep2 = pd.read_csv(os.path.join(data_path, "title_parte2.tsv"))
ep3 = pd.read_csv(os.path.join(data_path, "title_parte3.tsv"))
# Unir todos los DataFrames en uno solo
title_episode = pd.concat([ep1, ep2, ep3], ignore_index=True)

# --- Configuración de la página ---
st.set_page_config(
    page_title="IMDb: Episodios por Temporada",
    page_icon="images/IMDB_Logo_2016.png", 
    layout="wide"
)

# --- Sidebar ---
def load_css(file_name):
    try:
        with open(file_name, encoding="utf-8") as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.sidebar.warning(f"Archivo CSS '{file_name}' no encontrado. No se aplicará estilo personalizado.")

load_css("style.css") 
st.sidebar.image("images/IMDB_Logo_2016.png", width=280) 
st.sidebar.markdown("---")
st.sidebar.markdown("¡Explora más en la [Página Oficial de IMDb](https://www.imdb.com/)!")
st.sidebar.markdown("---")


# --- Funciones de Carga de Datos ---
@st.cache_data
def load_main_data():
    try:
        # Cargar dataset principal
        df_combined = pd.read_csv('data/imdb_dataset.csv', encoding='utf-8')

        # Usar directamente el DataFrame 
        df_episodes_raw = title_episode.copy()
        df_episodes_raw.replace('\\N', pd.NA, inplace=True)

        # Procesar columnas del dataset principal
        df_combined['startYear'] = pd.to_numeric(df_combined['startYear'], errors='coerce')
        df_combined['averageRating'] = pd.to_numeric(df_combined['averageRating'], errors='coerce')
        df_combined['numVotes'] = pd.to_numeric(df_combined['numVotes'], errors='coerce')
        df_combined['runtimeMinutes'] = pd.to_numeric(df_combined['runtimeMinutes'], errors='coerce')
        df_combined.dropna(subset=['startYear', 'averageRating', 'genres'], inplace=True)
        df_combined['startYear'] = df_combined['startYear'].astype(int)

        # Procesar columnas del episodio TSV
        df_episodes_raw.rename(columns={
            'tconst': 'episodeTconst',
            'parentTconst': 'tconst_parent_series',
            'seasonNumber': 'seasonNumber',
            'episodeNumber': 'episodeNumber'
        }, inplace=True)

        df_episodes_raw['seasonNumber'] = pd.to_numeric(df_episodes_raw['seasonNumber'], errors='coerce')
        df_episodes_raw['episodeNumber'] = pd.to_numeric(df_episodes_raw['episodeNumber'], errors='coerce')
        df_episodes_raw.dropna(subset=['tconst_parent_series', 'seasonNumber', 'episodeNumber'], inplace=True)
        df_episodes_raw['seasonNumber'] = df_episodes_raw['seasonNumber'].astype(int)
        df_episodes_raw['episodeNumber'] = df_episodes_raw['episodeNumber'].astype(int)

        # Fusionar ambos DataFrames
        df_final_combined = pd.merge(
            df_combined,
            df_episodes_raw[['tconst_parent_series', 'episodeTconst', 'seasonNumber', 'episodeNumber']],
            left_on='tconst',
            right_on='tconst_parent_series',
            how='left'
        )

        df_final_combined.drop(columns=['tconst_parent_series'], inplace=True)
        return df_final_combined

    except FileNotFoundError as e:
        st.error(f"Error al cargar archivos CSV/TSV: {e}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        return pd.DataFrame()

@st.cache_data
def load_episode_ratings_data():
    try:
        return imdb_episodios.copy()
    except Exception as e:
        st.error(f"Ocurrió un error al procesar los datos de calificaciones de episodios: {e}")
        return pd.DataFrame()

# Cargar los datos para ambos gráficos
df_main = load_main_data()
imdb_episodios = load_episode_ratings_data()

# --- Contenido de la Página de Episodios por Temporada ---
st.title("Análisis Detallado de Series y Episodios")
st.markdown("Explora la estructura de temporadas y la evolución de las calificaciones de episodios.")

# --- Lógica para el SELECTBOX ÚNICO de Serie ---
if not df_main.empty and not imdb_episodios.empty:
    # 1. Obtener series con episodios para el gráfico de CONTEO
    series_for_count_chart = df_main[
        (df_main['titleType'] == 'tvSeries') &
        (df_main['episodeTconst'].notna())
    ].drop_duplicates(subset=['tconst'])

    # 2. Obtener series con calificaciones de episodios para el gráfico de RATINGS
    series_for_ratings_chart = imdb_episodios.drop_duplicates(subset=['series_primaryTitle'])

    # Nos aseguramos que 'primaryTitle' y 'series_primaryTitle' se puedan comparar
    series_for_count_chart_renamed = series_for_count_chart.rename(columns={'primaryTitle': 'series_primaryTitle_main_df'}).copy()

    # Fusionar para encontrar series comunes que estén en ambos sets de datos
    common_series_df = pd.merge(
        series_for_count_chart_renamed,
        series_for_ratings_chart,
        left_on='series_primaryTitle_main_df',
        right_on='series_primaryTitle',
        how='inner' # Solo series que tienen datos completos para AMBOS gráficos
    )

    if not common_series_df.empty:
        # Extraer los títulos de las series comunes
        sorted_common_series_titles = sorted(common_series_df['series_primaryTitle'].unique())

        selected_series_title = st.selectbox(
            "**Selecciona una Serie:**",
            options=sorted_common_series_titles,
            index=sorted_common_series_titles.index("Game of Thrones") if "Game of Thrones" in sorted_common_series_titles else (
                  sorted_common_series_titles.index("Breaking Bad") if "Breaking Bad" in sorted_common_series_titles else 0
            ),
            key='unified_series_selector'
        )

        if selected_series_title:
            # Obtener el tconst de la serie seleccionada para df_main
            selected_series_tconst_main = series_for_count_chart[
                series_for_count_chart['primaryTitle'] == selected_series_title
            ]['tconst'].iloc[0]

            # Información general de la serie (rating, votos)
            series_info = series_for_count_chart[series_for_count_chart['primaryTitle'] == selected_series_title].iloc[0]
            series_rating = series_info['averageRating']
            series_num_votes = series_info['numVotes']
            st.markdown(f"**Calificación Promedio de la Serie:** {series_rating:.1f} ⭐ (Basado en {series_num_votes:,} votos)")

            # --- SECCIÓN 1: Cantidad de Episodios por Temporada ---
            st.markdown("---")
            st.header("Cantidad de Episodios por Temporada")

            episodes_data_for_count_chart = df_main[
                (df_main['tconst'] == selected_series_tconst_main) &
                (df_main['episodeTconst'].notna()) &
                (df_main['runtimeMinutes'].notna())
            ].copy()

            if not episodes_data_for_count_chart.empty:
                episodes_per_season = episodes_data_for_count_chart.groupby('seasonNumber').size().reset_index(name='Cantidad de Episodios')
                episodes_per_season.rename(columns={'seasonNumber': 'Temporada'}, inplace=True)
                episodes_per_season['Temporada'] = episodes_per_season['Temporada'].astype(str)

                fig_episodes_per_season = px.bar(
                    episodes_per_season,
                    x='Temporada',
                    y='Cantidad de Episodios',
                    title=f'Cantidad de Episodios por Temporada de "{selected_series_title}"',
                    labels={'Temporada': 'Temporada', 'Cantidad de Episodios': 'Cantidad de Episodios'},
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )

                fig_episodes_per_season.update_layout(
                    xaxis_title="Temporada",
                    yaxis_title="Cantidad de Episodios",
                    hovermode="x unified",
                    font=dict(size=12)
                )

                st.plotly_chart(fig_episodes_per_season, use_container_width=True)
            else:
                st.info(f"No se encontraron datos de episodios por temporada para la serie '{selected_series_title}'.")


            # --- SECCIÓN 2: Calificaciones de Episodios por Temporada ---
            st.markdown("---")
            st.header("Calificaciones de Episodios por Temporada")

            df_selected_series_ratings_filtered = imdb_episodios[
                imdb_episodios['series_primaryTitle'] == selected_series_title
            ].copy()

            if not df_selected_series_ratings_filtered.empty:
                season_numbers_ratings = sorted(df_selected_series_ratings_filtered['seasonNumber'].unique().tolist())
                selected_season_ratings = st.selectbox(
                    f"Selecciona una Temporada para {selected_series_title} (Calificaciones):",
                    season_numbers_ratings,
                    index=0,
                    key='select_season_for_ratings_chart' # Clave única
                )

                df_selected_season_ratings = df_selected_series_ratings_filtered[
                    df_selected_series_ratings_filtered['seasonNumber'] == selected_season_ratings
                ].copy()

                df_selected_season_ratings['episodeNumber'] = pd.to_numeric(df_selected_season_ratings['episodeNumber'], errors='coerce')
                df_selected_season_ratings['episode_averageRating'] = pd.to_numeric(df_selected_season_ratings['episode_averageRating'], errors='coerce')

                df_selected_season_ratings.dropna(subset=['episodeNumber', 'episode_averageRating'], inplace=True)
                df_selected_season_ratings.sort_values(by='episodeNumber', inplace=True)
                df_selected_season_ratings.reset_index(drop=True, inplace=True)

                if not df_selected_season_ratings.empty:

                    def get_rating_category(rating):
                        if rating >= 7.0: return 'Alto'
                        elif 4.0 <= rating <= 6.9: return 'Normal'
                        else: return 'Bajo'

                    df_selected_season_ratings['rating_category'] = df_selected_season_ratings['episode_averageRating'].apply(get_rating_category)

                    category_colors = {
                        'Alto': '#2CA02C',   # Verde
                        'Normal': '#FF7F0E', # Naranja
                        'Bajo': '#D62728'    # Rojo
                    }

                    fig_ratings = go.Figure()

                    marker_colors = []
                    if len(df_selected_season_ratings) > 0:
                        # Usar .item() para extraer el valor de una Serie de un solo elemento
                        marker_colors.append(category_colors.get(df_selected_season_ratings.iloc[0]['rating_category'], 'grey'))

                    for i in range(1, len(df_selected_season_ratings)):
                        episode_prev = df_selected_season_ratings.iloc[i-1]
                        episode_curr = df_selected_season_ratings.iloc[i]

                        # Usar .item() para extraer el valor de una Serie de un solo elemento
                        segment_color = category_colors.get(episode_curr['rating_category'], 'grey')
                        marker_colors.append(segment_color)

                        fig_ratings.add_trace(go.Scatter(
                            x=[episode_prev['episodeNumber'], episode_curr['episodeNumber']],
                            y=[episode_prev['episode_averageRating'], episode_curr['episode_averageRating']],
                            mode='lines',
                            line=dict(color=segment_color, width=2.5),
                            showlegend=False,
                            hoverinfo='skip'
                        ))

                    fig_ratings.add_trace(go.Scatter(
                        x=df_selected_season_ratings['episodeNumber'],
                        y=df_selected_season_ratings['episode_averageRating'],
                        mode='markers',
                        marker=dict(
                            size=10,
                            color=marker_colors,
                            line=dict(width=0.5, color='DarkSlateGrey')
                        ),
                        name='Calificación de Episodios',
                        hoverinfo='text',
                        hovertext=[
                            f"Episodio: {row['episodeNumber']}<br>"
                            f"Calificación: {row['episode_averageRating']:.1f} ({row['rating_category']})<br>"
                            f"Votos: {row['episode_numVotes']:,}"
                            for index, row in df_selected_season_ratings.iterrows()
                        ]
                    ))

                    fig_ratings.update_layout(
                        title_text=f'Calificaciones de Episodios - {selected_series_title} Temporada {selected_season_ratings}',
                        xaxis_title='Número de Episodio',
                        yaxis_title='Calificación Promedio (1-10)',
                        yaxis_range=[0, 10],
                        yaxis_dtick=1,
                        xaxis_dtick=1,
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='DarkSlateGrey'),
                        xaxis=dict(showgrid=False, zeroline=False),
                        yaxis=dict(showgrid=True, gridcolor='LightGrey', zeroline=False),
                        title_font_size=20,
                        hoverlabel=dict(bgcolor='rgba(46, 52, 64, 0.8)', font_size=13, font_family="Arial", bordercolor='grey', font=dict(color='white'))
                    )

                    st.plotly_chart(fig_ratings, use_container_width=True)

                    st.markdown(
                        """
                        <p style='font-size: small; color: grey;'>
                        Este gráfico muestra la calificación de cada episodio dentro de la temporada seleccionada.<br>
                        La línea y los puntos se colorean según el rango de rating del episodio:
                        <span style='color:#2CA02C; font-weight:bold;'>Verde para 'Alto' (7.0-10)</span>,
                        <span style='color:#FF7F0E; font-weight:bold;'>Naranja para 'Normal' (4.0-6.9)</span>, y
                        <span style='color:#D62728; font-weight:bold;'>Rojo para 'Bajo' (1.0-3.9)</span>.
                        </p>
                        """,
                        unsafe_allow_html=True
                    )

                else:
                    st.info(f"No se encontraron episodios con calificaciones para la **Temporada {selected_season_ratings}** de **{selected_series_title}**.")
            else:
                st.warning(f"No se encontraron datos de episodios con calificaciones para la serie '{selected_series_title}'.")

        else: 
            st.info("Por favor, selecciona una serie para ver sus datos de episodios.")

    else:
        st.warning("No se encontraron series con datos completos (conteo y calificaciones de episodios) para esta visualización. Asegúrate de que ambos DataFrames tengan datos de series coincidentes.")

else:
    st.error("No se pudieron cargar los DataFrames necesarios para la visualización. Verifica las rutas de los archivos CSV/TSV y sus contenidos.")
