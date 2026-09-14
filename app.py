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
    page_title="Zohan Pronostic v4 - Top 5 Marcadores Claros",
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
# 2. GESTIÓN DE BASE DE DATOS Y TXT
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
# 3. MOTOR INTELIGENTE Y TOP 5 MARCADORES
# ==========================================
def calcular_forma_reciente_equipo(historial, equipo, n=5):
    partidos_local = [p for p in historial if p['local'] == equipo]
    partidos_visita = [p for p in historial if p['visitante'] == equipo]
    
    ult_l = partidos_local[-n:] if len(partidos_local) >= n else partidos_local
    gf_l_rec = sum(p['goles_local'] for p in ult_l) / max(1, len(ult_l))
    gc_l_rec = sum(p['goles_visita'] for p in ult_l) / max(1, len(ult_l))
    
    ult_v = partidos_visita[-n:] if len(partidos_visita) >= n else partidos_visita
    gf_v_rec = sum(p['goles_visita'] for p in ult_v) / max(1, len(ult_v))
    gc_v_rec = sum(p['goles_local'] for p in ult_v) / max(1, len(ult_v))
    
    return {
        "gf_l_rec": gf_l_rec, "gc_l_rec": gc_l_rec,
        "gf_v_rec": gf_v_rec, "gc_v_rec": gc_v_rec
    }

def np_poisson_sim(lmbda):
    L = math.exp(-lmbda)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

def motor_analisis_inteligente(stats_local, stats_visita, historial, p_local, p_visita, iteraciones_mc=10000):
    pj_l = max(1, stats_local["PJ_L"])
    pj_v = max(1, stats_visita["PJ_V"])
    
    gf_l_casa_base = stats_local["GF_L"] / pj_l
    gc_l_casa_base = stats_local["GC_L"] / pj_l
    gf_v_fuera_base = stats_visita["GF_V"] / pj_v
    gc_v_fuera_base = stats_visita["GC_V"] / pj_v

    forma_l = calcular_forma_reciente_equipo(historial, p_local, n=5)
    forma_v = calcular_forma_reciente_equipo(historial, p_visita, n=5)

    gf_l_efectivo = (gf_l_casa_base * 0.7) + (forma_l["gf_l_rec"] * 0.3)
    gc_l_efectivo = (gc_l_casa_base * 0.7) + (forma_l["gc_l_rec"] * 0.3)
    gf_v_efectivo = (gf_v_fuera_base * 0.7) + (forma_v["gf_v_rec"] * 0.3)
    gc_v_efectivo = (gc_v_fuera_base * 0.7) + (forma_v["gc_v_rec"] * 0.3)

    lambda_h_base = (gf_l_efectivo + gc_v_efectivo) / 2
    lambda_a_base = (gf_v_efectivo + gc_l_efectivo) / 2

    fib_236 = 0.236
    fib_382 = 0.382

    factor_ajuste_h = 1 + (fib_236 if gf_l_efectivo > gc_v_efectivo else -fib_382)
    factor_ajuste_a = 1 + (fib_236 if gf_v_efectivo > gc_l_efectivo else -fib_382)

    lambda_home_sync = max(0.2, lambda_h_base * factor_ajuste_h)
    lambda_away_sync = max(0.2, lambda_a_base * factor_ajuste_a)

    xg_total = round(lambda_home_sync + lambda_away_sync, 2)
    umbral_fibonacci = round(xg_total * (1 + fib_382), 2)

    wins_l, wins_v, draws = 0, 0, 0
    conteo_scores = {}

    for _ in range(iteraciones_mc):
        gh = np_poisson_sim(lambda_home_sync)
        ga = np_poisson_sim(lambda_away_sync)

        if gh > ga:
            wins_l += 1
        elif gh < ga:
            wins_v += 1
        else:
            draws += 1

        sc_key = (gh, ga)
        conteo_scores[sc_key] = conteo_scores.get(sc_key, 0) + 1

    p_local_pct = (wins_l / iteraciones_mc) * 100
    p_empate_pct = (draws / iteraciones_mc) * 100
    p_visita_pct = (wins_v / iteraciones_mc) * 100

    cuota_l = round(100 / max(0.1, p_local_pct), 2)
    cuota_e = round(100 / max(0.1, p_empate_pct), 2)
    cuota_v = round(100 / max(0.1, p_visita_pct), 2)

    # Extracción de los TOP 5 marcadores exactos
    sorted_scores = sorted(conteo_scores.items(), key=lambda x: x[1], reverse=True)
    top_scores = [(s[0][0], s[0][1], (s[1] / iteraciones_mc) * 100) for s in sorted_scores[:5]]

    ambos_marcan = "Sí" if (lambda_home_sync >= 0.95 and lambda_away_sync >= 0.95) else "No"
    rec_goles = "Más de 2.5" if xg_total > 2.55 else ("Menos de 2.5" if xg_total < 2.05 else "Línea 1.5 / 2.0")

    return {
        "xg_local": round(lambda_home_sync, 2),
        "xg_visita": round(lambda_away_sync, 2),
        "xg_total": xg_total,
        "umbral_fibonacci": umbral_fibonacci,
        "p_local": round(p_local_pct, 1),
        "p_empate": round(p_empate_pct, 1),
        "p_visita": round(p_visita_pct, 1),
        "cuota_l": cuota_l,
        "cuota_e": cuota_e,
        "cuota_v": cuota_v,
        "top_scores": top_scores,
        "ambos_marcan": ambos_marcan,
        "rec_goles": rec_goles
    }

# ==========================================
# 4. INTERFAZ STREAMLIT
# ==========================================
db = cargar_base_datos()

liga_sel = st.sidebar.selectbox("⚽ Seleccionar Liga", list(LIGAS_EQUIPOS.keys()), key="select_liga_main")
datos_liga = db[liga_sel]

# Respaldo TXT
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

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Tabla de Posiciones", 
    "⚙️ Carga Directa Avanzada (Tabla)", 
    "📝 Registrar Partido", 
    "🎯 Analizador Inteligente"
])

# --- TAB 1: TABLA CON BOTONES DE FACETA ---
with tab1:
    st.header(f"Tabla de Posiciones - {liga_sel}")
    st.markdown("Selecciona la faceta que deseas visualizar en la tabla:")
    
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
    st.markdown(f"**Visualizando Clasificación:** `{filtro_vista}`")

    df_tabla = pd.DataFrame.from_dict(datos_liga["tabla"], orient="index")
    if filtro_vista == "General":
        cols = ["PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]
    elif filtro_vista == "Local":
        cols = ["PJ_L", "PG_L", "PE_L", "PP_L", "GF_L", "GC_L", "DG_L", "Pts_L"]
    else:
        cols = ["PJ_V", "PG_V", "PE_V", "PP_V", "GF_V", "GC_V", "DG_V", "Pts_V"]

    df_v = df_tabla[cols].copy()
    df_v.columns = ["PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]
    df_v = df_v.sort_values(by=["Pts", "DG", "GF"], ascending=False)
    st.dataframe(df_v, use_container_width=True)

# --- TAB 2: CARGA DIRECTA AVANZADA ---
with tab2:
    st.header("⚙️ Carga Directa Avanzada por Equipo")
    st.info("Introduce de forma detallada el desglose completo en casa y fuera de casa para alimentar los cálculos con máxima precisión.")
    
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    eq_target = st.selectbox("Seleccionar Equipo a Configurar:", equipos_disponibles, key="eq_avanzado")
    dt_eq = datos_liga["tabla"][eq_target]
    
    with st.form(key=f"form_avanzado_{eq_target}"):
        col_l, col_v = st.columns(2)
        
        with col_l:
            st.markdown("### 🏠 Rendimiento Local (Casa)")
            pj_l = st.number_input("Partidos Jugados (Local)", min_value=0, value=int(dt_eq["PJ_L"]))
            pg_l = st.number_input("Ganados (Local)", min_value=0, value=int(dt_eq["PG_L"]))
            pe_l = st.number_input("Empatados (Local)", min_value=0, value=int(dt_eq["PE_L"]))
            pp_l = st.number_input("Perdidos (Local)", min_value=0, value=int(dt_eq["PP_L"]))
            gf_l = st.number_input("Goles a Favor (Local)", min_value=0, value=int(dt_eq["GF_L"]))
            gc_l = st.number_input("Goles en Contra (Local)", min_value=0, value=int(dt_eq["GC_L"]))
            
        with col_v:
            st.markdown("### ✈️ Rendimiento Visitante (Fuera)")
            pj_v = st.number_input("Partidos Jugados (Visitante)", min_value=0, value=int(dt_eq["PJ_V"]))
            pg_v = st.number_input("Ganados (Visitante)", min_value=0, value=int(dt_eq["PG_V"]))
            pe_v = st.number_input("Empatados (Visitante)", min_value=0, value=int(dt_eq["PE_V"]))
            pp_v = st.number_input("Perdidos (Visitante)", min_value=0, value=int(dt_eq["PP_V"]))
            gf_v = st.number_input("Goles a Favor (Visitante)", min_value=0, value=int(dt_eq["GF_V"]))
            gc_v = st.number_input("Goles en Contra (Visitante)", min_value=0, value=int(dt_eq["GC_V"]))
            
        btn_guardar_avanzado = st.form_submit_button("💾 Actualizar Perfil Completo del Equipo", type="primary")
        
        if btn_guardar_avanzado:
            pts_l = (pg_l * 3) + pe_l
            dg_l = gf_l - gc_l
            pts_v = (pg_v * 3) + pe_v
            dg_v = gf_v - gc_v
            
            datos_liga["tabla"][eq_target] = {
                "PJ": pj_l + pj_v, "PG": pg_l + pg_v, "PE": pe_l + pe_v, "PP": pp_l + pp_v,
                "GF": gf_l + gf_v, "GC": gc_l + gc_v, "DG": dg_l + dg_v, "Pts": pts_l + pts_v,
                "PJ_L": pj_l, "PG_L": pg_l, "PE_L": pe_l, "PP_L": pp_l, "GF_L": gf_l, "GC_L": gc_l, "DG_L": dg_l, "Pts_L": pts_l,
                "PJ_V": pj_v, "PG_V": pg_v, "PE_V": pe_v, "PP_V": pp_v, "GF_V": gf_v, "GC_V": gc_v, "DG_V": dg_v, "Pts_V": pts_v
            }
            guardar_base_datos(db)
            st.success(f"¡Perfil estadístico avanzado de **{eq_target}** guardado con éxito!")
            st.rerun()

# --- TAB 3: REGISTRO PARTIDO ---
with tab3:
    st.header("Registrar Partido (Impacto en Tabla e Historial)")
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    
    with st.form(key="form_match_sync"):
        c1, c2 = st.columns(2)
        with c1:
            eq_l = st.selectbox("Local", equipos_disponibles, index=0)
            gl = st.number_input("Goles Local", min_value=0, step=1, value=0)
        with c2:
            eq_v = st.selectbox("Visitante", equipos_disponibles, index=1 if len(equipos_disponibles)>1 else 0)
            gv = st.number_input("Goles Visitante", min_value=0, step=1, value=0)
            
        if st.form_submit_button("⚽ Registrar y Sincronizar Sistema", type="primary"):
            if eq_l == eq_v:
                st.error("El local y visitante no pueden ser el mismo equipo.")
            else:
                aplicar_partido_a_tabla(datos_liga["tabla"], eq_l, eq_v, gl, gv)
                datos_liga["historial"].append({"local": eq_l, "visitante": eq_v, "goles_local": gl, "goles_visita": gv})
                guardar_base_datos(db)
                st.success("¡Partido registrado y analizado por el modelo inteligente!")
                st.rerun()

    st.markdown("---")
    st.subheader("Historial Registrado")
    if datos_liga["historial"]:
        for idx, p in enumerate(reversed(datos_liga["historial"])):
            idx_r = len(datos_liga["historial"]) - 1 - idx
            ch1, ch2 = st.columns([4, 1])
            with ch1:
                st.write(f"**{p['local']}** {p['goles_local']} - {p['goles_visita']} **{p['visitante']}**")
            with ch2:
                if st.button("Eliminar", key=f"del_sync_{idx_r}"):
                    pb = datos_liga["historial"].pop(idx_r)
                    aplicar_partido_a_tabla(datos_liga["tabla"], pb["local"], pb["visitante"], pb["goles_local"], pb["goles_visita"], revertir=True)
                    guardar_base_datos(db)
                    st.rerun()

# --- TAB 4: ANALIZADOR INTELIGENTE (CON TOP 5 MARCADORES CLAROS) ---
with tab4:
    st.header("🎯 Analizador Inteligente Unificado (Forma + Poisson + Montecarlo + Fibonacci)")
    st.info("Este motor combina las estadísticas globales de la tabla con la inercia reciente de los últimos partidos, filtrando con Fibonacci y simulando 10,000 escenarios.")
    
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    cp1, cp2 = st.columns(2)
    with cp1:
        p_local = st.selectbox("Local", equipos_disponibles, key="sync_loc")
    with cp2:
        p_visita = st.selectbox("Visitante", equipos_disponibles, index=1 if len(equipos_disponibles)>1 else 0, key="sync_vis")

    if p_local == p_visita:
        st.warning("Selecciona dos equipos diferentes.")
    else:
        stats_l = datos_liga["tabla"][p_local]
        stats_v = datos_liga["tabla"][p_visita]
        historial = datos_liga["historial"]
        
        res = motor_analisis_inteligente(stats_l, stats_v, historial, p_local, p_visita)
        
        st.markdown("---")
        st.subheader("📊 Probabilidades Unificadas y Cuotas Justas (Montecarlo 10k)")
        r1, r2, r3 = st.columns(3)
        r1.metric(f"Victoria {p_local}", f"{res['p_local']}%", f"Cuota Justa: {res['cuota_l']}")
        r2.metric("Empate", f"{res['p_empate']}%", f"Cuota Justa: {res['cuota_e']}")
        r3.metric(f"Victoria {p_visita}", f"{res['p_visita']}%", f"Cuota Justa: {res['cuota_v']}")
        
        st.markdown("---")
        st.subheader("⚽ Goles Esperados (xG Inteligente) & Filtro de Volatilidad Fibonacci")
        xg1, xg2, xg3, xg4 = st.columns(4)
        xg1.metric("xG Local (Forma)", res['xg_local'])
        xg2.metric("xG Visitante (Forma)", res['xg_visita'])
        xg3.metric("xG Total Sincronizado", res['xg_total'])
        xg4.metric("Umbral Fibonacci (38.2%)", res['umbral_fibonacci'])
        
        st.markdown("---")
        st.subheader("🎯 Top 5 Marcadores Exactos Más Probables")
        st.markdown("Clasificación estocástica de los 5 resultados más recurrentes según la simulación conjunta:")
        
        # Construcción de tabla clara y limpia para los Top 5
        top_data = []
        for i, (gl_val, gv_val, prob_val) in enumerate(res['top_scores']):
            top_data.append({
                "Ranking": f"#{i+1}",
                "Marcador Exacto": f"{p_local} {int(gl_val)} - {int(gv_val)} {p_visita}",
                "Probabilidad Estocástica": f"{round(prob_val, 2)}%"
            })
        
        df_top5 = pd.DataFrame(top_data)
        st.dataframe(df_top5, use_container_width=True, hide_index=True)
            
        st.markdown("---")
        st.subheader("💡 Consenso de Mercado y Recomendaciones")
        m_rec1, m_rec2 = st.columns(2)
        m_rec1.success(f"**Línea de Goles:** {res['rec_goles']}")
        m_rec2.success(f"**Ambos Anotan (BTTS):** {res['ambos_marcan']}")

