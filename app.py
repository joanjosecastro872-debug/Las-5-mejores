# /mount/src/las-5-mejores/app.py
import streamlit as st
import json
import os
import pandas as pd
import numpy as np
from scipy.stats import poisson

# ==========================================
# 1. CONFIGURACIÓN BASE Y ESTILO MÓVIL
# ==========================================
st.set_page_config(
    page_title="Zohan Pronostic v6.5 - Elite Fibonacci, H2H & Top 5",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        overflow-x: auto;
        white-space: nowrap;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: nowrap;
    }
    </style>
""", unsafe_allow_html=True)

DB_FILE = "zohan_pronostic_db.json"

LIGAS_EQUIPOS = {
    "🇪🇸 LaLiga": [
        "Athletic Club", "Atlético de Madrid", "CA Osasuna", "Celta de Vigo", 
        "Deportivo Alavés", "Deportivo de La Coruña", "Elche CF", "FC Barcelona", 
        "Getafe CF", "Levante UD", "Málaga CF", "Racing de Santander", 
        "Rayo Vallecano", "RCD Espanyol", "Real Betis", "Real Madrid", 
        "Real Sociedad", "Sevilla FC", "Valencia CF", "Villarreal CF"
    ],
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": [
        "Arsenal FC", "Aston Villa", "AFC Bournemouth", "Brentford FC", 
        "Brighton & Hove Albion", "Chelsea FC", "Coventry City", "Crystal Palace", 
        "Everton FC", "Fulham FC", "Hull City", "Ipswich Town", 
        "Leeds United", "Liverpool FC", "Manchester City", "Manchester United", 
        "Newcastle United", "Nottingham Forest", "Sunderland AFC", "Tottenham Hotspur"
    ],
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": [
        "Birmingham City", "Blackburn Rovers", "Bolton Wanderers", "Bristol City", 
        "Burnley FC", "Cardiff City", "Charlton Athletic", "Derby County", 
        "Lincoln City", "Middlesbrough FC", "Millwall FC", "Norwich City", 
        "Portsmouth FC", "Preston North End", "Queens Park Rangers (QPR)", "Sheffield United", 
        "Southampton FC", "Stoke City", "Swansea City", "Watford FC", 
        "West Bromwich Albion", "West Ham United", "Wolverhampton Wanderers", "Wrexham AFC"
    ],
    "🇮🇹 Serie A": [
        "AC Milan", "AC Monza", "AS Roma", "Atalanta BC", 
        "Bologna FC", "Cagliari Calcio", "Como 1907", "Fiorentina", 
        "Frosinone Calcio", "Genoa CFC", "Inter de Milán", "Juventus", 
        "Parma Calcio", "Sassuolo", "SS Lazio", "SSC Napoli", 
        "Torino FC", "Udinese Calcio", "US Lecce", "Venezia FC"
    ],
    "🇩🇪 Bundesliga": [
        "1. FC Colonia", "1. FC Union Berlin", "1. FSV Mainz 05", "Bayer 04 Leverkusen", 
        "Bayern Múnich", "Borussia Dortmund", "Borussia Mönchengladbach", "Eintracht Frankfurt", 
        "FC Augsburg", "Hamburger SV", "Holstein Kiel", "RB Leipzig", 
        "SC Friburgo", "Schalke 04", "SV Werder Bremen", "TSG Hoffenheim", 
        "VfB Stuttgart", "VfL Wolfsburg"
    ],
    "🇫🇷 Ligue 1": [
        "AJ Auxerre", "Angers SCO", "AS Mónaco", "ESTAC Troyes", 
        "FC Lorient", "HAC Le Havre", "LOSC Lille", "OGC Niza", 
        "Olympique de Lyon", "Olympique de Marsella", "Paris FC", "Paris Saint-Germain", 
        "RC Estrasburgo", "RC Lens", "Stade Brestois 29", "Stade Rennais", 
        "Toulouse FC", "Stade de Reims"
    ]
}

# ==========================================
# 2. GESTIÓN DE BASE DE DATOS Y LÓGICA
# ==========================================
def obtener_estructura_equipo():
    return {
        "PJ": 0, "PG": 0, "PE": 0, "PP": 0, "GF": 0, "GC": 0, "DG": 0, "Pts": 0,
        "PJ_L": 0, "PG_L": 0, "PE_L": 0, "PP_L": 0, "GF_L": 0, "GC_L": 0, "DG_L": 0, "Pts_L": 0,
        "PJ_V": 0, "PG_V": 0, "PE_V": 0, "PP_V": 0, "GF_V": 0, "GC_V": 0, "DG_V": 0, "Pts_V": 0
    }

def inicializar_liga_vacia(equipos):
    tabla = {}
    for eq in equipos:
        tabla[eq] = obtener_estructura_equipo()
    return {"tabla": tabla, "historial": []}

def cargar_base_datos():
    keys_requeridas = obtener_estructura_equipo()
    data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    for liga, equipos in LIGAS_EQUIPOS.items():
        if liga not in data:
            data[liga] = inicializar_liga_vacia(equipos)
        else:
            if "tabla" not in data[liga]:
                data[liga]["tabla"] = {}
            if "historial" not in data[liga]:
                data[liga]["historial"] = []
                
            for eq in equipos:
                if eq not in data[liga]["tabla"]:
                    data[liga]["tabla"][eq] = obtener_estructura_equipo()
                else:
                    for key, val in keys_requeridas.items():
                        if key not in data[liga]["tabla"][eq]:
                            data[liga]["tabla"][eq][key] = val
    return data

def guardar_base_datos(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def aplicar_partido_a_tabla(tabla, local, visitante, gl, gv, revertir=False):
    factor = -1 if revertir else 1
    
    if gl > gv:
        pts_l, pts_v = 3, 0
        pg_l, pe_l, pp_l = 1, 0, 0
        pg_v, pe_v, pp_v = 0, 0, 1
    elif gl < gv:
        pts_l, pts_v = 0, 3
        pg_l, pe_l, pp_l = 0, 0, 1
        pg_v, pe_v, pp_v = 1, 0, 0
    else:
        pts_l, pts_v = 1, 1
        pg_l, pe_l, pp_l = 0, 1, 0
        pg_v, pe_v, pp_v = 0, 1, 0

    eq_l = tabla[local]
    eq_l["PJ"] += factor * 1
    eq_l["PG"] += factor * pg_l
    eq_l["PE"] += factor * pe_l
    eq_l["PP"] += factor * pp_l
    eq_l["GF"] += factor * gl
    eq_l["GC"] += factor * gv
    eq_l["DG"] = eq_l["GF"] - eq_l["GC"]
    eq_l["Pts"] += factor * pts_l

    eq_v = tabla[visitante]
    eq_v["PJ"] += factor * 1
    eq_v["PG"] += factor * pg_v
    eq_v["PE"] += factor * pe_v
    eq_v["PP"] += factor * pp_v
    eq_v["GF"] += factor * gv
    eq_v["GC"] += factor * gl
    eq_v["DG"] = eq_v["GF"] - eq_v["GC"]
    eq_v["Pts"] += factor * pts_v

def calcular_fibonacci_y_tendencia(stats_eq, historial, equipo):
    pj = max(1, stats_eq["PJ"])
    pts = stats_eq["Pts"]
    eficiencia = round((pts / (pj * 3)) * 100, 1) if pj > 0 else 0.0
    ratio_rendimiento = eficiencia / 100.0

    if ratio_rendimiento <= 0.35:
        fibo_estado = "Soporte Crítico (0.382) - Toca Fondo / Rebote Inminente"
        fibo_mensaje = "Zona de soporte profundo en retroceso de Fibonacci. Acumula presión extrema, ideal para rebote alcista."
        tendencia = "Bajista Agotada (Alta probabilidad de corrección positiva)"
    elif ratio_rendimiento >= 0.70:
        fibo_estado = "Zona de Resistencia Alta (0.236) - Techo de Rendimiento"
        fibo_mensaje = "Parte alta de la curva de Fibonacci. Muestra máxima solidez pero con riesgo de corrección a la baja si decae la intensidad."
        tendencia = "Alcista Sólida (Inercia ganadora dominante)"
    else:
        fibo_estado = "Zona de Transición Neutral (0.500 - 0.618)"
        fibo_mensaje = "Rango de equilibrio intermedio en la onda de Fibonacci, dependiente de los ajustes tácticos del encuentro."
        tendencia = "Estable / Transición Moderada"

    return {
        "eficiencia": eficiencia,
        "fibo_estado": fibo_estado,
        "fibo_mensaje": fibo_mensaje,
        "tendencia": tendencia
    }

def simular_monte_carlo(lambda_l, lambda_v, n_simulaciones=10000):
    goles_l = np.random.poisson(lambda_l, n_simulaciones)
    goles_v = np.random.poisson(lambda_v, n_simulaciones)
    
    wins_l = np.sum(goles_l > goles_v)
    wins_v = np.sum(goles_l < goles_v)
    empates = np.sum(goles_l == goles_v)
    
    p_l = (wins_l / n_simulaciones) * 100
    p_v = (wins_v / n_simulaciones) * 100
    p_e = (empates / n_simulaciones) * 100
    
    return p_l, p_e, p_v, goles_l, goles_v

def calcular_top_marcadores_exactos(lambda_l, lambda_v, top_n=5):
    goles_max = 6
    pmf_l = poisson.pmf(np.arange(goles_max), lambda_l)
    pmf_v = poisson.pmf(np.arange(goles_max), lambda_v)
    matriz = np.outer(pmf_l, pmf_v)
    
    resultados = []
    for gl in range(goles_max):
        for gv in range(goles_max):
            prob = float(matriz[gl, gv]) * 100
            resultados.append({
                "Marcador": f"{gl} - {gv}", 
                "Goles Local": gl, 
                "Goles Visitante": gv, 
                "Probabilidad (%)": round(prob, 2)
            })
            
    resultados_ordenados = sorted(resultados, key=lambda x: x["Probabilidad (%)"], reverse=True)
    return resultados_ordenados[:top_n]

# ==========================================
# 3. INTERFAZ STREAMLIT
# ==========================================
db = cargar_base_datos()

liga_sel = st.sidebar.selectbox("⚽ Seleccionar Liga", list(LIGAS_EQUIPOS.keys()), key="select_liga_main")
datos_liga = db[liga_sel]

st.sidebar.markdown("---")
st.sidebar.subheader("📱 Gestión de Archivo .TXT")
db_string = json.dumps(db, ensure_ascii=False, indent=4)
st.sidebar.download_button(
    label="📥 Descargar Base de Datos (.TXT)",
    data=db_string,
    file_name="zohan_pronostic_db.txt",
    mime="text/plain"
)

archivo_subido = st.sidebar.file_uploader("📤 Cargar Base de Datos (.TXT)", type=["txt"])
if archivo_subido is not None:
    try:
        contenido_cargado = json.load(archivo_subido)
        if isinstance(contenido_cargado, dict):
            guardar_base_datos(contenido_cargado)
            st.sidebar.success("¡Base de datos restaurada! Recarga la app.")
            if st.sidebar.button("🔄 Recargar"):
                st.rerun()
    except Exception:
        st.sidebar.error("Archivo .txt inválido.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Tabla de Posiciones", 
    "⚙️ Carga Directa Avanzada", 
    "📝 Registrar Partido", 
    "🔬 Auditoría Global y Cruzada",
    "🎯 Analizador Quirúrgico Elite"
])

# --- TAB 1: TABLA DE POSICIONES ---
with tab1:
    st.header(f"Tabla de Posiciones - {liga_sel}")
    if 'vista_tabla' not in st.session_state:
        st.session_state.vista_tabla = "General"

    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
        if st.button("🌐 Ver General", use_container_width=True, type="primary" if st.session_state.vista_tabla=="General" else "secondary"):
            st.session_state.vista_tabla = "General"
            st.rerun()
    with b_col2:
        if st.button("🏠 Ver Local", use_container_width=True, type="primary" if st.session_state.vista_tabla=="Local" else "secondary"):
            st.session_state.vista_tabla = "Local"
            st.rerun()
    with b_col3:
        if st.button("✈️ Ver Visitante", use_container_width=True, type="primary" if st.session_state.vista_tabla=="Visitante" else "secondary"):
            st.session_state.vista_tabla = "Visitante"
            st.rerun()

    filtro_vista = st.session_state.vista_tabla
    df_tabla = pd.DataFrame.from_dict(datos_liga["tabla"], orient="index")
    cols = ["PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"] if filtro_vista=="General" else (["PJ_L", "PG_L", "PE_L", "PP_L", "GF_L", "GC_L", "DG_L", "Pts_L"] if filtro_vista=="Local" else ["PJ_V", "PG_V", "PE_V", "PP_V", "GF_V", "GC_V", "DG_V", "Pts_V"])
    df_v = df_tabla[cols].copy()
    df_v.columns = ["PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]
    df_v = df_v.sort_values(by=["Pts", "DG", "GF"], ascending=False)
    st.dataframe(df_v, use_container_width=True)

# --- TAB 2: CARGA DIRECTA AVANZADA ---
with tab2:
    st.header("⚙️ Carga Directa Avanzada por Equipo")
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    eq_target = st.selectbox("Seleccionar Equipo a Configurar:", equipos_disponibles, key="eq_avanzado")
    dt_eq = datos_liga["tabla"][eq_target]
    
    with st.form(key=f"form_avanzado_{eq_target}"):
        col_l, col_v = st.columns(2)
        with col_l:
            st.markdown("### 🏠 Rendimiento Local")
            pj_l = st.number_input("PJ (L)", min_value=0, value=int(dt_eq["PJ_L"]))
            pg_l = st.number_input("PG (L)", min_value=0, value=int(dt_eq["PG_L"]))
            pe_l = st.number_input("PE (L)", min_value=0, value=int(dt_eq["PE_L"]))
            pp_l = st.number_input("PP (L)", min_value=0, value=int(dt_eq["PP_L"]))
            gf_l = st.number_input("GF (L)", min_value=0, value=int(dt_eq["GF_L"]))
            gc_l = st.number_input("GC (L)", min_value=0, value=int(dt_eq["GC_L"]))
        with col_v:
            st.markdown("### ✈️ Rendimiento Visitante")
            pj_v = st.number_input("PJ (V)", min_value=0, value=int(dt_eq["PJ_V"]))
            pg_v = st.number_input("PG (V)", min_value=0, value=int(dt_eq["PG_V"]))
            pe_v = st.number_input("PE (V)", min_value=0, value=int(dt_eq["PE_V"]))
            pp_v = st.number_input("PP (V)", min_value=0, value=int(dt_eq["PP_V"]))
            gf_v = st.number_input("GF (V)", min_value=0, value=int(dt_eq["GF_V"]))
            gc_v = st.number_input("GC (V)", min_value=0, value=int(dt_eq["GC_V"]))
            
        if st.form_submit_button("💾 Guardar Perfil", type="primary"):
            datos_liga["tabla"][eq_target] = {
                "PJ": pj_l + pj_v, "PG": pg_l + pg_v, "PE": pe_l + pe_v, "PP": pp_l + pp_v,
                "GF": gf_l + gf_v, "GC": gc_l + gc_v, "DG": (gf_l+gf_v)-(gc_l+gc_v), "Pts": (pg_l+pg_v)*3 + (pe_l+pe_v),
                "PJ_L": pj_l, "PG_L": pg_l, "PE_L": pe_l, "PP_L": pp_l, "GF_L": gf_l, "GC_L": gc_l, "DG_L": gf_l-gc_l, "Pts_L": pg_l*3+pe_l,
                "PJ_V": pj_v, "PG_V": pg_v, "PE_V": pe_v, "PP_V": pp_v, "GF_V": gf_v, "GC_V": gc_v, "DG_V": gf_v-gc_v, "Pts_V": pg_v*3+pe_v
            }
            guardar_base_datos(db)
            st.success("¡Guardado con éxito!")
            st.rerun()

# --- TAB 3: REGISTRO PARTIDO ---
with tab3:
    st.header("Registrar Partido")
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    with st.form(key="form_match_sync"):
        c1, c2 = st.columns(2)
        with c1:
            eq_l = st.selectbox("Local", equipos_disponibles, index=0)
            gl = st.number_input("Goles Local", min_value=0, step=1, value=0)
        with c2:
            eq_v = st.selectbox("Visitante", equipos_disponibles, index=1 if len(equipos_disponibles)>1 else 0)
            gv = st.number_input("Goles Visitante", min_value=0, step=1, value=0)
            
        if st.form_submit_button("⚽ Registrar", type="primary"):
            if eq_l == eq_v:
                st.error("El local y visitante no pueden ser iguales.")
            else:
                aplicar_partido_a_tabla(datos_liga["tabla"], eq_l, eq_v, gl, gv)
                datos_liga["historial"].append({"local": eq_l, "visitante": eq_v, "goles_local": gl, "goles_visita": gv})
                guardar_base_datos(db)
                st.success("¡Partido registrado!")
                st.rerun()

# --- TAB 4: AUDITORÍA GLOBAL Y CRUZADA ---
with tab4:
    st.header("🔬 Auditoría Global y Examen Cruzado por Equipo")
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    eq_audit = st.selectbox("Seleccionar Equipo a Examinar:", equipos_disponibles, key="select_audit_eq")
    
    if eq_audit:
        stats_audit = datos_liga["tabla"][eq_audit]
        fibo_audit = calcular_fibonacci_y_tendencia(stats_audit, datos_liga["historial"], eq_audit)
        
        st.markdown("---")
        st.subheader(f"📋 Radiografía Global & Fibonacci: {eq_audit}")
        m1, m2, m3 = st.columns(3)
        m1.metric("Eficiencia Total", f"{fibo_audit['eficiencia']}%")
        m2.metric("Tendencia Actual", fibo_audit['tendencia'])
        m3.metric("Nivel Fibonacci", fibo_audit['fibo_estado'])
        st.info(f"💡 **Nota Táctica:** {fibo_audit['fibo_mensaje']}")

# --- TAB 5: ANALIZADOR QUIRÚRGICO ELITE ---
with tab5:
    st.header(f"🎯 Analizador Quirúrgico Elite - Fibonacci, H2H & Top 5 ({liga_sel})")
    st.info("Los datos globales se extraen automáticamente de la tabla de posiciones. Registra abajo el historial cara a cara (H2H) y ejecuta el motor.")
    
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    cp1, cp2 = st.columns(2)
    with cp1:
        p_local = st.selectbox("Equipo Local", equipos_disponibles, key="sync_loc")
    with cp2:
        p_visita = st.selectbox("Equipo Visitante", equipos_disponibles, index=1 if len(equipos_disponibles)>1 else 0, key="sync_vis")

    stats_l_base = datos_liga["tabla"][p_local]
    stats_v_base = datos_liga["tabla"][p_visita]

    # Extracción automática estricta desde la tabla de posiciones
    m_pj_l = max(1, stats_l_base["PJ_L"])
    m_gf_l = stats_l_base["GF_L"]
    m_gc_l = stats_l_base["GC_L"]

    m_pj_v = max(1, stats_v_base["PJ_V"])
    m_gf_v = stats_v_base["GF_V"]
    m_gc_v = stats_v_base["GC_V"]

    with st.expander("📊 Datos Extraídos Automáticamente de la Tabla", expanded=False):
        ex_c1, ex_c2 = st.columns(2)
        with ex_c1:
            st.markdown(f"**🏠 Local ({p_local}) [Como Local]:**")
            st.write(f"- PJ: `{m_pj_l}` | GF: `{m_gf_l}` | GC: `{m_gc_l}`")
        with ex_c2:
            st.markdown(f"**✈️ Visitante ({p_visita}) [Como Visitante]:**")
            st.write(f"- PJ: `{m_pj_v}` | GF: `{m_gf_v}` | GC: `{m_gc_v}`")

    st.markdown("---")
    with st.expander("⚔️ Ingreso Manual: Últimos 10 Partidos Cara a Cara (H2H)", expanded=True):
        st.write("Registra el balance directo de los últimos 10 enfrentamientos entre ambos:")
        h2h_c1, h2h_c2, h2h_c3 = st.columns(3)
        with h2h_c1:
            m_h2h_v_loc = st.number_input(f"Victorias de {p_local}", min_value=0, max_value=10, value=3, key="h2h_vl")
        with h2h_c2:
            m_h2h_emp = st.number_input("Empates", min_value=0, max_value=10, value=3, key="h2h_pe")
        with h2h_c3:
            m_h2h_v_vis = st.number_input(f"Victorias de {p_visita}", min_value=0, max_value=10, value=4, key="h2h_vv")

    st.markdown("---")
    if p_local == p_visita:
        st.warning("⚠️ Selecciona dos equipos diferentes para realizar el análisis cruzado.")
    else:
        if st.button("🔥 Ejecutar Simulación Estocástica & Top 5 Marcadores Exactos", type="primary"):
            fibo_l = calcular_fibonacci_y_tendencia(stats_l_base, datos_liga["historial"], p_local)
            fibo_v = calcular_fibonacci_y_tendencia(stats_v_base, datos_liga["historial"], p_visita)
            
            gf_l_prom = m_gf_l / m_pj_l
            gc_l_prom = m_gc_l / m_pj_l
            gf_v_prom = m_gf_v / m_pj_v
            gc_v_prom = m_gc_v / m_pj_v
            
            lambda_local = (gf_l_prom + gc_v_prom) / 2
            lambda_visita = (gf_v_prom + gc_l_prom) / 2
            
            mc_prob_l, mc_prob_e, mc_prob_v, sim_gl, sim_gv = simular_monte_carlo(lambda_local, lambda_visita, 10000)
            prom_sim_gl = np.mean(sim_gl)
            prom_sim_gv = np.mean(sim_gv)

            top_marcadores = calcular_top_marcadores_exactos(lambda_local, lambda_visita, 5)

            st.markdown("---")
            st.subheader("📋 Mensaje y Desglose Táctico Integral (Fibonacci & Tendencia)")
            
            msg_clima = f"### 🏟️ Radiografía del Encuentro: {p_local} vs {p_visita}\n\n"
            
            msg_clima += f"#### 1️⃣ Tendencias y Niveles de Fibonacci\n"
            msg_clima += f"- **{p_local} (Local):** Tendencia: *{fibo_l['tendencia']}* | Nivel: **{fibo_l['fibo_estado']}**.\n  > *{fibo_l['fibo_mensaje']}*\n"
            msg_clima += f"- **{p_visita} (Visitante):** Tendencia: *{fibo_v['tendencia']}* | Nivel: **{fibo_v['fibo_estado']}**.\n  > *{fibo_v['fibo_mensaje']}*\n\n"
            
            msg_clima += f"#### 2️⃣ Historial Cara a Cara Manual (Últimos 10 partidos)\n"
            msg_clima += f"- Balance ingresado: `{m_h2h_v_loc}` victorias para {p_local} | `{m_h2h_emp}` empates | `{m_h2h_v_vis}` victorias para {p_visita}.\n\n"
            
            msg_clima += f"#### 3️⃣ Motor Matemático (Monte Carlo & Poisson)\n"
            msg_clima += f"- **Expectativa de Goles (Lambda):** Local: `{prom_sim_gl:.2f}` | Visitante: `{prom_sim_gv:.2f}`.\n"
            msg_clima += f"- **Probabilidades de Resultado:** Victoria Local: **{mc_prob_l:.1f}%** | Empate: **{mc_prob_e:.1f}%** | Victoria Visitante: **{mc_prob_v:.1f}%**.\n\n"
            
            msg_clima += f"#### 4️⃣ Top 5 Posibles Marcadores Exactos\n"
            for idx, m in enumerate(top_marcadores, 1):
                msg_clima += f"  {idx}. **{m['Marcador']}** (Probabilidad: **{m['Probabilidad (%)']}%**)\n"
            msg_clima += "\n"
            
            if mc_prob_l > mc_prob_v and mc_prob_l > mc_prob_e:
                veredicto_final = f"**Veredicto Táctico:** Escenario inclinado a favor del anfitrión (**{p_local}**). La inercia y los soportes respaldan el favoritismo."
            elif mc_prob_v > mc_prob_l and mc_prob_v > mc_prob_e:
                veredicto_final = f"**Veredicto Táctico:** Alerta de golpe foráneo. El visitante (**{p_visita}**) muestra argumentos numéricos idóneos para puntuar fuera de casa."
            else:
                veredicto_final = f"**Veredicto Táctico:** Partido de máxima paridad. Las curvas de Fibonacci apuntan a un duelo cerrado donde los detalles definirán el marcador."
                
            msg_clima += f"#### 🎯 Conclusión del Analizador\n{veredicto_final}"
            
            st.success(msg_clima)

            st.markdown("---")
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric(f"Victoria {p_local}", f"{mc_prob_l:.1f}%", f"Goles: {prom_sim_gl:.2f}")
            col_m2.metric("Empate Probable", f"{mc_prob_e:.1f}%")
            col_m3.metric(f"Victoria {p_visita}", f"{mc_prob_v:.1f}%", f"Goles: {prom_sim_gv:.2f}")

            st.markdown("---")
            st.subheader("🎯 Tabla de los 5 Posibles Marcadores Exactos")
            df_marcadores = pd.DataFrame(top_marcadores)
            st.dataframe(df_marcadores, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("🚨 Radar de Alerta Roja (Modo Francotirador)")
            UMBRAL_FRANCOTIRADOR = 78.0
            UMBRAL_VISITANTE_ELITE = 70.0
            
            if mc_prob_l >= UMBRAL_FRANCOTIRADOR:
                st.error(f"🎯 **¡ALERTA ROJA ACTIVADA!** Victoria aplastante proyectada para **{p_local}** con un **{mc_prob_l:.1f}%** de confianza estocástica.")
            elif mc_prob_v >= UMBRAL_VISITANTE_ELITE:
                st.error(f"🎯 **¡ALERTA ROJA ACTIVADA!** Asalto táctico proyectado de **{p_visita}** con un **{mc_prob_v:.1f}%** de probabilidad simulada.")
            else:
                st.info("🛡️ **Carril Normal:** Partido dentro de parámetros estándar. Sin alertas extremas; ideal para análisis conservador.")

