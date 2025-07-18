import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuración de la página ---
st.set_page_config(
    page_title="IMDb: Exploración Temporal",
    page_icon="images/IMDB_Logo_2016.png",
    layout="wide"
)

def load_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("style.css")

# Luego, el enlace a IMDb
st.sidebar.image("images/IMDB_Logo_2016.png", width=280) # Ajusta el 'width' según necesites
st.sidebar.markdown("¡Explora más en la [Página Oficial de IMDb](https://www.imdb.com/)!")

# --- Función para cargar los datos (con caché para eficiencia) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('data/imdb_dataset.csv', encoding='utf-8')
        # Asegúrate de que las columnas numéricas sean del tipo correcto
        df['startYear'] = pd.to_numeric(df['startYear'], errors='coerce')
        df['averageRating'] = pd.to_numeric(df['averageRating'], errors='coerce')
        df['numVotes'] = pd.to_numeric(df['numVotes'], errors='coerce')

        # Limpiar datos: eliminar filas con años, ratings o géneros nulos
        df.dropna(subset=['startYear', 'averageRating', 'genres'], inplace=True)
        # Convertir startYear a entero después de quitar NaNs
        df['startYear'] = df['startYear'].astype(int)

        return df
    except FileNotFoundError:
        st.error("Error: El archivo 'data/imdb_dataset.csv' no se encontró.")
        st.info("Asegúrate de que el archivo CSV esté en la carpeta principal de tu proyecto.")
        return pd.DataFrame()

# Cargar los datos
df_combined = load_data()

# --- Mapeo de nombres originales a nombres amigables para la interfaz ---
NAME_MAP = {
    "movie": "Películas",
    "tvSeries": "Series"
}

# --- Contenido de la Página de Exploración Temporal ---


if not df_combined.empty:
    # --- FILTROS DE LA PÁGINA PRINCIPAL (¡Movidos aquí!) ---
    st.header("Puntuación de Géneros por Año")
    st.markdown("Analiza cómo las calificaciones promedio de géneros específicos han evolucionado a lo largo de los años.")

    # Selectbox para Tipo de Título (Películas, Series, Todos)
    title_type_options_original = df_combined['titleType'].unique().tolist()
    title_type_display_options = ["Todos"] + [NAME_MAP.get(tt, tt) for tt in title_type_options_original]
    title_type_display_options.sort(key=lambda x: (
        0 if x == "Todos" else 1 if x == "Películas" else 2 if x == "Series" else 3
    ))

    selected_title_display_type = st.selectbox( # Ya no es st.sidebar.selectbox
        "Selecciona el tipo de título:",
        options=title_type_display_options,
        index=0,
        key='temporal_title_type_select'
    )

    # Filtrar el DataFrame según el tipo de título seleccionado
    if selected_title_display_type == "Todos":
        df_filtered_by_type = df_combined.copy()
        selected_title_internal_type = "Todos"
    else:
        selected_title_internal_type = ""
        for original, display in NAME_MAP.items():
            if display == selected_title_display_type:
                selected_title_internal_type = original
                break
        if not selected_title_internal_type:
            selected_title_internal_type = selected_title_display_type
        df_filtered_by_type = df_combined[df_combined['titleType'] == selected_title_internal_type].copy()

    # Multiselect para Géneros (Máximo 5)
    all_genres = df_filtered_by_type['genres'].dropna().str.split(',').explode().unique()
    all_genres_sorted = sorted(all_genres)

    selected_genres = st.multiselect( # Ya no es st.sidebar.multiselect
        'Selecciona hasta 5 géneros:',
        options=all_genres_sorted,
        default=all_genres_sorted[:min(3, len(all_genres_sorted))],
        max_selections=5,
        key='temporal_genre_multiselect'
    )

    # --- LÓGICA Y VISUALIZACIÓN DEL GRÁFICO DE LÍNEAS ---
    if selected_genres:
        df_plot = df_filtered_by_type[
            df_filtered_by_type['genres'].apply(
                lambda x: any(g in str(x).split(',') for g in selected_genres) if pd.notna(x) else False
            )
        ].copy()

        if not df_plot.empty:
            df_plot_exploded = df_plot.assign(genres=df_plot['genres'].str.split(',')).explode('genres')
            df_plot_exploded = df_plot_exploded[df_plot_exploded['genres'].isin(selected_genres)]

            genre_yearly_avg_rating = df_plot_exploded.groupby(['startYear', 'genres'])['averageRating'].mean().reset_index()
            genre_yearly_avg_rating.rename(columns={'genres': 'Género', 'averageRating': 'Calificación Promedio'}, inplace=True)

            genre_yearly_counts = df_plot_exploded.groupby(['startYear', 'genres']).size().reset_index(name='count')
            genre_yearly_counts.rename(columns={'genres': 'Género'}, inplace=True)

            genre_yearly_avg_rating = pd.merge(genre_yearly_avg_rating, genre_yearly_counts, on=['startYear', 'Género'], how='left')

            MIN_TITLES_FOR_AVERAGE = 10
            genre_yearly_avg_rating_filtered = genre_yearly_avg_rating[
                genre_yearly_avg_rating['count'] >= MIN_TITLES_FOR_AVERAGE
            ]

            if not genre_yearly_avg_rating_filtered.empty:
                fig = px.line(
                    genre_yearly_avg_rating_filtered,
                    x='startYear',
                    y='Calificación Promedio',
                    color='Género',
                    title=f'Calificación Promedio de Géneros Seleccionados ({selected_title_display_type}) por Año',
                    labels={
                        'startYear': 'Año de Lanzamiento',
                        'Calificación Promedio': 'Calificación Promedio IMDb'
                    },
                    hover_data={'count': True}
                )

                fig.update_layout(
                    xaxis_title="Año de Lanzamiento",
                    yaxis_title="Calificación Promedio IMDb",
                    hovermode="x unified",
                    legend_title_text='Géneros',
                    font=dict(size=12)
                )
                fig.update_yaxes(range=[1, 10])

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No hay suficientes datos (mínimo {MIN_TITLES_FOR_AVERAGE} títulos por año/género) para los géneros seleccionados en el rango de años para '{selected_title_display_type}'. Intenta seleccionar otros géneros.")
        else:
            st.warning("No se encontraron títulos con los géneros seleccionados para el tipo de título actual. Por favor, ajusta tus selecciones.")
    else:
        st.info("Por favor, selecciona al menos un género para ver el gráfico de líneas.")

    # --- NUEVO GRÁFICO DE LÍNEAS: COMPARACIÓN PELÍCULAS VS SERIES POR RANGO DE AÑOS ---
    st.markdown("---") # Un separador visual
    st.header("Puntuación Promedio Anual (Películas vs. Series)")
    st.markdown("Compara cómo han evolucionado las calificaciones promedio de películas y series a lo largo de los años en un rango de tiempo específico.")

    # Obtener el rango de años disponible en los datos
    min_year = int(df_combined['startYear'].min())
    max_year = int(df_combined['startYear'].max())

    # Contenedor para los selectores de año (para que aparezcan uno al lado del otro si hay espacio)
    col1, col2 = st.columns(2)

    with col1:
        start_year = st.selectbox(
            "Año de Inicio:",
            options=list(range(min_year, max_year + 1)),
            index=list(range(min_year, max_year + 1)).index(min_year), # Por defecto el año mínimo
            key='start_year_select'
        )
    with col2:
        end_year = st.selectbox(
            "Año de Término:",
            options=list(range(min_year, max_year + 1)),
            index=list(range(min_year, max_year + 1)).index(max_year), # Por defecto el año máximo
            key='end_year_select'
        )

    # Validación de años
    if start_year > end_year:
        st.warning("El Año de Inicio no puede ser posterior al Año de Término. Por favor, ajusta tu selección.")
    else:
        # Filtrar el DataFrame para el rango de años y solo para películas y series
        df_comparison_years = df_combined[
            (df_combined['startYear'] >= start_year) &
            (df_combined['startYear'] <= end_year) &
            (df_combined['titleType'].isin(['movie', 'tvSeries']))
        ].copy()

        if not df_comparison_years.empty:
            # Calcular la calificación promedio por año y tipo de título
            # También contamos el número de títulos para posibles filtros de datos escasos
            yearly_avg_comparison = df_comparison_years.groupby(['startYear', 'titleType'])['averageRating'].agg(
                ['mean', 'count']
            ).reset_index()
            yearly_avg_comparison.rename(columns={'mean': 'Calificación Promedio', 'titleType': 'Tipo de Título'}, inplace=True)

            # Mapear 'movie'/'tvSeries' a 'Películas'/'Series'
            yearly_avg_comparison['Tipo de Título'] = yearly_avg_comparison['Tipo de Título'].map(NAME_MAP)

            # Opcional: Filtrar años/tipos con pocos datos (ej. menos de 50 títulos)
            MIN_TITLES_COMPARISON = 50 # Puedes ajustar este umbral
            yearly_avg_comparison_filtered = yearly_avg_comparison[yearly_avg_comparison['count'] >= MIN_TITLES_COMPARISON]

            if not yearly_avg_comparison_filtered.empty:
                # Definir colores específicos
                colors = {
                    "Películas": "#31688B", # Azul
                    "Series": "#E34A33"     # Naranja/Rojo
                }

                # Crear el gráfico de líneas comparativo
                fig_comparison = px.line(
                    yearly_avg_comparison_filtered,
                    x='startYear',
                    y='Calificación Promedio',
                    color='Tipo de Título', # Una línea para Películas, otra para Series
                    title=f'Puntuación Promedio de Películas y Series del Año {start_year} al {end_year}',
                    labels={
                        'startYear': 'Año',
                        'Calificación Promedio': 'Calificación Promedio IMDb'
                    },
                    color_discrete_map=colors, # Aplicar los colores definidos
                    markers=True, # Mostrar puntos en cada dato (año)
                    hover_data={'count': True} # Mostrar el número de títulos en el tooltip
                )

                # Actualizar el diseño del gráfico
                fig_comparison.update_layout(
                    xaxis_title="Año",
                    yaxis_title="Calificación Promedio IMDb",
                    hovermode="x unified",
                    legend_title_text='Formato',
                    font=dict(size=12)
                )

                # Ajustar el rango del eje Y
                fig_comparison.update_yaxes(range=[1, 10])

                st.plotly_chart(fig_comparison, use_container_width=True)
            else:
                st.warning(f"No hay suficientes datos (mínimo {MIN_TITLES_COMPARISON} títulos por año/formato) para los años seleccionados ({start_year}-{end_year}). Ajusta tu rango de años o reduce el umbral de datos.")
        else:
            st.warning(f"No se encontraron datos de películas o series para el rango de años {start_year}-{end_year}. Por favor, ajusta los años seleccionados.")
else:
    st.error("No se pudieron cargar los datos. Por favor, verifica la ruta del archivo CSV y que no esté vacío.")
