import streamlit as st
import json
import os
import pandas as pd
import math

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

# Listas base de ligas y equipos
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
# 2. GESTIÓN DE BASE DE DATOS JSON BLINDADA
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
# 3. LÓGICA DE ACTUALIZACIÓN DE ESTADÍSTICAS
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

    # Actualizar Local
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

    # Actualizar Visitante
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
# 4. MOTOR DE ANÁLISIS Y POISSON
# ==========================================
def calcular_metricas_equipo(eq_stats):
    pj = max(1, eq_stats["PJ"])
    pj_l = max(1, eq_stats["PJ_L"])
    pj_v = max(1, eq_stats["PJ_V"])
    
    return {
        "prom_gf_general": eq_stats["GF"] / pj,
        "prom_gc_general": eq_stats["GC"] / pj,
        "prom_gf_local": eq_stats["GF_L"] / pj_l,
        "prom_gc_local": eq_stats["GC_L"] / pj_l,
        "prom_gf_visitante": eq_stats["GF_V"] / pj_v,
        "prom_gc_visitante": eq_stats["GC_V"] / pj_v,
        "rendimiento_general": (eq_stats["Pts"] / (pj * 3)) * 100,
        "rendimiento_local": (eq_stats["Pts_L"] / (pj_l * 3)) * 100,
        "rendimiento_visitante": (eq_stats["Pts_V"] / (pj_v * 3)) * 100
    }

def calculate_poisson_matrix(home_data, away_data, max_goles=6):
    mL = calcular_metricas_equipo(home_data)
    mV = calcular_metricas_equipo(away_data)
    
    # xG esperado cruzando local/visitante y defensa general/específica
    lambda_home = (mL["prom_gf_local"] + mV["prom_gc_visitante"]) / 2
    lambda_away = (mV["prom_gf_visitante"] + mL["prom_gc_local"]) / 2

    # Asegurar valores mínimos lógicos para evitar ceros absolutos
    lambda_home = max(0.2, lambda_home)
    lambda_away = max(0.2, lambda_away)

    matrix = []
    for i in range(max_goles + 1):
        row = []
        prob_i = (lambda_home**i * math.exp(-lambda_home)) / math.factorial(i)
        for j in range(max_goles + 1):
            prob_j = (lambda_away**j * math.exp(-lambda_away)) / math.factorial(j)
            row.append(prob_i * prob_j)
        matrix.append(row)
        
    return matrix, round(lambda_home, 2), round(lambda_away, 2)

def generar_pronostico(stats_local, stats_visita):
    matrix, xg_l, xg_v = calculate_poisson_matrix(stats_local, stats_visita)
    
    prob_local = 0.0
    prob_empate = 0.0
    prob_visita = 0.0
    
    exact_scores = []

    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            p = matrix[i][j]
            if i > j:
                prob_local += p
            elif i < j:
                prob_visita += p
            else:
                prob_empate += p
            exact_scores.append((i, j, p))

    # Normalizar porcentajes
    total = prob_local + prob_empate + prob_visita
    if total > 0:
        prob_local = (prob_local / total) * 100
        prob_empate = (prob_empate / total) * 100
        prob_visita = (prob_visita / total) * 100

    # Ordenar marcadores más probables
    exact_scores.sort(key=lambda x: x[2], reverse=True)
    top_scores = exact_scores[:3]

    xg_total = xg_l + xg_v
    ambos_marcan = "Sí" if (xg_l >= 0.95 and xg_v >= 0.95) else "No"
    recomendacion_goles = "Más de 2.5" if xg_total > 2.6 else ("Menos de 2.5" if xg_total < 2.1 else "Línea 1.5 / 2.0")

    return {
        "xg_local": xg_l,
        "xg_visita": xg_v,
        "xg_total": round(xg_total, 2),
        "prob_local": round(prob_local, 1),
        "prob_empate": round(prob_empate, 1),
        "prob_visita": round(prob_visita, 1),
        "ambos_marcan": ambos_marcan,
        "recomendacion_goles": recomendacion_goles,
        "top_scores": top_scores
    }

# ==========================================
# 5. INTERFAZ STREAMLIT DE USUARIO
# ==========================================
db = cargar_base_datos()

liga_seleccionada = st.sidebar.selectbox("⚽ Seleccionar Liga", list(LIGAS_EQUIPOS.keys()), key="select_liga_main")
datos_liga = db[liga_seleccionada]

# Creación de pestañas principales
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Tabla de Posiciones", 
    "⚙️ Carga Directa (Liga Avanzada)", 
    "📝 Registrar Match a Match", 
    "🎯 Analizador de Pronósticos"
])

# --- TAB 1: TABLA DE POSICIONES ---
with tab1:
    st.header(f"Tabla de Posiciones - {liga_seleccionada}")
    
    filtro_vista = st.radio("Vista de Clasificación:", ["General", "Local", "Visitante"], horizontal=True, key="filtro_vista_tab1")
    
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

# --- TAB 2: PESTAÑA PARA CARGA DIRECTA DE LIGAS ADELANTADAS ---
with tab2:
    st.header("⚙️ Ingresar Estadísticas Acumuladas Directas")
    st.info("Utiliza esta sección para poner al día la liga si ya está avanzada, sin tener que meter los partidos pasados uno por uno.")
    
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    equipo_sel = st.selectbox("Selecciona un Equipo a Configurar:", equipos_disponibles, key="select_eq_carga_dir")
    
    datos_actuales = datos_liga["tabla"][equipo_sel]
    
    with st.form(key=f"form_carga_{equipo_sel}"):
        col_loc, col_vis = st.columns(2)
        
        with col_loc:
            st.markdown("### 🏠 Rendimiento en Casa (Local)")
            pg_l = st.number_input("Partidos Ganados (Local)", min_value=0, value=int(datos_actuales["PG_L"]), key=f"pg_l_{equipo_sel}")
            pe_l = st.number_input("Partidos Empatados (Local)", min_value=0, value=int(datos_actuales["PE_L"]), key=f"pe_l_{equipo_sel}")
            pp_l = st.number_input("Partidos Perdidos (Local)", min_value=0, value=int(datos_actuales["PP_L"]), key=f"pp_l_{equipo_sel}")
            gf_l = st.number_input("Goles a Favor (Local)", min_value=0, value=int(datos_actuales["GF_L"]), key=f"gf_l_{equipo_sel}")
            gc_l = st.number_input("Goles en Contra (Local)", min_value=0, value=int(datos_actuales["GC_L"]), key=f"gc_l_{equipo_sel}")
            
        with col_vis:
            st.markdown("### ✈️ Rendimiento Fuera (Visitante)")
            pg_v = st.number_input("Partidos Ganados (Visitante)", min_value=0, value=int(datos_actuales["PG_V"]), key=f"pg_v_{equipo_sel}")
            pe_v = st.number_input("Partidos Empatados (Visitante)", min_value=0, value=int(datos_actuales["PE_V"]), key=f"pe_v_{equipo_sel}")
            pp_v = st.number_input("Partidos Perdidos (Visitante)", min_value=0, value=int(datos_actuales["PP_V"]), key=f"pp_v_{equipo_sel}")
            gf_v = st.number_input("Goles a Favor (Visitante)", min_value=0, value=int(datos_actuales["GF_V"]), key=f"gf_v_{equipo_sel}")
            gc_v = st.number_input("Goles en Contra (Visitante)", min_value=0, value=int(datos_actuales["GC_V"]), key=f"gc_v_{equipo_sel}")
            
        btn_actualizar = st.form_submit_button("💾 Guardar Datos del Equipo", type="primary")
        
        if btn_actualizar:
            pj_l = pg_l + pe_l + pp_l
            pts_l = (pg_l * 3) + pe_l
            dg_l = gf_l - gc_l
            
            pj_v = pg_v + pe_v + pp_v
            pts_v = (pg_v * 3) + pe_v
            dg_v = gf_v - gc_v
            
            pj_tot = pj_l + pj_v
            pg_tot = pg_l + pg_v
            pe_tot = pe_l + pe_v
            pp_tot = pp_l + pp_v
            gf_tot = gf_l + gf_v
            gc_tot = gc_l + gc_v
            dg_tot = gf_tot - gc_tot
            pts_tot = pts_l + pts_v
            
            datos_liga["tabla"][equipo_sel] = {
                "PJ": pj_tot, "PG": pg_tot, "PE": pe_tot, "PP": pp_tot, "GF": gf_tot, "GC": gc_tot, "DG": dg_tot, "Pts": pts_tot,
                "PJ_L": pj_l, "PG_L": pg_l, "PE_L": pe_l, "PP_L": pp_l, "GF_L": gf_l, "GC_L": gc_l, "DG_L": dg_l, "Pts_L": pts_l,
                "PJ_V": pj_v, "PG_V": pg_v, "PE_V": pe_v, "PP_V": pp_v, "GF_V": gf_v, "GC_V": gc_v, "DG_V": dg_v, "Pts_V": pts_v
            }
            
            guardar_base_datos(db)
            st.success(f"¡Estadísticas de **{equipo_sel}** actualizadas correctamente!")
            st.rerun()

# --- TAB 3: REGISTRAR PARTIDO A PARTIDO ---
with tab3:
    st.header("Registrar Partido Individual (Jornada a Jornada)")
    
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    
    with st.form(key="form_registrar_partido_individual"):
        col_l, col_v = st.columns(2)
        with col_l:
            eq_local = st.selectbox("Equipo Local", equipos_disponibles, index=0, key="match_loc_ind")
            goles_local = st.number_input("Goles Local", min_value=0, step=1, value=0, key="m_goles_l_ind")
        with col_v:
            idx_v = 1 if len(equipos_disponibles) > 1 else 0
            eq_visita = st.selectbox("Equipo Visitante", equipos_disponibles, index=idx_v, key="match_vis_ind")
            goles_visita = st.number_input("Goles Visitante", min_value=0, step=1, value=0, key="m_goles_v_ind")
            
        btn_partido = st.form_submit_button("⚽ Guardar Resultado de Match", type="primary")
        
        if btn_partido:
            if eq_local == eq_visita:
                st.error("El equipo local y visitante no pueden ser el mismo.")
            else:
                aplicar_partido_a_tabla(datos_liga["tabla"], eq_local, eq_visita, goles_local, goles_visita)
                reg = {
                    "local": eq_local,
                    "visitante": eq_visita,
                    "goles_local": goles_local,
                    "goles_visita": goles_visita
                }
                datos_liga["historial"].append(reg)
                guardar_base_datos(db)
                st.success(f"Registrado: {eq_local} {goles_local} - {goles_visita} {eq_visita}")
                st.rerun()

    st.markdown("---")
    st.subheader("Historial de Partidos Registrados")
    if datos_liga["historial"]:
        for idx, p in enumerate(reversed(datos_liga["historial"])):
            index_real = len(datos_liga["historial"]) - 1 - idx
            c1, c2 = st.columns([4, 1])
            with c1:
                st.write(f"**{p['local']}** {p['goles_local']} - {p['goles_visita']} **{p['visitante']}**")
            with c2:
                if st.button("Eliminar", key=f"del_partido_{index_real}"):
                    partido_borrar = datos_liga["historial"].pop(index_real)
                    aplicar_partido_a_tabla(
                        datos_liga["tabla"], 
                        partido_borrar["local"], 
                        partido_borrar["visitante"], 
                        partido_borrar["goles_local"], 
                        partido_borrar["goles_visita"], 
                        revertir=True
                    )
                    guardar_base_datos(db)
                    st.rerun()
    else:
        st.info("No hay partidos en el historial registrado uno a uno.")

# --- TAB 4: ANALIZADOR DE PRONÓSTICOS ---
with tab4:
    st.header("Predicción y Métricas del Enfrentamiento (Poisson)")
    
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p_local = st.selectbox("Seleccionar Local", equipos_disponibles, key="p_loc_analisis")
    with col_p2:
        idx_v_p = 1 if len(equipos_disponibles) > 1 else 0
        p_visita = st.selectbox("Seleccionar Visitante", equipos_disponibles, index=idx_v_p, key="p_vis_analisis")

    if p_local == p_visita:
        st.warning("Selecciona dos equipos diferentes para generar el pronóstico.")
    else:
        stats_loc = datos_liga["tabla"][p_local]
        stats_vis = datos_liga["tabla"][p_visita]
        
        pron = generar_pronostico(stats_loc, stats_vis)
        
        st.subheader("📊 Probabilidades del Partido")
        m1, m2, m3 = st.columns(3)
        m1.metric(f"Victoria {p_local}", f"{pron['prob_local']}%")
        m2.metric("Empate", f"{pron['prob_empate']}%")
        m3.metric(f"Victoria {p_visita}", f"{pron['prob_visita']}%")
        
        st.subheader("⚽ Goles Esperados (xG)")
        g1, g2, g3 = st.columns(3)
        g1.metric(f"xG {p_local}", pron['xg_local'])
        g2.metric(f"xG {p_visita}", pron['xg_visita'])
        g3.metric("Expectativa Total", pron['xg_total'])
        
        st.subheader("🎯 Marcadores Exactos Más Probables")
        sc1, sc2, sc3 = st.columns(3)
        top = pron['top_scores']
        if len(top) >= 1:
            sc1.info(f"**1º Opción:** {p_local} {top[0][0]} - {top[0][1]} {p_visita}\n\nProb: {round(top[0][2]*100, 1)}%")
        if len(top) >= 2:
            sc2.info(f"**2º Opción:** {p_local} {top[1][0]} - {top[1][1]} {p_visita}\n\nProb: {round(top[1][2]*100, 1)}%")
        if len(top) >= 3:
            sc3.info(f"**3º Opción:** {p_local} {top[2][0]} - {top[2][1]} {p_visita}\n\nProb: {round(top[2][2]*100, 1)}%")
            
        st.subheader("💡 Recomendaciones de Mercado")
        rec1, rec2 = st.columns(2)
        rec1.success(f"**Línea de Goles:** {pron['recomendacion_goles']}")
        rec2.success(f"**Ambos Anotan (BTTS):** {pron['ambos_marcan']}")
