import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuración de página
st.set_page_config(page_title="Gestor de Gastos Inteligente", layout="wide")

# Lista de categorías maestras para validación y recategorización
CATEGORIAS_MAESTRAS = [
    'Supermercados', 'Restaurantes & Delivery', 'Transporte & Auto', 
    'Salud & Bienestar', 'Hogar & Servicios', 'Viajes & Ocio', 
    'Compras & Tech', 'Transferencias & Otros'
]

# ==================== FUNCIONES DE PROCESAMIENTO ====================

def aplicar_inteligencia_categorizacion(df):
    """Aplica las reglas de unificación de comercios y categorías"""
    # Unificación de comercios
    reglas_agrupacion = {
        'WONG': 'Wong', 'UBER': 'Uber', 'RAPPI': 'Rappi', 'PLIN': 'Plin',
        'APPLE': 'Apple', 'FRISKA': 'Friska', 'SMART FIT': 'Smart Fit',
        'PACIFICO': 'Pacifico Seguros', 'MASS': 'Tiendas Mass', 'OXXO': 'Oxxo',
        'ALIEXPRESS': 'AliExpress', 'AMAZON': 'Amazon', 'LATAM': 'Latam Airlines',
        'VENDOMATICA': 'Vendomática', 'CINEPLANET': 'Cineplanet', 'SODIMAC': 'Sodimac',
        'MAESTRO': 'Maestro'
    }

    df['Comercio'] = df['Descripcion']
    for clave, nombre_limpio in reglas_agrupacion.items():
        mask = df['Comercio'].str.contains(clave, case=False, na=False)
        df.loc[mask, 'Comercio'] = nombre_limpio

    # Reglas de categorías simplificadas
    reglas_simplificadas = {
        'Supermercados': ['wong', 'metro', 'tottus', 'mass', 'oxxo', 'tambo', 'market', 'bodega', 'jumbo', 'carrefour', 'listo'],
        'Restaurantes & Delivery': ['rappi', 'pedidosya', 'dominos', 'restaurante', 'cafe', 'caffe', 'starbucks', 'kfc', 'mcdonalds', 'subway', 'pizzeria', 'chifa', 'bife', 'sushi'],
        'Transporte & Auto': ['uber', 'cabify', 'taxi', 'e s ', 'grifo', 'rutas de lima', 'peaje', 'estacion', 'servicentro', 'parking', 'apparka'],
        'Salud & Bienestar': ['farmacia', 'clinica', 'pacifico', 'smart fit', 'smartfit', 'dent', 'fisio', 'spa', 'montalvo', 'botica', 'hospital'],
        'Hogar & Servicios': ['sodimac', 'maestro', 'promart', 'dh lurin', 'movistar', 'claro', 'enel', 'sedapal', 'calidda'],
        'Viajes & Ocio': ['airbnb', 'booking', 'latam', 'hotel', 'cineplanet', 'spotify', 'youtube', 'turismo', 'duty free', 'despegar', 'avianca'],
        'Compras & Tech': ['apple', 'aliexpress', 'amazon', 'ebay', 'dji', 'h&m', 'zara', 'miniso', 'tai loy', 'falabella', 'ripley', 'adidas', 'puma', 'levis'],
        'Transferencias & Otros': ['plin-', 'yape', 'cargo da ']
    }

    df['Categoria_Final'] = 'Transferencias & Otros'
    for nueva_cat, palabras in reglas_simplificadas.items():
        patron = '|'.join(palabras)
        mask = df['Descripcion'].str.contains(patron, case=False, na=False)
        df.loc[mask, 'Categoria_Final'] = nueva_cat
    
    # Respetar categorías manuales si ya son parte de las maestras
    if 'Categoria' in df.columns:
        mask_manual = df['Categoria'].isin(CATEGORIAS_MAESTRAS)
        df.loc[mask_manual, 'Categoria_Final'] = df['Categoria']

    return df

def procesar_archivo(file, is_excel=False):
    try:
        if is_excel:
            df = pd.read_excel(file)
        else:
            df = pd.read_csv(file, encoding='latin1', sep=',', quoting=3)
        
        # Limpieza básica
        df.columns = df.columns.str.replace('"', '').str.strip()
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace('"', '', regex=False)
        
        # Validar columnas necesarias
        cols_necesarias = ['Fecha', 'Descripcion', 'Monto']
        if not all(c in df.columns for c in cols_necesarias):
            st.error(f"El archivo debe contener al menos: {cols_necesarias}")
            return None

        df['Descripcion'] = df['Descripcion'].fillna('').astype(str).str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Monto'] = df['Monto'].astype(str).str.replace('"', '', regex=False).astype(float)
        
        df = df.dropna(subset=['Monto', 'Fecha']).drop_duplicates()
        df = aplicar_inteligencia_categorizacion(df)

        # Formateo temporal
        df['Mes'] = df['Fecha'].dt.strftime('%Y-%m')
        dias = {0:'Lunes', 1:'Martes', 2:'Miércoles', 3:'Jueves', 4:'Viernes', 5:'Sábado', 6:'Domingo'}
        df['Dia_Semana'] = df['Fecha'].dt.dayofweek.map(dias)
        
        return df
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
        return None

# ==================== INTERFAZ DE USUARIO ====================

# Inicializar estado
if 'data' not in st.session_state:
    st.session_state.data = None

if st.session_state.data is None:
    # --- PANTALLA DE INICIO ---
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://images.unsplash.com/photo-1580519542036-c47de6196ba5?auto=format&fit=crop&q=80&w=400", caption="Controla tus finanzas")
    
    with col2:
        st.title("Bienvenido a tu Gestor de Gastos")
        st.markdown("""
        Esta herramienta procesa tus movimientos bancarios, unifica comercios (como Uber o Wong) 
        y clasifica todo en 8 categorías clave para que entiendas en qué se va tu dinero.
        """)
        
        st.subheader("¿Cómo quieres empezar?")
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🚀 Usar Datos de Ejemplo (gastos.csv)", use_container_width=True):
                if os.path.exists('gastos.csv'):
                    st.session_state.data = procesar_archivo('gastos.csv')
                    st.rerun()
                else:
                    st.error("No se encontró el archivo 'gastos.csv' en el repositorio.")
        
        with col_btn2:
            st.info("O sube tu propio archivo debajo")

        st.markdown("---")
        st.write("### Cargar mis datos")
        uploaded_file = st.file_uploader("Sube tu CSV o Excel", type=["csv", "xlsx"])
        
        if uploaded_file:
            is_excel = uploaded_file.name.endswith('.xlsx')
            if st.button("Procesar mi archivo"):
                st.session_state.data = procesar_archivo(uploaded_file, is_excel=is_excel)
                st.rerun()

        with st.expander("📌 Requisitos del archivo (Formato mínimo)"):
            st.write("""
            Para que el sistema funcione, tu archivo debe tener estas columnas:
            - **Fecha**: (DD/MM/AAAA o AAAA-MM-DD)
            - **Descripcion**: Nombre del establecimiento o detalle.
            - **Monto**: Valor numérico del gasto.
            - *Opcional*: **Categoria** (Si ya tienes una clasificación propia).
            """)

else:
    # --- TABLERO ACTIVO ---
    df = st.session_state.data
    
    # Botón reset en Sidebar
    if st.sidebar.button("🗑️ Borrar datos y volver al inicio"):
        st.session_state.data = None
        st.rerun()

    st.sidebar.header("🔍 Filtros Globales")
    meses = sorted(df['Mes'].unique())
    meses_sel = st.sidebar.multiselect("Filtrar Meses", meses, default=meses)
    
    categorias = sorted(df['Categoria_Final'].unique())
    cats_sel = st.sidebar.multiselect("Filtrar Categorías", categorias, default=categorias)
    
    df_f = df[(df['Mes'].isin(meses_sel)) & (df['Categoria_Final'].isin(cats_sel))]
    
    tab1, tab2 = st.tabs(["🔥 Vista General", "📊 Análisis Detallado"])
    
    with tab1:
        c1, c2, c3 = st.columns(3)
        c1.metric("Gasto Total", f"S/ {df_f['Monto'].sum():,.2f}")
        c2.metric("Transacciones", len(df_f))
        c3.metric("Ticket Promedio", f"S/ {df_f['Monto'].mean():,.2f}" if not df_f.empty else "0")
        
        st.markdown("---")
        st.subheader("Mapa de Calor: Concentración de Gasto")
        if not df_f.empty:
            pivot = df_f.pivot_table(index='Categoria_Final', columns='Mes', values='Monto', aggfunc='sum').fillna(0)
            st.plotly_chart(px.imshow(pivot, text_auto='.0f', color_continuous_scale='OrRd', aspect="auto"), use_container_width=True)

    with tab2:
        st.subheader("Composición Acumulada por Mes")
        fig_bar = px.bar(df_f.groupby(['Mes', 'Categoria_Final'])['Monto'].sum().reset_index(), 
                        x='Mes', y='Monto', color='Categoria_Final', text_auto='.2s')
        st.plotly_chart(fig_bar, use_container_width=True)
        
        col_l, col_r = st.columns(2)
        with col_l:
            st.subheader("Top 10 Comercios")
            top_c = df_f.groupby('Comercio')['Monto'].sum().nlargest(10).reset_index()
            st.plotly_chart(px.bar(top_c, x='Monto', y='Comercio', orientation='h', color='Monto'), use_container_width=True)
        with col_r:
            st.subheader("Distribución Semanal")
            orden_dias = ['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']
            dias_g = df_f.groupby('Dia_Semana')['Monto'].sum().reindex(orden_dias).reset_index()
            st.plotly_chart(px.bar(dias_g, x='Dia_Semana', y='Monto', color='Dia_Semana'), use_container_width=True)

    with st.expander("📋 Detalle de Transacciones Filtradas"):
        st.dataframe(df_f[['Fecha', 'Comercio', 'Categoria_Final', 'Monto']].sort_values('Fecha', ascending=False), use_container_width=True)
