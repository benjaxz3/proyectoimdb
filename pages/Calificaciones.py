# pages/01_Calificaciones.py
import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuración de la página ---
st.set_page_config(
    page_title="IMDb: Calificaciones y Títulos Destacados",
    page_icon="images/IMDB_Logo_2016.png", # Asegúrate de que la ruta de la imagen sea correcta
    layout="wide"
)

# --- Sidebar ---
def load_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("style.css")
st.sidebar.image("images/IMDB_Logo_2016.png", width=280)
st.sidebar.markdown("¡Explora más en la [Página Oficial de IMDb](https://www.imdb.com/)!")

# --- Función para cargar los datos (con caché para eficiencia) ---
@st.cache_data
def load_data():
    try:
        # Asumiendo que 'imdb_movies_and_series_combined.csv' es tu archivo combinado
        df = pd.read_csv('data/imdb_dataset.csv', encoding='utf-8')
        
        # Convertir tipos de datos y manejar errores
        df['startYear'] = pd.to_numeric(df['startYear'], errors='coerce')
        df['runtimeMinutes'] = pd.to_numeric(df['runtimeMinutes'], errors='coerce')
        df['averageRating'] = pd.to_numeric(df['averageRating'], errors='coerce')
        df['numVotes'] = pd.to_numeric(df['numVotes'], errors='coerce')
        
        # Eliminar filas con valores NaN importantes para las visualizaciones
        df.dropna(subset=['startYear', 'averageRating', 'genres'], inplace=True)
        
        # Convertir a entero después de limpiar NaN
        df['startYear'] = df['startYear'].astype(int)

        return df
    except FileNotFoundError:
        st.error("Error: El archivo 'imdb_movies_and_series_combined.csv' no se encontró.")
        st.info("Asegúrate de que tu archivo CSV combinado esté en la misma carpeta que tus scripts de Streamlit, o ajusta la ruta.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Ocurrió un error al cargar o procesar los datos: {e}")
        st.info("Verifica el formato del archivo y los nombres de las columnas.")
        return pd.DataFrame()

# Cargar los datos
df_combined = load_data()

# --- Mapeo de nombres originales a nombres amigables para la interfaz ---
NAME_MAP = {
    "movie": "Películas",
    "tvSeries": "Series"
}

# --- Mapeo de colores personalizados estilo IMDb ---
COLOR_MAP_HIST = {
    "Todos": "#F5C518",  # Amarillo IMDb
    "Películas": "#31688B", # Azul oscuro
    "Series": "#E34A33"     # Naranja/Rojo
}
COLOR_MAP_TOP = {
    "Películas": "#31688B",
    "Series": "#E34A33"
}

# --- Contenido de la Página Principal ---
st.title("Calificaciones y Títulos Destacados en IMDb")
st.markdown("Explora la distribución general de calificaciones, la composición de géneros por rango de calificación y descubre los títulos mejor puntuados.")



if not df_combined.empty:
    # --- SECCIÓN 1: HISTOGRAMA DE CALIFICACIONES ---
    st.header("Distribución de Calificaciones")
    st.markdown("Observa cómo se distribuyen las calificaciones promedio de los títulos.")

    # Widget Selectbox para filtrar el HISTOGRAMA
    hist_title_types_original = df_combined['titleType'].dropna().unique().tolist()
    hist_display_title_types = ["Todos"] + [NAME_MAP.get(tt, tt) for tt in hist_title_types_original if tt in NAME_MAP]
    hist_display_title_types.sort(key=lambda x: (
        0 if x == "Todos" else 1 if x == "Películas" else 2 if x == "Series" else 3
    ))

    selected_hist_display_type = st.selectbox(
        "Selecciona el tipo de título para el histograma:",
        options=hist_display_title_types,
        index=0,
        key='hist_selectbox'
    )

    selected_hist_internal_type = ""
    if selected_hist_display_type == "Todos":
        selected_hist_internal_type = "Todos"
    else:
        inverted_name_map = {v: k for k, v in NAME_MAP.items()}
        selected_hist_internal_type = inverted_name_map.get(selected_hist_display_type, selected_hist_display_type)

    df_hist_filtered = df_combined.copy()
    if selected_hist_internal_type != "Todos":
        df_hist_filtered = df_hist_filtered[df_hist_filtered['titleType'] == selected_hist_internal_type]

    if not df_hist_filtered.empty:
        current_hist_color = COLOR_MAP_HIST.get(selected_hist_display_type, "#6A5ACD")

        fig_hist = px.histogram(
            df_hist_filtered,
            x='averageRating',
            nbins=20,
            title=f'Histograma de Calificaciones Promedio de {selected_hist_display_type}',
            labels={'averageRating': 'Calificación Promedio', 'count': 'Número de Títulos'},
            color_discrete_sequence=[current_hist_color]
        )
        fig_hist.update_layout(xaxis_title="Calificación Promedio", yaxis_title="Número de Títulos", bargap=0.05)
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.warning(f"No hay datos para generar el histograma para '{selected_hist_display_type}'.")


    st.markdown("---") # Un separador visual
    # --- SECCIÓN 2: GRÁFICO DE TORTA DE GÉNEROS POR RANGO DE CALIFICACIÓN ---
    st.header("Composición de Géneros por Rango de Calificación")
    st.markdown("Selecciona un rango de calificación y **entre 3 y 5 géneros** para ver su proporción dentro de ese segmento de títulos. Esto ayuda a entender qué géneros son populares en diferentes rangos de puntuación.")

    # --- Selectbox para Rangos de Puntuación ---
    rating_ranges = [
        "1.0 - 2.0", "2.1 - 3.0", "3.1 - 4.0", "4.1 - 5.0",
        "5.1 - 6.0", "6.1 - 7.0", "7.1 - 8.0", "8.1 - 9.0", "9.1 - 10.0"
    ]
    selected_rating_range = st.selectbox(
        "Selecciona un rango de calificación:",
        options=rating_ranges,
        index=6, # Por defecto, selecciona "7.1 - 8.0"
        key='pie_rating_range_selectbox'
    )

    # Parsear el rango seleccionado
    min_rating, max_rating = map(float, selected_rating_range.split(' - '))

    # Filtrar el DataFrame por el rango de calificación
    df_filtered_by_rating_range = df_combined[
        (df_combined['averageRating'] >= min_rating) &
        (df_combined['averageRating'] <= max_rating) &
        (df_combined['genres'].notna()) # Asegurarse de que tienen géneros
    ].copy()

    # Obtener todos los géneros únicos para el multiselect (basado en el DataFrame filtrado por rango)
    all_genres_in_range = df_filtered_by_rating_range['genres'].dropna().str.split(',').explode().unique()
    all_genres_in_range_sorted = sorted(all_genres_in_range)

    # --- Lógica de selección de géneros para el gráfico de torta (sin min_selections/max_selections) ---
    # Sugerir un default que se ajuste al límite, pero sin forzarlo directamente en el widget
    default_genres_for_pie = []
    if len(all_genres_in_range_sorted) >= 3:
        default_genres_for_pie = all_genres_in_range_sorted[:min(5, len(all_genres_in_range_sorted))]


    selected_pie_genres = st.multiselect(
        '**Selecciona entre 3 y 5 géneros** para el gráfico de torta:',
        options=all_genres_in_range_sorted,
        default=default_genres_for_pie, # Usar el default calculado
        key='pie_multiselect'
    )

    # --- Lógica condicional para mostrar el gráfico o advertencias (validación manual) ---
    if not df_filtered_by_rating_range.empty:
        if 3 <= len(selected_pie_genres) <= 5: # Validar el rango de selección aquí
            # Contar la frecuencia de los géneros seleccionados dentro del rango de calificación
            genre_counts_for_pie = df_filtered_by_rating_range['genres'].dropna().str.split(',').explode()
            genre_counts_for_pie = genre_counts_for_pie[genre_counts_for_pie.isin(selected_pie_genres)].value_counts()

            if not genre_counts_for_pie.empty:
                df_pie_chart_data = genre_counts_for_pie.reset_index()
                df_pie_chart_data.columns = ['Genre', 'Count']

                fig_pie = px.pie(
                    df_pie_chart_data,
                    values='Count',
                    names='Genre',
                    title=f'Proporción de Géneros Seleccionados para Calificaciones {selected_rating_range}',
                    hole=0.3, # Crea un gráfico de dona
                    color_discrete_sequence=px.colors.sequential.Plotly3
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.warning("No hay títulos con los géneros seleccionados en este rango de calificación. Intenta elegir otros géneros o un rango diferente.")
        elif len(selected_pie_genres) < 3:
            st.info("Por favor, selecciona **al menos 3 géneros** para el gráfico de torta.")
        elif len(selected_pie_genres) > 5:
            st.info("Has seleccionado más de 5 géneros. Por favor, selecciona **un máximo de 5 géneros** para el gráfico de torta.")
    else:
        st.warning(f"No hay títulos en el rango de calificación '{selected_rating_range}'. Intenta seleccionar un rango diferente.")


    st.markdown("---") # Un separador visual
    # --- SECCIÓN 3: TOP 30 TÍTULOS MEJOR PUNTUADOS ---
    st.header("Top 30 Títulos Mejor Puntuados")
    st.markdown("Descubre las 30 películas o series con las calificaciones más altas, filtradas por un mínimo de votos para asegurar relevancia y evitar títulos con pocas valoraciones.")

    # Widget Selectbox para el TOP 30
    top_selection_options = ["Películas", "Series"]
    selected_top_display_type = st.selectbox(
        "Selecciona el tipo de título para el Top 30:",
        options=top_selection_options,
        index=0,
        key='top_selectbox'
    )

    # Convertir selección amigable a nombre interno para el TOP 30
    inverted_name_map_top = {v: k for k, v in NAME_MAP.items()}
    selected_top_internal_type = inverted_name_map_top.get(selected_top_display_type, selected_top_display_type)

    # Widget Slider para el Mínimo de Votos en el TOP 30
    min_votes_threshold = st.slider(
        f"Mínimo de votos para ser incluido en el Top 30 de {selected_top_display_type}:",
        min_value=100,
        max_value=250000,
        value=5000,
        step=100,
        key=f'votes_slider_top_{selected_top_display_type}'
    )

    # Filtrar y ordenar el DataFrame para el TOP 30
    df_for_top = df_combined[df_combined['titleType'] == selected_top_internal_type].copy()
    df_filtered_by_votes_top = df_for_top[df_for_top['numVotes'] >= min_votes_threshold]

    df_top_30 = df_filtered_by_votes_top.sort_values(
        by=['averageRating', 'numVotes'],
        ascending=[False, False]
    ).head(30)

    # --- Mostrar el Gráfico de Barras del Top 30 ---
    if not df_top_30.empty:
        current_top_color = COLOR_MAP_TOP.get(selected_top_display_type, "#6A5ACD")

        fig_top30 = px.bar(
            df_top_30.sort_values(by='averageRating', ascending=True),
            x='averageRating',
            y='primaryTitle',
            orientation='h',
            title=f'Top 30 {selected_top_display_type} Mejor Puntuadas (Mín. {min_votes_threshold:,} votos)',
            labels={
                'primaryTitle': 'Título',
                'averageRating': 'Calificación Promedio'
            },
            color_discrete_sequence=[current_top_color],
            hover_data={'startYear': True, 'genres': True, 'numVotes': ':,d'}
        )

        fig_top30.update_layout(
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="Calificación Promedio",
            yaxis_title="Título",
            height=900
        )

        st.plotly_chart(fig_top30, use_container_width=True)
    else:
        st.warning(f"No se encontraron {selected_top_display_type.lower()} en el Top 30 con los criterios seleccionados (mínimo {min_votes_threshold:,} votos). Intenta reducir el umbral de votos o selecciona un tipo de título diferente.")
else:
    st.error("No se pudieron cargar los datos. Por favor, verifica la ruta del archivo CSV 'imdb_movies_and_series_combined.csv' y que no esté vacío.")
