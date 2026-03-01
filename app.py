import streamlit as st
import pandas as pd
import plotly.express as px
import os
import re

# ==================== CONFIGURACIÓN Y ESTILOS ====================
st.set_page_config(page_title="PlatitAI - Inteligencia Financiera", layout="wide")

BRAND_STYLE = """
    <h1 style='text-align: center; color: #00A8E8; font-family: sans-serif;'>PlatitAI</h1>
    <p style='text-align: center; color: #666;'>Inteligencia Financiera Predictiva</p>
"""

# ==================== ESTADO DE SESIÓN ====================
if 'data' not in st.session_state:
    st.session_state.data = None
if 'tipo_data' not in st.session_state:
    st.session_state.tipo_data = None
if 'budgets' not in st.session_state:
    st.session_state.budgets = {}
if 'fijos' not in st.session_state:
    st.session_state.fijos = []
if 'mis_categorias' not in st.session_state:
    st.session_state.mis_categorias = [
        'Supermercados', 'Restaurantes & Delivery', 'Transporte & Auto', 
        'Salud & Bienestar', 'Hogar & Servicios', 'Viajes & Ocio', 
        'Compras & Tech', 'Transferencias & Otros'
    ]

# ==================== FUNCIONES DE PROCESAMIENTO ====================

def aplicar_inteligencia(df, categorias_usuario):
    df['Comercio'] = df['Descripcion'].str.upper().str.replace('*', '', regex=False).str.strip()
    
    reglas_ia = {
        'Supermercados': ['wong', 'metro', 'tottus', 'mass', 'oxxo', 'tambo'],
        'Restaurantes & Delivery': ['rappi', 'pedidosya', 'starbucks', 'kfc', 'cafe', 'pizz'],
        'Transporte & Auto': ['uber', 'cabify', 'taxi', 'grifo', 'peaje', 'gasolin'],
        'Salud & Bienestar': ['farmacia', 'clinica', 'smart fit', 'pacifico'],
        'Hogar & Servicios': ['sodimac', 'maestro', 'promart', 'movistar', 'claro', 'sedapal'],
        'Viajes & Ocio': ['airbnb', 'booking', 'latam', 'spotify', 'youtube', 'netflix'],
        'Compras & Tech': ['apple', 'aliexpress', 'amazon', 'ebay', 'h&m', 'zara'],
        'Transferencias & Otros': ['plin-', 'yape', 'transferencia']
    }

    df['Categoria_Final'] = categorias_usuario[-1] if categorias_usuario else "Otros"
    for cat, palabras in reglas_ia.items():
        if cat in categorias_usuario:
            mask = df['Descripcion'].str.contains('|'.join(palabras), case=False, na=False)
            df.loc[mask, 'Categoria_Final'] = cat
    
    if 'Categoria' in df.columns:
        df['Categoria'] = df['Categoria'].fillna('').astype(str).strip()
        mask = df['Categoria'].isin(categorias_usuario)
        df.loc[mask, 'Categoria_Final'] = df['Categoria']

    return df

def cargar_datos(file, is_excel=False):
    try:
        if is_excel: df = pd.read_excel(file)
        else:
            try: df = pd.read_csv(file, encoding='utf-8-sig', sep=',', quoting=3)
            except: df = pd.read_csv(file, encoding='latin1', sep=',', quoting=3)
        
        df.columns = df.columns.str.replace('"', '').str.strip()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df['Monto'] = pd.to_numeric(df['Monto'].astype(str).str.replace('"', '', regex=False), errors='coerce')
        df = df.dropna(subset=['Monto', 'Fecha']).drop_duplicates()
        return aplicar_inteligencia(df, st.session_state.mis_categorias)
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# ==================== BARRA LATERAL (MENÚ) ====================

with st.sidebar:
    st.markdown(BRAND_STYLE, unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?q=80&w=200", use_container_width=True)
    st.markdown("---")
    
    if st.session_state.data is not None:
        # CONVERSIÓN DE MONEDA
        st.subheader("💱 Moneda")
        moneda = st.radio("Mostrar datos en:", ["Soles (S/)", "Dólares ($)"], horizontal=True)
        tc = st.number_input("Tipo de cambio", value=3.75, step=0.01)
        
        st.markdown("---")
        menu = st.radio("Navegación", ["🔥 Dashboard", "🎯 Presupuestos", "📈 Análisis Avanzado", "✏️ Recategorizar", "⚙️ Configuración"])
        
        if st.button("🗑️ Reiniciar Sesión", use_container_width=True):
            st.session_state.data = None
            st.rerun()
    else:
        menu = "Inicio"

# ==================== LÓGICA DE PÁGINAS ====================

if st.session_state.data is None:
    st.title("Bienvenido a PlatitAI")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("### 1. Configura tus Categorías")
        cats_raw = st.text_area("Una por línea:", value="\n".join(st.session_state.mis_categorias), height=150)
        if st.button("Guardar Estructura"):
            st.session_state.mis_categorias = [c.strip() for c in cats_raw.split("\n") if c.strip()]
            st.success("Categorías listas.")
        
        st.markdown("---")
        st.markdown("### 2. Carga de Datos")
        file = st.file_uploader("Sube CSV o Excel", type=["csv", "xlsx"])
        if st.button("🚀 Usar Ejemplo"):
            if os.path.exists('gastos.csv'):
                st.session_state.data = cargar_datos('gastos.csv')
                st.session_state.tipo_data = "EJEMPLO"
                st.rerun()
        if file and st.button("Procesar Archivo"):
            st.session_state.data = cargar_datos(file, file.name.endswith('.xlsx'))
            st.session_state.tipo_data = "TUS DATOS"
            st.rerun()
    with c2:
        st.image("https://images.unsplash.com/photo-1554224155-6726b3ff858f?q=80&w=500")
        st.info("PlatitAI limpiará comillas, duplicados y categorizará tus gastos automáticamente.")

else:
    # Ajuste de Moneda
    df = st.session_state.data.copy()
    simbolo = "S/" if moneda == "Soles (S/)" else "$"
    if simbolo == "$":
        df['Monto'] = df['Monto'] / tc

    df['Mes'] = df['Fecha'].dt.strftime('%Y-%m')
    df['Dia_Mes'] = df['Fecha'].dt.day
    
    # Filtros Sidebar
    with st.sidebar:
        st.markdown("---")
        meses_sel = st.multiselect("Meses", sorted(df['Mes'].unique()), default=sorted(df['Mes'].unique())[-2:])
        cats_sel = st.multiselect("Categorías", sorted(st.session_state.mis_categorias), default=st.session_state.mis_categorias)
    
    df_f = df[(df['Mes'].isin(meses_sel)) & (df['Categoria_Final'].isin(cats_sel))]

    # 1. PÁGINA: DASHBOARD (Con Alertas y MoM)
    if menu == "🔥 Dashboard":
        label_color = "#888" if st.session_state.tipo_data == "EJEMPLO" else "#2E7D32"
        st.markdown(f"<h2 style='text-align: center; color: {label_color};'>{st.session_state.tipo_data}</h2>", unsafe_allow_html=True)
        
        # Lógica MoM (Mes a Mes)
        total_actual = df_f['Monto'].sum()
        if len(meses_sel) >= 1:
            mes_actual = meses_sel[-1]
            gasto_mes_actual = df[df['Mes'] == mes_actual]['Monto'].sum()
            
            # Buscar mes anterior
            all_meses = sorted(df['Mes'].unique())
            idx = all_meses.index(mes_actual)
            if idx > 0:
                mes_anterior = all_meses[idx-1]
                gasto_mes_anterior = df[df['Mes'] == mes_anterior]['Monto'].sum()
                variacion = ((gasto_mes_actual / gasto_mes_anterior) - 1) * 100
                delta_color = "inverse" # Rojo si sube, Verde si baja
            else:
                gasto_mes_anterior = 0
                variacion = 0
                delta_color = "normal"

        c1, c2, c3 = st.columns(3)
        c1.metric(f"Gasto {mes_actual}", f"{simbolo} {gasto_mes_actual:,.2f}", f"{variacion:.1f}% vs mes anterior", delta_color=delta_color)
        c2.metric("Transacciones", len(df_f))
        c3.metric("Ticket Promedio", f"{simbolo} {df_f['Monto'].mean():,.2f}" if not df_f.empty else "0")

        # Alertas de Presupuesto
        st.markdown("### 🎯 Estado de Presupuestos")
        cols_b = st.columns(len(st.session_state.budgets) if st.session_state.budgets else 1)
        if not st.session_state.budgets:
            st.info("Configura techos de gasto en la pestaña 'Presupuestos' para ver alertas aquí.")
        else:
            for i, (cat, limit) in enumerate(st.session_state.budgets.items()):
                spent = df[(df['Mes'] == mes_actual) & (df['Categoria_Final'] == cat)]['Monto'].sum()
                ratio = min(spent / limit, 1.0)
                color = "green" if ratio < 0.7 else "orange" if ratio < 0.9 else "red"
                with cols_b[i % len(cols_b)]:
                    st.write(f"**{cat}**")
                    st.progress(ratio)
                    st.write(f"{simbolo} {spent:,.0f} / {limit:,.0f}")
                    if ratio >= 1.0: st.error("🔥 ¡Límite superado!")
                    elif ratio >= 0.85:
                        # Alerta IA Proyectada
                        dia_hoy = pd.Timestamp.now().day
                        proyeccion = (spent / dia_hoy) * 30
                        if proyeccion > limit:
                            st.warning(f"⚠️ IA: Al ritmo actual, cerrarás el mes en {simbolo} {proyeccion:,.0f}")

        st.markdown("---")
        st.subheader("📅 Patrones de Gasto por Día del Mes")
        daily_trend = df_f.groupby('Dia_Mes')['Monto'].sum().reset_index()
        fig_trend = px.line(daily_trend, x='Dia_Mes', y='Monto', markers=True, title="¿Cuándo gastas más? (Día 1 al 31)")
        st.plotly_chart(fig_trend, use_container_width=True)

    # 2. PÁGINA: PRESUPUESTOS (Configuración)
    elif menu == "🎯 Presupuestos":
        st.header("Configuración de Presupuestos y Gastos Fijos")
        col_b1, col_b2 = st.columns(2)
        
        with col_b1:
            st.subheader("Establecer Límites Mensuales")
            cat_to_limit = st.selectbox("Selecciona Categoría", st.session_state.mis_categorias)
            limit_val = st.number_input(f"Monto máximo mensual ({simbolo})", min_value=0, value=1000)
            if st.button("Fijar Presupuesto"):
                st.session_state.budgets[cat_to_limit] = limit_val
                st.success(f"Presupuesto para {cat_to_limit} guardado.")
            
            st.write("---")
            st.write("Presupuestos actuales:", st.session_state.budgets)

        with col_b2:
            st.subheader("Clasificar Gastos Fijos")
            st.write("Selecciona los comercios que son 'Gastos de Supervivencia' (Alquiler, Luz, Seguros).")
            all_comercios = sorted(df['Comercio'].unique())
            fijos_sel = st.multiselect("Marcar como Fijos", all_comercios, default=st.session_state.fijos)
            if st.button("Guardar Gastos Fijos"):
                st.session_state.fijos = fijos_sel
                st.success("Clasificación guardada.")

    # 3. PÁGINA: ANÁLISIS AVANZADO (Detector Hormiga y Suscripciones)
    elif menu == "📈 Análisis Avanzado":
        tab_a, tab_b, tab_c = st.tabs(["🐜 Gastos Hormiga", "🕵️ Suscripciones", "📊 Top 10"])
        
        with tab_a:
            umbral = st.slider("Monto máximo de Gasto Hormiga:", 5, 50, 20)
            hormiga = df_f[df_f['Monto'] <= umbral]
            st.error(f"Total en Gastos Hormiga: {simbolo} {hormiga['Monto'].sum():,.2f}")
            st.plotly_chart(px.pie(hormiga, names='Comercio', values='Monto'), use_container_width=True)

        with tab_b:
            st.subheader("Detector de Pagos Recurrentes")
            recurrentes = df.groupby(['Comercio', 'Monto']).agg(Veces=('Fecha', 'count'), Meses=('Mes', 'nunique')).reset_index()
            suscrip = recurrentes[recurrentes['Meses'] >= 2].sort_values('Veces', ascending=False)
            st.dataframe(suscrip, use_container_width=True)

        with tab_c:
            col_l, col_r = st.columns(2)
            top_m = df_f.groupby('Comercio')['Monto'].sum().nlargest(10).reset_index()
            top_f = df_f.groupby('Comercio')['Monto'].count().nlargest(10).reset_index()
            col_l.plotly_chart(px.bar(top_m, x='Monto', y='Comercio', orientation='h', title="Top 10 por Gasto Total"), use_container_width=True)
            col_r.plotly_chart(px.bar(top_f, x='Monto', y='Comercio', orientation='h', title="Top 10 por Frecuencia"), use_container_width=True)

    # 4. PÁGINA: RECATEGORIZAR (Bulk Edit)
    elif menu == "✏️ Recategorizar":
        st.header("Módulo de Recategorización")
        res_edit = df.groupby('Comercio').agg(Total=('Monto', 'sum'), Cat=('Categoria_Final', 'first')).reset_index().sort_values('Total', ascending=False)
        res_edit['Nueva'] = res_edit['Cat']
        editado = st.data_editor(res_edit, column_config={"Nueva": st.column_config.SelectboxColumn("Cambiar a:", options=st.session_state.mis_categorias)}, hide_index=True, use_container_width=True)
        
        if st.button("💾 Aplicar Cambios Permanentes"):
            for _, row in editado.iterrows():
                st.session_state.data.loc[st.session_state.data['Comercio'] == row['Comercio'], 'Categoria_Final'] = row['Nueva']
            st.rerun()

    # 5. PÁGINA: CONFIGURACIÓN (Exportar)
    elif menu == "⚙️ Configuración":
        st.header("⚙️ Gestión de Datos")
        st.write("Costo de Vida Mínimo (Gastos Fijos):")
        fijos_df = df_f[df_f['Comercio'].isin(st.session_state.fijos)]
        st.warning(f"Tu gasto fijo en este periodo es: {simbolo} {fijos_df['Monto'].sum():,.2f}")
        
        st.markdown("---")
        st.subheader("Exportar Datos")
        csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 Descargar CSV Limpio", csv, "platit_final.csv", "text/csv")
