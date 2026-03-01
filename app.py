import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re

# ==================== CONFIGURACIÓN Y ESTILOS ====================
st.set_page_config(page_title="PlatitAI | FTDStudio", layout="wide")

# Estilo para el nombre de la marca
BRAND_STYLE = """
    <h1 style='text-align: center; color: #00A8E8; font-family: sans-serif;'>PlatitAI</h1>
    <p style='text-align: center; color: #666;'>Inteligencia Financiera Personal</p>
"""

# ==================== ESTADO DE SESIÓN ====================
if 'data' not in st.session_state:
    st.session_state.data = None
if 'tipo_data' not in st.session_state:
    st.session_state.tipo_data = None
if 'mis_categorias' not in st.session_state:
    st.session_state.mis_categorias = [
        'Supermercados', 'Restaurantes & Delivery', 'Transporte & Auto', 
        'Salud & Bienestar', 'Hogar & Servicios', 'Viajes & Ocio', 
        'Compras & Tech', 'Transferencias & Otros'
    ]

# ==================== FUNCIONES DE PROCESAMIENTO ====================

def aplicar_inteligencia_categorizacion(df, categorias_usuario):
    """Unificación de comercios y categorización automática inteligente"""
    
    # 1. Unificación de nombres (Limpieza de asteriscos y mayúsculas)
    df['Comercio'] = df['Descripcion'].str.upper().str.replace('*', '', regex=False).str.strip()
    
    reglas_agrupacion = {
        'WONG': 'Wong', 'UBER': 'Uber', 'RAPPI': 'Rappi', 'PLIN': 'Plin',
        'APPLE': 'Apple', 'FRISKA': 'Friska', 'SMART FIT': 'Smart Fit',
        'PACIFICO': 'Pacifico Seguros', 'MASS': 'Tiendas Mass', 'OXXO': 'Oxxo',
        'ALIEXPRESS': 'AliExpress', 'AMAZON': 'Amazon', 'LATAM': 'Latam Airlines',
        'VENDOMATICA': 'Vendomática', 'CINEPLANET': 'Cineplanet', 'SODIMAC': 'Sodimac',
        'MAESTRO': 'Maestro'
    }

    for clave, nombre_limpio in reglas_agrupacion.items():
        mask = df['Comercio'].str.contains(clave, case=False, na=False)
        df.loc[mask, 'Comercio'] = nombre_limpio

    # 2. Reglas de categorías automáticas
    reglas_ia = {
        'Supermercados': ['wong', 'metro', 'tottus', 'mass', 'oxxo', 'tambo', 'market', 'jumbo', 'carrefour'],
        'Restaurantes & Delivery': ['rappi', 'pedidosya', 'dominos', 'restaurante', 'cafe', 'starbucks', 'kfc', 'mcdonalds', 'pizzeria', 'sushi'],
        'Transporte & Auto': ['uber', 'cabify', 'taxi', 'grifo', 'peaje', 'estacion', 'apparka', 'gasolin'],
        'Salud & Bienestar': ['farmacia', 'clinica', 'smart fit', 'smartfit', 'dent', 'fisio', 'spa', 'pacifico', 'hospital'],
        'Hogar & Servicios': ['sodimac', 'maestro', 'promart', 'movistar', 'claro', 'enel', 'sedapal', 'notaria', 'calidda'],
        'Viajes & Ocio': ['airbnb', 'booking', 'latam', 'hotel', 'cine', 'spotify', 'youtube', 'netflix', 'disney', 'despegar'],
        'Compras & Tech': ['apple', 'aliexpress', 'amazon', 'ebay', 'h&m', 'zara', 'miniso', 'tai loy', 'falabella', 'ripley'],
        'Transferencias & Otros': ['plin-', 'yape', 'transferencia', 'cargo da ']
    }

    default_cat = categorias_usuario[-1] if categorias_usuario else "Otros"
    df['Categoria_Final'] = default_cat
    
    for nueva_cat, palabras in reglas_ia.items():
        if nueva_cat in categorias_usuario:
            patron = '|'.join(palabras)
            mask = df['Descripcion'].str.contains(patron, case=False, na=False)
            df.loc[mask, 'Categoria_Final'] = nueva_cat
    
    # 3. Respetar categorías previas si coinciden con la lista del usuario
    if 'Categoria' in df.columns:
        df['Categoria'] = df['Categoria'].fillna('').astype(str).str.strip()
        mask_manual = df['Categoria'].isin(categorias_usuario)
        df.loc[mask_manual, 'Categoria_Final'] = df['Categoria']

    return df

def procesar_archivo(file, is_excel=False):
    """Cargador universal con codificación robusta"""
    try:
        if is_excel:
            df = pd.read_excel(file)
        else:
            try:
                df = pd.read_csv(file, encoding='utf-8-sig', sep=',', quoting=3)
            except:
                df = pd.read_csv(file, encoding='latin1', sep=',', quoting=3)
        
        # Limpieza de encabezados y caracteres extraños
        df.columns = df.columns.str.replace('"', '').str.strip()
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.replace('"', '', regex=False).str.strip()
        
        # Validación de columnas
        cols_necesarias = ['Fecha', 'Descripcion', 'Monto']
        if not all(c in df.columns for c in cols_necesarias):
            st.error(f"Faltan columnas obligatorias: {cols_necesarias}")
            return None

        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Monto'] = pd.to_numeric(df['Monto'], errors='coerce')
        
        # Eliminación de Duplicados y Nulos
        df = df.dropna(subset=['Monto', 'Fecha']).drop_duplicates()
        
        # Aplicar IA de categorización
        df = aplicar_inteligencia_categorizacion(df, st.session_state.mis_categorias)

        # Formateo temporal
        df['Mes'] = df['Fecha'].dt.strftime('%Y-%m')
        dias = {0:'Lunes', 1:'Martes', 2:'Miércoles', 3:'Jueves', 4:'Viernes', 5:'Sábado', 6:'Domingo'}
        df['Dia_Semana_Num'] = df['Fecha'].dt.dayofweek
        df['Dia_Semana'] = df['Dia_Semana_Num'].map(dias)
        
        return df
    except Exception as e:
        st.error(f"Error al procesar: {e}")
        return None

# ==================== BARRA LATERAL (MENÚ) ====================

with st.sidebar:
    st.markdown(BRAND_STYLE, unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?q=80&w=200", use_container_width=True)
    st.markdown("---")
    
    if st.session_state.data is None:
        menu = "Inicio"
        st.info("Configura y sube tus datos para empezar")
    else:
        menu = st.radio(
            "Menú de Análisis",
            ["🔥 Vista General", "📈 Evolutivo Mensual", "🕵️ Inteligencia de Gasto", "📊 Rankings Top 10", "✏️ Recategorizar"],
            index=0
        )
        st.markdown("---")
        if st.button("🗑️ Borrar Todo y Reiniciar", use_container_width=True):
            st.session_state.data = None
            st.session_state.tipo_data = None
            st.rerun()

# ==================== LÓGICA DE PÁGINAS ====================

if st.session_state.data is None:
    # --- PANTALLA DE INICIO / PERSONALIZACIÓN ---
    st.title("Bienvenido a PlatitAI")
    
    col_intro, col_setup = st.columns([1, 1])
    
    with col_intro:
        st.markdown("""
        ### Control financiero inteligente
        PlatitAI organiza tus consumos bancarios, detecta suscripciones y analiza tus hábitos automáticamente.
        
        **Instrucciones:**
        1. Define tus categorías a la derecha.
        2. Sube tu archivo CSV/Excel o usa el ejemplo.
        """)
        
        uploaded_file = st.file_uploader("Cargar movimientos (CSV o Excel)", type=["csv", "xlsx"])
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 Usar Datos de Ejemplo", use_container_width=True):
                if os.path.exists('gastos.csv'):
                    st.session_state.data = procesar_archivo('gastos.csv')
                    st.session_state.tipo_data = "EJEMPLO"
                    st.rerun()
        with c2:
            if uploaded_file and st.button("Procesar Mi Archivo", use_container_width=True):
                st.session_state.data = procesar_archivo(uploaded_file, uploaded_file.name.endswith('.xlsx'))
                st.session_state.tipo_data = "TUS DATOS"
                st.rerun()

    with col_setup:
        st.subheader("⚙️ Configuración de Categorías")
        st.write("Edita las categorías que PlatitAI usará para clasificar:")
        cats_raw = st.text_area("Una categoría por línea:", value="\n".join(st.session_state.mis_categorias), height=200)
        if st.button("💾 Guardar Mi Estructura"):
            st.session_state.mis_categorias = [c.strip() for c in cats_raw.split("\n") if c.strip()]
            st.success("Estructura guardada.")

else:
    # --- CABECERA DINÁMICA ---
    color_label = "#888" if st.session_state.tipo_data == "EJEMPLO" else "#2E7D32"
    st.markdown(f"<h1 style='text-align: center; color: {color_label}; font-size: 50px;'>{st.session_state.tipo_data}</h1>", unsafe_allow_html=True)
    st.markdown("---")

    df = st.session_state.data
    
    # Filtros Globales en Sidebar
    with st.sidebar:
        st.subheader("🔍 Filtros")
        meses_sel = st.multiselect("Filtrar Meses", sorted(df['Mes'].unique()), default=sorted(df['Mes'].unique()))
        categorias_sel = st.multiselect("Filtrar Categorías", sorted(df['Categoria_Final'].unique()), default=sorted(df['Categoria_Final'].unique()))
    
    df_f = df[(df['Mes'].isin(meses_sel)) & (df['Categoria_Final'].isin(categorias_sel))]

    # --- NAVEGACIÓN ---

    if menu == "🔥 Vista General":
        m1, m2, m3 = st.columns(3)
        m1.metric("Gasto Total", f"S/ {df_f['Monto'].sum():,.2f}")
        m2.metric("N° Operaciones", len(df_f))
        m3.metric("Ticket Promedio", f"S/ {df_f['Monto'].mean():,.2f}" if not df_f.empty else "0")
        
        st.markdown("---")
        if not df_f.empty:
            st.subheader("🌡️ Mapa de Calor: Intensidad de Gasto por Categoría")
            pivot = df_f.pivot_table(index='Categoria_Final', columns='Mes', values='Monto', aggfunc='sum').fillna(0)
            st.plotly_chart(px.imshow(pivot, text_auto='.0f', color_continuous_scale='OrRd', aspect="auto"), use_container_width=True)

    elif menu == "📈 Evolutivo Mensual":
        st.subheader("📊 Composición Acumulada de Gastos")
        evolutivo = df_f.groupby(['Mes', 'Categoria_Final'])['Monto'].sum().reset_index()
        fig_evol = px.bar(evolutivo, x='Mes', y='Monto', color='Categoria_Final', text_auto='.2s', title="Gasto Total Mensual por Categoría")
        st.plotly_chart(fig_evol, use_container_width=True)

    elif menu == "🕵️ Inteligencia de Gasto":
        st.header("🕵️ Análisis de Comportamiento")
        
        # 1. Detector de Suscripciones
        with st.expander("💳 Detector de Suscripciones y Recurrentes", expanded=True):
            st.write("Comercios con el mismo monto exacto que aparecen en 2 o más meses distintos.")
            recurrentes = df.groupby(['Comercio', 'Monto']).agg(Veces=('Fecha', 'count'), Meses=('Mes', 'nunique')).reset_index()
            suscrip = recurrentes[recurrentes['Meses'] >= 2].sort_values('Veces', ascending=False)
            st.table(suscrip)

        # 2. Detector de Gastos Hormiga
        st.markdown("---")
        st.subheader("🐜 Gastos Hormiga")
        umbral = st.slider("Define el monto máximo para 'Gasto Hormiga' (S/):", 5, 50, 20)
        hormiga = df_f[df_f['Monto'] <= umbral]
        total_h = hormiga['Monto'].sum()
        st.warning(f"Total acumulado en Gastos Hormiga: S/ {total_h:,.2f}")
        st.plotly_chart(px.pie(hormiga, names='Comercio', values='Monto', title="Distribución de Gastos Pequeños"), use_container_width=True)

    elif menu == "📊 Rankings Top 10":
        st.header("📊 Rankings de Consumo")
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Top 10 por Monto Total (S/)")
            top_monto = df_f.groupby('Comercio')['Monto'].sum().nlargest(10).reset_index()
            st.plotly_chart(px.bar(top_monto, x='Monto', y='Comercio', orientation='h', color='Monto', color_continuous_scale='Reds'), use_container_width=True)
            
        with c2:
            st.subheader("Top 10 por Frecuencia (Visitas)")
            top_freq = df_f.groupby('Comercio')['Monto'].count().nlargest(10).reset_index()
            top_freq.columns = ['Comercio', 'Frecuencia']
            st.plotly_chart(px.bar(top_freq, x='Frecuencia', y='Comercio', orientation='h', color='Frecuencia', color_continuous_scale='Greens'), use_container_width=True)

    elif menu == "✏️ Recategorizar":
        st.header("✏️ Módulo de Recategorización en Lote")
        st.write("Cambia la categoría de un comercio para normalizar todos tus datos históricos.")
        
        # Preparamos tabla resumen por Comercio
        res_edit = df.groupby('Comercio').agg(
            Total_Gastado=('Monto', 'sum'),
            Categoria_Actual=('Categoria_Final', 'first')
        ).reset_index().sort_values('Total_Gastado', ascending=False)
        
        res_edit['Nueva_Categoria'] = res_edit['Categoria_Actual']

        df_editor = st.data_editor(
            res_edit,
            column_config={
                "Nueva_Categoria": st.column_config.SelectboxColumn("🎯 Seleccionar Nueva", options=st.session_state.mis_categorias)
            },
            disabled=["Comercio", "Total_Gastado", "Categoria_Actual"],
            hide_index=True,
            use_container_width=True
        )

        if st.button("💾 Aplicar Cambios a Toda la Sesión", type="primary"):
            for _, row in df_editor.iterrows():
                if row['Categoria_Actual'] != row['Nueva_Categoria']:
                    st.session_state.data.loc[st.session_state.data['Comercio'] == row['Comercio'], 'Categoria_Final'] = row['Nueva_Categoria']
            st.success("¡Categorías actualizadas!")
            st.rerun()

    # Expander de datos crudos al final de cualquier página
    with st.expander("📋 Ver Registro Completo de Movimientos"):
        st.dataframe(df_f[['Fecha', 'Comercio', 'Categoria_Final', 'Monto']].sort_values('Fecha', ascending=False), use_container_width=True)

