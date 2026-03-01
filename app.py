import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuración de página
st.set_page_config(page_title="Gestor de Gastos Inteligente", layout="wide")

# Lista de categorías maestras
CATEGORIAS_MAESTRAS = [
    'Supermercados', 
    'Restaurantes & Delivery', 
    'Transporte & Auto', 
    'Salud & Bienestar', 
    'Hogar & Servicios', 
    'Viajes & Ocio', 
    'Compras & Tech', 
    'Transferencias & Otros'
]

# ==================== FUNCIONES DE PROCESAMIENTO ====================

def procesar_csv(file):
    """Lógica de limpieza y categorización automática"""
    try:
        # Lectura robusta
        df = pd.read_csv(file, encoding='latin1', sep=',', quoting=3)
        df.columns = df.columns.str.replace('"', '').str.strip()
        
        # Limpieza de comillas y nulos
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace('"', '', regex=False)
        
        df['Descripcion'] = df['Descripcion'].fillna('').astype(str).str.strip()
        df['Categoria_Original'] = df['Categoria'].fillna('').astype(str).str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Monto'] = df['Monto'].astype(str).str.replace('"', '', regex=False).astype(float)
        
        df = df.dropna(subset=['Monto', 'Fecha']).drop_duplicates()

        # Reglas de unificación de comercios
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

        # Reglas de categorización simplificada
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

        # Aplicar categorías
        df['Categoria_Final'] = 'Transferencias & Otros'
        for nueva_cat, palabras in reglas_simplificadas.items():
            patron = '|'.join(palabras)
            mask = df['Descripcion'].str.contains(patron, case=False, na=False)
            df.loc[mask, 'Categoria_Final'] = nueva_cat

        # Si ya tiene una categoría maestra manual, respetarla
        mask_manual = df['Categoria_Original'].isin(CATEGORIAS_MAESTRAS)
        df.loc[mask_manual, 'Categoria_Final'] = df['Categoria_Original']

        # Formatear columnas temporales
        df['Mes'] = df['Fecha'].dt.strftime('%Y-%m')
        dias = {0:'Lunes', 1:'Martes', 2:'Miércoles', 3:'Jueves', 4:'Viernes', 5:'Sábado', 6:'Domingo'}
        df['Dia_Semana'] = df['Fecha'].dt.dayofweek.map(dias)
        
        return df
    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
        return None

# ==================== INTERFAZ DE USUARIO ====================

st.title("💰 Dashboard de Gastos Personal")

# Inicializar el estado de los datos
if 'data' not in st.session_state:
    st.session_state.data = None

# 1. Módulo de Carga
with st.expander("📂 Paso 1: Subir Archivo CSV", expanded=(st.session_state.data is None)):
    uploaded_file = st.file_uploader("Elige tu archivo gastos.csv", type="csv")
    if uploaded_file is not None:
        if st.button("Procesar y Ver Tablero"):
            st.session_state.data = procesar_csv(uploaded_file)
            st.rerun()

# Botón para borrar todo (Sidebar)
if st.session_state.data is not None:
    if st.sidebar.button("🗑️ Borrar todos los datos"):
        st.session_state.data = None
        st.rerun()

# 2. Visualización del Tablero
if st.session_state.data is not None:
    df = st.session_state.data
    
    # Filtros Sidebar
    st.sidebar.header("Filtros")
    meses = sorted(df['Mes'].unique())
    meses_sel = st.sidebar.multiselect("Meses", meses, default=meses)
    
    categorias = sorted(df['Categoria_Final'].unique())
    cats_sel = st.sidebar.multiselect("Categorías", categorias, default=categorias)
    
    # Aplicar filtros
    df_f = df[(df['Mes'].isin(meses_sel)) & (df['Categoria_Final'].isin(cats_sel))]
    
    # Pestañas
    tab1, tab2 = st.tabs(["🔥 Vista Principal", "📊 Análisis Detallado"])
    
    with tab1:
        # Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Gastado", f"S/ {df_f['Monto'].sum():,.2f}")
        c2.metric("N° Operaciones", len(df_f))
        c3.metric("Ticket Promedio", f"S/ {df_f['Monto'].mean():,.2f}" if len(df_f)>0 else "0")
        
        st.markdown("---")
        st.subheader("Mapa de Calor: Intensidad de Gasto")
        if not df_f.empty:
            heat = df_f.pivot_table(index='Categoria_Final', columns='Mes', values='Monto', aggfunc='sum').fillna(0)
            fig_h = px.imshow(heat, text_auto='.0f', color_continuous_scale='Blues', aspect="auto")
            st.plotly_chart(fig_h, use_container_width=True)

    with tab2:
        st.subheader("Composición Mensual")
        fig_b = px.bar(df_f.groupby(['Mes', 'Categoria_Final'])['Monto'].sum().reset_index(), 
                     x='Mes', y='Monto', color='Categoria_Final', text_auto='.2s')
        st.plotly_chart(fig_b, use_container_width=True)
        
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Top Comercios")
            top = df_f.groupby('Comercio')['Monto'].sum().nlargest(10).reset_index()
            st.plotly_chart(px.bar(top, x='Monto', y='Comercio', orientation='h'), use_container_width=True)
        with col_right:
            st.subheader("Gasto por Día")
            dias_g = df_f.groupby('Dia_Semana')['Monto'].sum().reindex(['Lunes','Martes','Miércoles','Jueves','Viernes','Sábado','Domingo']).reset_index()
            st.plotly_chart(px.bar(dias_g, x='Dia_Semana', y='Monto'), use_container_width=True)

    with st.expander("📋 Ver lista de movimientos"):
        st.write(df_f[['Fecha', 'Comercio', 'Categoria_Final', 'Monto']].sort_values('Fecha', ascending=False))
else:
    st.info("Por favor, sube un archivo CSV para comenzar el análisis.")