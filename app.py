import streamlit as st
import json
import os
import pandas as pd
import math
import random

# ==========================================
# 1. CONFIGURACIÓN BASE Y ESTILO MÓVIL
# ==========================================
st.set_page_config(
    page_title="Zohan Pronostic v2 - Análisis Avanzado",
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
# 2. GESTIÓN DE BASE DE DATOS Y RESPALDO TXT
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

# ==========================================
# 3. ACTUALIZACIÓN DESDE LA TABLA
# ==========================================
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

    eq_l["PJ_L"] += factor * 1
    eq_l["PG_L"] += factor * pg_l
    eq_l["PE_L"] += factor * pe_l
    eq_l["PP_L"] += factor * pp_l
    eq_l["GF_L"] += factor * gl
    eq_l["GC_L"] += factor * gv
    eq_l["DG_L"] = eq_l["GF_L"] - eq_l["GC_L"]
    eq_l["Pts_L"] += factor * pts_l

    eq_v = tabla[visitante]
    eq_v["PJ"] += factor * 1
    eq_v["PG"] += factor * pg_v
    eq_v["PE"] += factor * pe_v
    eq_v["PP"] += factor * pp_v
    eq_v["GF"] += factor * gv
    eq_v["GC"] += factor * gl
    eq_v["DG"] = eq_v["GF"] - eq_v["GC"]
    eq_v["Pts"] += factor * pts_v

    eq_v["PJ_V"] += factor * 1
    eq_v["PG_V"] += factor * pg_v
    eq_v["PE_V"] += factor * pe_v
    eq_v["PP_V"] += factor * pp_v
    eq_v["GF_V"] += factor * gv
    eq_v["GC_V"] += factor * gl
    eq_v["DG_V"] = eq_v["GF_V"] - eq_v["GC_V"]
    eq_v["Pts_V"] += factor * pts_v

# ==========================================
# 4. MOTOR MATEMÁTICO 100% BASADO EN LA TABLA
# ==========================================
def calcular_metricas_equipo(eq_stats):
    pj = max(1, eq_stats["PJ"])
    pj_l = max(1, eq_stats["PJ_L"])
    pj_v = max(1, eq_stats["PJ_V"])
    
    return {
        "prom_gf_local": eq_stats["GF_L"] / pj_l,
        "prom_gc_local": eq_stats["GC_L"] / pj_l,
        "prom_gf_visitante": eq_stats["GF_V"] / pj_v,
        "prom_gc_visitante": eq_stats["GC_V"] / pj_v,
    }

def motor_analisis_avanzado(stats_local, stats_visita, iteraciones_mc=10000):
    mL = calcular_metricas_equipo(stats_local)
    mV = calcular_metricas_equipo(stats_visita)
    
    # 1. Lambda Poisson puro desde la tabla
    lambda_home = max(0.2, (mL["prom_gf_local"] + mV["prom_gc_visitante"]) / 2)
    lambda_away = max(0.2, (mV["prom_gf_visitante"] + mL["prom_gc_local"]) / 2)

    # 2. Simulador de Montecarlo (10,000 iteraciones estocásticas)
    wins_l, wins_v, draws = 0, 0, 0
    conteo_scores = {}
    
    for _ in range(iteraciones_mc):
        # Generar goles usando distribución de Poisson basada en los lambdas de la tabla
        g_l = np_poisson_sim(lambda_home)
        g_v = np_poisson_sim(lambda_away)
        
        if g_l > g_v:
            wins_l += 1
        elif g_l < g_v:
            wins_v += 1
        else:
            draws += 1
            
        score_key = (g_l, g_v)
        conteo_scores[score_key] = conteo_scores.get(score_key, 0) + 1

    p_local = (wins_l / iteraciones_mc) * 100
    p_empate = (draws / iteraciones_mc) * 100
    p_visita = (wins_v / iteraciones_mc) * 100

    # 3. Cuotas Justas (Fair Odds)
    cuota_l = round(100 / max(0.1, p_local), 2)
    cuota_e = round(100 / max(0.1, p_empate), 2)
    cuota_v = round(100 / max(0.1, p_visita), 2)

    # 4. Retroceso Fibonacci aplicado a la dispersión de goles y umbrales de tendencia
    xg_total = round(lambda_home + lambda_away, 2)
    niveles_fib = [0.236, 0.382, 0.618]
    umbral_fib = round(xg_total * (1 + niveles_fib[1]), 2) # Nivel analítico del 38.2%

    # 5. Top Marcadores Exactos por Montecarlo
    sorted_scores = sorted(conteo_scores.items(), key=lambda x: x[1], reverse=True)
    top_scores = [(s[0][0], s[0][1], (s[1] / iteraciones_mc) * 100) for s in sorted_scores[:3]]

    # 6. Mercados
    ambos_marcan = "Sí" if (lambda_home >= 0.95 and lambda_away >= 0.95) else "No"
    rec_goles = "Más de 2.5" if xg_total > 2.6 else ("Menos de 2.5" if xg_total < 2.1 else "Línea 1.5 / 2.0")

    return {
        "xg_local": round(lambda_home, 2),
        "xg_visita": round(lambda_away, 2),
        "xg_total": xg_total,
        "p_local": round(p_local, 1),
        "p_empate": round(p_empate, 1),
        "p_visita": round(p_visita, 1),
        "cuota_l": cuota_l,
        "cuota_e": cuota_e,
        "cuota_v": cuota_v,
        "umbral_fib": umbral_fib,
        "top_scores": top_scores,
        "ambos_marcan": ambos_marcan,
        "rec_goles": rec_goles
    }

def np_poisson_sim(lmbda):
    # Generador nativo de Poisson sin librerías externas pesadas
    L = math.exp(-lmbda)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

# ==========================================
# 5. INTERFAZ STREAMLIT DE USUARIO
# ==========================================
db = cargar_base_datos()

liga_seleccionada = st.sidebar.selectbox("⚽ Seleccionar Liga", list(LIGAS_EQUIPOS.keys()), key="select_liga_main")
datos_liga = db[liga_seleccionada]

# --- BARRA LATERAL: RESPALDO TXT ---
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

# PESTAÑAS PRINCIPALES
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Tabla de Posiciones", 
    "⚙️ Carga Directa (Tabla)", 
    "📝 Registrar Match a Match", 
    "🎯 Analizador Cuantitativo"
])

# --- TAB 1: TABLA DE POSICIONES ---
with tab1:
    st.header(f"Tabla de Posiciones - {liga_seleccionada}")
    filtro_vista = st.radio("Vista de Clasificación:", ["General", "Local", "Visitante"], horizontal=True)
    
    df_tabla = pd.DataFrame.from_dict(datos_liga["tabla"], orient="index")
    if filtro_vista == "General":
        columnas = ["PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]
    elif filtro_vista == "Local":
        columnas = ["PJ_L", "PG_L", "PE_L", "PP_L", "GF_L", "GC_L", "DG_L", "Pts_L"]
    else:
        columnas = ["PJ_V", "PG_V", "PE_V", "PP_V", "GF_V", "GC_V", "DG_V", "Pts_V"]

    df_vista = df_tabla[columnas].copy()
    df_vista.columns = ["PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]
    df_vista = df_vista.sort_values(by=["Pts", "DG", "GF"], ascending=False)
    st.dataframe(df_vista, use_container_width=True)

# --- TAB 2: CARGA DIRECTA DE LA TABLA (EQUIPOS) ---
with tab2:
    st.header("⚙️ Configuración Directa de Estadísticas en la Tabla")
    st.info("Introduce directamente las estadísticas acumuladas extraídas de la tabla para cada equipo, separadas por su rendimiento en casa y fuera.")
    
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    equipo_sel = st.selectbox("Selecciona un Equipo:", equipos_disponibles, key="select_eq_carga_dir")
    datos_actuales = datos_liga["tabla"][equipo_sel]
    
    with st.form(key=f"form_carga_{equipo_sel}"):
        col_l, col_vis = st.columns(2)
        with col_l:
            st.markdown("### 🏠 Rendimiento Local")
            pg_l = st.number_input("Partidos Ganados (Local)", min_value=0, value=int(datos_actuales["PG_L"]))
            pe_l = st.number_input("Partidos Empatados (Local)", min_value=0, value=int(datos_actuales["PE_L"]))
            pp_l = st.number_input("Partidos Perdidos (Local)", min_value=0, value=int(datos_actuales["PP_L"]))
            gf_l = st.number_input("Goles a Favor (Local)", min_value=0, value=int(datos_actuales["GF_L"]))
            gc_l = st.number_input("Goles en Contra (Local)", min_value=0, value=int(datos_actuales["GC_L"]))
            
        with col_vis:
            st.markdown("### ✈️ Rendimiento Visitante")
            pg_v = st.number_input("Partidos Ganados (Visitante)", min_value=0, value=int(datos_actuales["PG_V"]))
            pe_v = st.number_input("Partidos Empatados (Visitante)", min_value=0, value=int(datos_actuales["PE_V"]))
            pp_v = st.number_input("Partidos Perdidos (Visitante)", min_value=0, value=int(datos_actuales["PP_V"]))
            gf_v = st.number_input("Goles a Favor (Visitante)", min_value=0, value=int(datos_actuales["GF_V"]))
            gc_v = st.number_input("Goles en Contra (Visitante)", min_value=0, value=int(datos_actuales["GC_V"]))
            
        btn_actualizar = st.form_submit_button("💾 Guardar en la Tabla", type="primary")
        
        if btn_actualizar:
            pj_l = pg_l + pe_l + pp_l
            pts_l = (pg_l * 3) + pe_l
            dg_l = gf_l - gc_l
            
            pj_v = pg_v + pe_v + pp_v
            pts_v = (pg_v * 3) + pe_v
            dg_v = gf_v - gc_v
            
            datos_liga["tabla"][equipo_sel] = {
                "PJ": pj_l + pj_v, "PG": pg_l + pg_v, "PE": pe_l + pe_v, "PP": pp_l + pp_v,
                "GF": gf_l + gf_v, "GC": gc_l + gc_v, "DG": dg_l + dg_v, "Pts": pts_l + pts_v,
                "PJ_L": pj_l, "PG_L": pg_l, "PE_L": pe_l, "PP_L": pp_l, "GF_L": gf_l, "GC_L": gc_l, "DG_L": dg_l, "Pts_L": pts_l,
                "PJ_V": pj_v, "PG_V": pg_v, "PE_V": pe_v, "PP_V": pp_v, "GF_V": gf_v, "GC_V": gc_v, "DG_V": dg_v, "Pts_V": pts_v
            }
            guardar_base_datos(db)
            st.success(f"¡Tabla actualizada para **{equipo_sel}**!")
            st.rerun()

# --- TAB 3: REGISTRAR PARTIDO A PARTIDO ---
with tab3:
    st.header("Registrar Partido (Impacto Automático en la Tabla)")
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    
    with st.form(key="form_match"):
        c1, c2 = st.columns(2)
        with c1:
            eq_l = st.selectbox("Local", equipos_disponibles, index=0)
            gl = st.number_input("Goles Local", min_value=0, step=1, value=0)
        with c2:
            eq_v = st.selectbox("Visitante", equipos_disponibles, index=1 if len(equipos_disponibles)>1 else 0)
            gv = st.number_input("Goles Visitante", min_value=0, step=1, value=0)
            
        if st.form_submit_button("⚽ Registrar y Actualizar Tabla", type="primary"):
            if eq_l == eq_v:
                st.error("El local y visitante deben ser distintos.")
            else:
                aplicar_partido_a_tabla(datos_liga["tabla"], eq_l, eq_v, gl, gv)
                datos_liga["historial"].append({"local": eq_l, "visitante": eq_v, "goles_local": gl, "goles_visita": gv})
                guardar_base_datos(db)
                st.success("¡Partido registrado y tabla actualizada!")
                st.rerun()

    st.markdown("---")
    st.subheader("Historial de Partidos")
    if datos_liga["historial"]:
        for idx, p in enumerate(reversed(datos_liga["historial"])):
            idx_real = len(datos_liga["historial"]) - 1 - idx
            col_h1, col_h2 = st.columns([4, 1])
            with col_h1:
                st.write(f"**{p['local']}** {p['goles_local']} - {p['goles_visita']} **{p['visitante']}**")
            with col_h2:
                if st.button("Eliminar", key=f"del_{idx_real}"):
                    pb = datos_liga["historial"].pop(idx_real)
                    aplicar_partido_a_tabla(datos_liga["tabla"], pb["local"], pb["visitante"], pb["goles_local"], pb["goles_visita"], revertir=True)
                    guardar_base_datos(db)
                    st.rerun()

# --- TAB 4: ANALIZADOR CUANTITATIVO (POISSON + MONTE CARLO + FIBONACCI + CUOTAS) ---
with tab4:
    st.header("🎯 Analizador Cuantitativo Avanzado")
    st.info("Todos los cálculos se generan 100% en base al rendimiento acumulado en la tabla de posiciones.")
    
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    cp1, cp2 = st.columns(2)
    with cp1:
        p_local = st.selectbox("Equipo Local", equipos_disponibles, key="analisis_loc")
    with cp2:
        p_visita = st.selectbox("Equipo Visitante", equipos_disponibles, index=1 if len(equipos_disponibles)>1 else 0, key="analisis_vis")

    if p_local == p_visita:
        st.warning("Selecciona dos equipos diferentes.")
    else:
        stats_l = datos_liga["tabla"][p_local]
        stats_v = datos_liga["tabla"][p_visita]
        
        # Ejecutar motor cuantitativo
        res = motor_analisis_avanzado(stats_l, stats_v)
        
        st.markdown("---")
        st.subheader("📊 Reporte de Pronóstico y Probabilidades (Montecarlo 10k)")
        
        r1, r2, r3 = st.columns(3)
        r1.metric(f"Victoria {p_local}", f"{res['p_local']}%", f"Cuota: {res['cuota_l']}")
        r2.metric("Empate", f"{res['p_empate']}%", f"Cuota: {res['cuota_e']}")
        r3.metric(f"Victoria {p_visita}", f"{res['p_visita']}%", f"Cuota: {res['cuota_v']}")
        
        st.markdown("---")
        st.subheader("⚽ Goles Esperados (xG) & Análisis Fibonacci")
        xg1, xg2, xg3, xg4 = st.columns(4)
        xg1.metric(f"xG Local", res['xg_local'])
        xg2.metric(f"xG Visitante", res['xg_visita'])
        xg3.metric("xG Total", res['xg_total'])
        xg4.metric("Umbral Fibonacci (38.2%)", res['umbral_fib'])
        
        st.markdown("---")
        st.subheader("🎯 Top 3 Marcadores Exactos (Simulación)")
        sc1, sc2, sc3 = st.columns(3)
        top = res['top_scores']
        if len(top) >= 1:
            sc1.info(f"**1º Opción:** {p_local} {top[0][0]} - {top[0][1]} {p_visita}\n\nProb: {round(top[0][2], 1)}%")
        if len(top) >= 2:
            sc2.info(f"**2º Opción:** {p_local} {top[1][0]} - {top[1][1]} {p_visita}\n\nProb: {round(top[1][2], 1)}%")
        if len(top) >= 3:
            sc3.info(f"**3º Opción:** {p_local} {top[2][0]} - {top[2][1]} {p_visita}\n\nProb: {round(top[2][2], 1)}%")
            
        st.markdown("---")
        st.subheader("💡 Recomendaciones de Mercado")
        m_rec1, m_rec2 = st.columns(2)
        m_rec1.success(f"**Línea de Goles:** {res['rec_goles']}")
        m_rec2.success(f"**Ambos Anotan (BTTS):** {res['ambos_marcan']}")

