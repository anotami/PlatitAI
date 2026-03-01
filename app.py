import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Configuración de página
st.set_page_config(page_title="PlatitAI - Inteligencia Financiera", layout="wide")

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

# ==================== CARGA Y PROCESAMIENTO ====================

def aplicar_inteligencia(df, categorias_usuario):
    # Normalización para evitar problemas con tildes y mayúsculas
    df['Comercio'] = df['Descripcion'].str.upper().str.strip()
    
    reglas = {
        'Supermercados': ['wong', 'metro', 'tottus', 'mass', 'oxxo', 'tambo', 'jumbo', 'market'],
        'Restaurantes & Delivery': ['rappi', 'pedidosya', 'starbucks', 'kfc', 'mcdonalds', 'cafe', 'pizz', 'delivery'],
        'Transporte & Auto': ['uber', 'cabify', 'taxi', 'grifo', 'peaje', 'apparka', 'gasolin'],
        'Salud & Bienestar': ['farmacia', 'clinica', 'smart fit', 'smartfit', 'dent', 'fisio', 'pacifico'],
        'Hogar & Servicios': ['sodimac', 'maestro', 'promart', 'movistar', 'claro', 'enel', 'sedapal', 'calidda'],
        'Viajes & Ocio': ['airbnb', 'booking', 'latam', 'hotel', 'cine', 'spotify', 'youtube', 'netflix', 'disney'],
        'Compras & Tech': ['apple', 'aliexpress', 'amazon', 'ebay', 'falabella', 'ripley', 'h&m', 'zara'],
        'Transferencias & Otros': ['plin-', 'yape', 'transferencia', 'cargo']
    }
    
    default_cat = categorias_usuario[-1] if categorias_usuario else "Otros"
    df['Categoria_Final'] = default_cat
    
    for cat_maestra, palabras in reglas.items():
        if cat_maestra in categorias_usuario:
            patron = '|'.join(palabras)
            mask = df['Descripcion'].str.contains(patron, case=False, na=False)
            df.loc[mask, 'Categoria_Final'] = cat_maestra
            
    return df

def cargar_datos(file, is_excel=False):
    try:
        if is_excel:
            df = pd.read_excel(file)
        else:
            try:
                df = pd.read_csv(file, encoding='utf-8-sig', sep=',', quoting=3)
            except:
                df = pd.read_csv(file, encoding='latin1', sep=',', quoting=3)
        
        df.columns = df.columns.str.replace('"', '').str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Monto'] = pd.to_numeric(df['Monto'].astype(str).str.replace('"', '', regex=False), errors='coerce')
        df = df.dropna(subset=['Monto', 'Fecha'])
        return aplicar_inteligencia(df, st.session_state.mis_categorias)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

# ==================== BARRA LATERAL ====================

with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #00A8E8;'>PlatitAI</h1>", unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?q=80&w=200", use_container_width=True)
    st.markdown("---")
    
    if st.session_state.data is None:
        menu = "Inicio"
    else:
        menu = st.radio(
            "Análisis",
            ["🔥 Dashboard", "🕵️ Detector de Suscripciones", "🐜 Gastos Hormiga", "📊 Top 10 (Monto vs Freq)", "✏️ Editor", "⚙️ Ajustes"],
            index=0
        )
        st.markdown("---")
        if st.button("🗑️ Reiniciar Sesión"):
            st.session_state.data = None
            st.rerun()

# ==================== LÓGICA DE PÁGINAS ====================

if st.session_state.data is None:
    st.title("Bienvenido a PlatitAI")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 1. Sube tus datos")
        file = st.file_uploader("CSV o Excel", type=["csv", "xlsx"])
        if st.button("🚀 Usar Ejemplo"):
            if os.path.exists('gastos.csv'):
                st.session_state.data = cargar_datos('gastos.csv')
                st.session_state.tipo_data = "Ejemplo"
                st.rerun()
        if file and st.button("Procesar Archivo"):
            st.session_state.data = cargar_datos(file, file.name.endswith('.xlsx'))
            st.session_state.tipo_data = "Usuario"
            st.rerun()
    with c2:
        st.markdown("### 2. Categorías")
        cats = st.text_area("Una por línea:", value="\n".join(st.session_state.mis_categorias), height=150)
        if st.button("Guardar"):
            st.session_state.mis_categorias = [c.strip() for c in cats.split("\n") if c.strip()]
            st.success("Listo")

else:
    # Header dinámico
    label = "🛠️ DATOS DE EJEMPLO" if st.session_state.tipo_data == "Ejemplo" else "👤 TUS DATOS"
    st.markdown(f"<h3 style='text-align: center; color: gray;'>{label}</h3>", unsafe_allow_html=True)
    
    df = st.session_state.data
    df['Mes'] = df['Fecha'].dt.strftime('%Y-%m')
    
    # Filtros laterales
    with st.sidebar:
        meses_sel = st.multiselect("Meses", sorted(df['Mes'].unique()), default=sorted(df['Mes'].unique()))
        df_f = df[df['Mes'].isin(meses_sel)]

    # --- PÁGINAS ---

    if menu == "🔥 Dashboard":
        st.header("Vista General")
        col1, col2, col3 = st.columns(3)
        col1.metric("Gasto Total", f"S/ {df_f['Monto'].sum():,.2f}")
        col2.metric("Transacciones", len(df_f))
        col3.metric("Ticket Promedio", f"S/ {df_f['Monto'].mean():,.2f}")
        
        pivot = df_f.pivot_table(index='Categoria_Final', columns='Mes', values='Monto', aggfunc='sum').fillna(0)
        st.plotly_chart(px.imshow(pivot, text_auto='.0f', color_continuous_scale='Blues', title="Mapa de Calor"), use_container_width=True)

    elif menu == "🕵️ Detector de Suscripciones":
        st.header("Detector de Gastos Recurrentes")
        st.write("Identificamos comercios con el mismo monto que aparecen en varios meses.")
        
        # Agrupar por comercio, monto y contar meses únicos
        recurrentes = df.groupby(['Comercio', 'Monto']).agg(
            Frecuencia=('Fecha', 'count'),
            Meses_Unicos=('Mes', 'nunique')
        ).reset_index()
        
        # Filtro: debe aparecer en al menos 2 meses distintos
        suscripciones = recurrentes[recurrentes['Meses_Unicos'] >= 2].sort_values('Frecuencia', ascending=False)
        
        if not suscripciones.empty:
            st.dataframe(suscripciones, use_container_width=True)
            st.info("💡 Consejo: Revisa si estas suscripciones siguen siendo útiles para ti.")
        else:
            st.write("No se detectaron patrones recurrentes claros.")

    elif menu == "🐜 Gastos Hormiga":
        st.header("Análisis de Gastos Hormiga")
        umbral = st.slider("Define el monto máximo de un 'gasto hormiga' (S/):", 5, 50, 20)
        
        hormiga = df_f[df_f['Monto'] <= umbral]
        total_h = hormiga['Monto'].sum()
        
        st.warning(f"Has gastado **S/ {total_h:,.2f}** en montos menores a S/ {umbral}.")
        
        fig_h = px.pie(hormiga, names='Comercio', values='Monto', title="¿En qué se va el goteo de dinero?")
        st.plotly_chart(fig_h, use_container_width=True)

    elif menu == "📊 Top 10 (Monto vs Freq)":
        st.header("Ranking de Consumo")
        col_l, col_r = st.columns(2)
        
        with col_l:
            st.subheader("Top 10 por Monto (S/)")
            top_m = df_f.groupby('Comercio')['Monto'].sum().nlargest(10).reset_index()
            st.plotly_chart(px.bar(top_m, x='Monto', y='Comercio', orientation='h', color_discrete_sequence=['#EF553B']), use_container_width=True)
            
        with col_r:
            st.subheader("Top 10 por Repetición (Veces)")
            top_f = df_f.groupby('Comercio')['Monto'].count().nlargest(10).reset_index()
            top_f.columns = ['Comercio', 'Visitas']
            st.plotly_chart(px.bar(top_f, x='Visitas', y='Comercio', orientation='h', color_discrete_sequence=['#00CC96']), use_container_width=True)

    elif menu == "✏️ Editor":
        st.header("Recategorización")
        resumen = df.groupby('Comercio').agg(Total=('Monto', 'sum'), Cat=('Categoria_Final', 'first')).reset_index()
        resumen['Nueva'] = resumen['Cat']
        
        editado = st.data_editor(resumen, column_config={"Nueva": st.column_config.SelectboxColumn("Nueva", options=st.session_state.mis_categorias)}, use_container_width=True)
        
        if st.button("Aplicar"):
            for _, r in editado.iterrows():
                st.session_state.data.loc[st.session_state.data['Comercio'] == r['Comercio'], 'Categoria_Final'] = r['Nueva']
            st.rerun()

    elif menu == "⚙️ Ajustes":
        st.header("Exportación")
        st.dataframe(df)
        csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("Descargar CSV Limpio", csv, "platit_ai_report.csv", "text/csv")
