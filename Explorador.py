import streamlit as st
import pandas as pd
import os

# --- Construcción segura de ruta para la imagen ---
image_path = os.path.join(os.path.dirname(__file__), "images", "IMDB_Logo_2016.png")

# --- Configuración de la página principal ---
st.set_page_config(
    page_title="Explorador General IMDb",
    page_icon=image_path,
    layout="wide"
)

# --- Función para cargar el CSS ---
def load_css(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, file_name)
    with open(file_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Cargar el archivo CSS ---
load_css("style.css")

# --- Imagen central ---
st.image(image_path, width=450)

# --- Título y descripción ---
st.title("Bienvenido al Explorador de IMDb")

st.header("¿Qué es IMDb?")
st.markdown("""
IMDb (Internet Movie Database) es una plataforma en línea que ofrece información detallada y actualizada sobre películas, series de televisión, actores, directores y otros profesionales del entretenimiento. Reconocida mundialmente, permite a los usuarios consultar sinopsis, reparto, calificaciones, tráilers, críticas y listas de popularidad, siendo una herramienta clave tanto para cinéfilos como para profesionales de la industria audiovisual.
""")

st.markdown("---")

# --- Propósito del Proyecto ---
st.markdown("""
### **Propósito del Proyecto**

En la era digital, donde la oferta de películas y series es abrumadora, tomar decisiones informadas sobre qué ver puede ser un desafío. 
Este dashboard interactivo nace con la **finalidad de resolver estas interrogantes**, transformando una vasta cantidad de datos de IMDb en **conocimiento accesible y visual**. Nuestro objetivo es proporcionar una herramienta intuitiva que permita a los usuarios:

* **Explorar tendencias históricas:** Observar la evolución de las calificaciones y la popularidad de géneros específicos a lo largo de las décadas.
* **Comparar formatos:** Entender las diferencias en la recepción crítica y del público entre películas y series en un vistazo.
* **Identificar lo más destacado:** Descubrir rápidamente los títulos mejor valorados o con mayor impacto.

En resumen, este proyecto busca **democratizar el análisis de datos cinematográficos**, ofreciendo una perspectiva clara y dinámica para que cualquier persona pueda navegar por el universo de IMDb con mayor facilidad y obtener ideas para sus próximas noches de entretenimiento.
""")

st.markdown("---")

st.markdown("""
#### **Para proceder a ver las visualizaciones, utiliza el menú lateral para navegar entre las diferentes secciones de análisis de datos de películas y series.**
Aquí podrás encontrar:
- **Visión General de Calificaciones:** Un vistazo a cómo se distribuyen las valoraciones.
- **Episodios de series:** Un vistazo a la cantidad de episodios y temporadas de las series junto a su calificación.
- **Tendencias Temporales:** Cómo han cambiado las cosas a lo largo de los años.
""")

# --- Imagen lateral ---
st.sidebar.image(image_path, width=280)

st.sidebar.markdown("¡Explora más en la [Página Oficial de IMDb](https://www.imdb.com/)!")
