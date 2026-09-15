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
    page_title="Zohan Pronostic v6 - Auditoría Quirúrgica Total",
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

def calcular_rachas_completas(historial, equipo):
    partidos = []
    for p in historial:
        if p['local'] == equipo:
            res = "G" if p['goles_local'] > p['goles_visita'] else ("E" if p['goles_local'] == p['goles_visita'] else "P")
            partidos.append({"condicion": "Local", "rival": p['visitante'], "res": res, "gf": p['goles_local'], "gc": p['goles_visita']})
        elif p['visitante'] == equipo:
            res = "G" if p['goles_visita'] > p['goles_local'] else ("E" if p['goles_visita'] == p['goles_local'] else "P")
            partidos.append({"condicion": "Visitante", "rival": p['local'], "res": res, "gf": p['goles_visita'], "gc": p['goles_local']})
            
    if not partidos:
        return {"invicto": 0, "sin_ganar": 0, "ultimos": []}
        
    invicto = 0
    for p in reversed(partidos):
        if p['res'] in ["G", "E"]:
            invicto += 1
        else:
            break
            
    sin_ganar = 0
    for p in reversed(partidos):
        if p['res'] in ["E", "P"]:
            sin_ganar += 1
        else:
            break
            
    return {
        "invicto": invicto,
        "sin_ganar": sin_ganar,
        "ultimos": partidos[-5:]
    }

def ejecutar_auditoria_equipo(stats_eq, historial, equipo, tabla_liga):
    pj = max(1, stats_eq["PJ"])
    pg = stats_eq["PG"]
    pe = stats_eq["PE"]
    pp = stats_eq["PP"]
    gf = stats_eq["GF"]
    gc = stats_eq["GC"]
    pts = stats_eq["Pts"]
    
    eficiencia = round((pts / (pj * 3)) * 100, 1) if pj > 0 else 0.0
    prom_gf = round(gf / pj, 2)
    prom_gc = round(gc / pj, 2)
    
    rachas = calcular_rachas_completas(historial, equipo)
    ratio_rendimiento = eficiencia / 100.0
    
    if ratio_rendimiento <= 0.35 or rachas["sin_ganar"] >= 3:
        fibo_estado = "Soporte Crítico (0.382) - Toca Fondo"
        fibo_mensaje = "El equipo ha caído a su zona de soporte profundo. Históricamente, al tocar el nivel 0.382 acumula una presión competitiva extrema, lo que lo vuelve candidato idóneo para un **impulso alcista sorpresivo** en su siguiente encuentro."
    elif ratio_rendimiento >= 0.70:
        fibo_estado = "Zona de Resistencia Alta (0.236)"
        fibo_mensaje = "El equipo opera en la parte alta de la curva. Muestra solidez, pero está expuesto a correcciones de inercia o exceso de confianza si relaja la intensidad defensiva."
    else:
        fibo_estado = "Zona de Transición Neutral"
        fibo_mensaje = "El equipo oscila en un rango de estabilidad media. Su rendimiento depende de los ajustes tácticos por partido."

    lista_ord = sorted(tabla_liga.items(), key=lambda x: (x[1]["Pts"], x[1]["DG"], x[1]["GF"]), reverse=True)
    posicion = len(tabla_liga)
    for idx, (eq, _) in enumerate(lista_ord):
        if eq == equipo:
            posicion = idx + 1
            break

    return {
        "pj": pj, "pg": pg, "pe": pe, "pp": pp, "gf": gf, "gc": gc, "pts": pts,
        "eficiencia": eficiencia,
        "prom_gf": prom_gf,
        "prom_gc": prom_gc,
        "posicion": posicion,
        "rachas": rachas,
        "fibo_estado": fibo_estado,
        "fibo_mensaje": fibo_mensaje
    }

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
    st.info("Radiografía completa de la temporada: evalúa el rendimiento global, contrasta cómo se comporta jugando de local versus de visitante, y analiza su estado de forma e inercia matemática.")
    
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    eq_audit = st.selectbox("Seleccionar Equipo a Examinar:", equipos_disponibles, key="select_audit_eq")
    
    if eq_audit:
        stats_audit = datos_liga["tabla"][eq_audit]
        historial_audit = datos_liga["historial"]
        audit_res = ejecutar_auditoria_equipo(stats_audit, historial_audit, eq_audit, datos_liga["tabla"])
        
        st.markdown("---")
        st.subheader(f"📋 Radiografía Global de Temporada: {eq_audit}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Posición en Liga", f"{audit_res['posicion']}º lugar")
        m2.metric("Eficiencia Total", f"{audit_res['eficiencia']}%")
        m3.metric("Goles Favor (Prom)", f"{audit_res['prom_gf']}")
        m4.metric("Goles Contra (Prom)", f"{audit_res['prom_gc']}")
        
        # --- DESGLOSE CRUZADO: LOCAL VS VISITANTE ---
        st.markdown("---")
        st.subheader("🏠 vs ✈️ Comportamiento Cruzado (Casa y Fuera)")
        
        col_l_audit, col_v_audit = st.columns(2)
        
        with col_l_audit:
            st.markdown(f"#### 🏠 Rendimiento en Casa (Local)")
            pj_l = stats_audit["PJ_L"]
            pts_l = stats_audit["Pts_L"]
            ef_l = round((pts_l / (pj_l * 3)) * 100, 1) if pj_l > 0 else 0.0
            st.write(f"- **Partidos Jugados:** `{pj_l}`")
            st.write(f"- **Pts / G - E - P:** `{pts_l} pts` ({stats_audit['PG_L']}G - {stats_audit['PE_L']}E - {stats_audit['PP_L']}P)")
            st.write(f"- **Goles (F / C / DG):** `{stats_audit['GF_L']} GF` / `{stats_audit['GC_L']} GC` (DG: `{stats_audit['DG_L']}`)")
            st.metric("Eficiencia Local", f"{ef_l}%")
            
        with col_v_audit:
            st.markdown(f"#### ✈️ Rendimiento de Visitante (Fuera)")
            pj_v = stats_audit["PJ_V"]
            pts_v = stats_audit["Pts_V"]
            ef_v = round((pts_v / (pj_v * 3)) * 100, 1) if pj_v > 0 else 0.0
            st.write(f"- **Partidos Jugados:** `{pj_v}`")
            st.write(f"- **Pts / G - E - P:** `{pts_v} pts` ({stats_audit['PG_V']}G - {stats_audit['PE_V']}E - {stats_audit['PP_V']}P)")
            st.write(f"- **Goles (F / C / DG):** `{stats_audit['GF_V']} GF` / `{stats_audit['GC_V']} GC` (DG: `{stats_audit['DG_V']}`)")
            st.metric("Eficiencia Visitante", f"{ef_v}%")

        st.markdown("---")
        st.subheader("📈 Ciclo de Fibonacci y Estado de Inercia")
        st.markdown(f"**Estado del Ciclo:** `{audit_res['fibo_estado']}`")
        st.info(audit_res['fibo_mensaje'])
        
        st.markdown("---")
        st.subheader("📊 Historial de Rachas Puras")
        rc1, rc2 = st.columns(2)
        rc1.write(f"- **Racha Actual Invicto (Sin Perder):** `{audit_res['rachas']['invicto']} partidos`")
        rc2.write(f"- **Racha Actual Sequía (Sin Ganar):** `{audit_res['rachas']['sin_ganar']} partidos`")
        
        if audit_res['rachas']['ultimos']:
            st.markdown("**Últimos 5 encuentros registrados del equipo:**")
            df_ultimos = pd.DataFrame(audit_res['rachas']['ultimos'])
            df_ultimos.columns = ["Condición", "Rival", "Resultado", "GF", "GC"]
            st.dataframe(df_ultimos, use_container_width=True, hide_index=True)
        else:
            st.warning("No hay suficientes partidos registrados en el historial para mostrar el desglose.")

# --- TAB 5: ANALIZADOR QUIRÚRGICO ELITE (DOBLE CARRIL) ---
with tab5:
    st.header(f"🎯 Analizador Quirúrgico Elite - Doble Carril ({liga_sel})")
    st.info("Arquitectura de Doble Carril: **Carril Normal** (análisis estadístico sobrio y fiable para la mayoría de partidos) y **Carril Francotirador** (Alerta Roja exclusiva de alta exigencia para anomalías de valor).")
    
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    cp1, cp2 = st.columns(2)
    with cp1:
        p_local = st.selectbox("Equipo Local", equipos_disponibles, key="sync_loc")
    with cp2:
        p_visita = st.selectbox("Equipo Visitante", equipos_disponibles, index=1 if len(equipos_disponibles)>1 else 0, key="sync_vis")

    if p_local == p_visita:
        st.warning("⚠️ Selecciona dos equipos diferentes para realizar el análisis cruzado.")
    else:
        if st.button("🔥 Ejecutar Análisis de Doble Carril", type="primary"):
            stats_l = datos_liga["tabla"][p_local]
            stats_v = datos_liga["tabla"][p_visita]
            
            pj_l = max(1, stats_l["PJ"])
            pj_v = max(1, stats_v["PJ"])
            
            # Promedios de goles reales
            gf_l_prom = stats_l["GF"] / pj_l
            gc_l_prom = stats_l["GC"] / pj_l
            gf_v_prom = stats_v["GF"] / pj_v
            gc_v_prom = stats_v["GC"] / pj_v
            
            # Tasas de Poisson (lambda)
            lambda_local = (gf_l_prom + gc_v_prom) / 2
            lambda_visita = (gf_v_prom + gc_l_prom) / 2
            
            # Matriz de probabilidad (0 a 5 goles)
            matriz_prob = np.outer(
                [poisson.pmf(i, lambda_local) for i in range(6)],
                [poisson.pmf(j, lambda_visita) for j in range(6)]
            )
            
            prob_local = np.sum(np.tril(matriz_prob, -1)) * 100
            prob_empate = np.sum(np.diagonal(matriz_prob)) * 100
            prob_visita = np.sum(np.triu(matriz_prob, 1)) * 100
            
            # ----------------------------------------------------
            # CARRIL 1: MODO NORMAL (Análisis base sobrio y directo)
            # ----------------------------------------------------
            st.markdown("---")
            st.subheader("📊 Carril 1: Diagnóstico Estadístico (Modo Normal)")
            col_r1, col_r2, col_r3 = st.columns(3)
            col_r1.metric(f"Victoria {p_local}", f"{prob_local:.1f}%")
            col_r2.metric("Empate Técnico", f"{prob_empate:.1f}%")
            col_r3.metric(f"Victoria {p_visita}", f"{prob_visita:.1f}%")
            
            if prob_local > prob_visita and prob_local > prob_empate:
                veredicto_normal = f"Tendencia lógica favorable al local (**{p_local}**). Comportamiento de mercado estándar."
            elif prob_visita > prob_local and prob_visita > prob_empate:
                veredicto_normal = f"Tendencia favorable al visitante (**{p_visita}**). Resistencia visitante identificada."
            else:
                veredicto_normal = "Tendencia a paridad o partido cerrado de alta fricción táctica."
            
            st.info(f"💡 **Lectura Base:** {veredicto_normal}")
            
            # ----------------------------------------------------
            # CARRIL 2: MODO FRANCOTIRADOR (Alerta Roja Ultra-Exclusiva)
            # ----------------------------------------------------
            st.markdown("---")
            st.subheader("🚨 Carril 2: Radar de Alerta Roja (Modo Francotirador)")
            
            UMBRAL_FRANCOTIRADOR = 78.0
            UMBRAL_VISITANTE_ELITE = 70.0
            
            if prob_local >= UMBRAL_FRANCOTIRADOR:
                st.error(
                    f"🎯 **¡ALERTA ROJA DE FRANCOTIRADOR ACTIVADA (CARRIL 2)!**\n\n"
                    f"* **Objetivo de Oro:** Victoria aplastante de **{p_local}** con un nivel de confianza matemático del **{prob_local:.1f}%**.\n"
                    f"* **Veredicto de Élite:** Supera el filtro estricto de inercia y solidez. Inclusión obligatoria en tu combinada alta."
                )
            elif prob_visita >= UMBRAL_VISITANTE_ELITE:
                st.error(
                    f"🎯 **¡ALERTA ROJA DE FRANCOTIRADOR ACTIVADA (CARRIL 2)!**\n\n"
                    f"* **Objetivo de Oro:** Asalto táctico de **{p_visita}** con un {prob_visita:.1f}% de probabilidad.\n"
                    f"* **Veredicto de Élite:** Anomalía de valor detectada en la defensa rival. Cuota de alta rentabilidad lista para cazar."
                )
            else:
                st.success(
                    f"🛡️ **Carril Normal Activo — Sin Alerta Roja**\n\n"
                    f"* El partido no alcanza el umbral de exigencia extrema ({UMBRAL_FRANCOTIRADOR}%+). El sistema opera de forma sobria, protegiendo tu bankroll de falsas alarmas. Partido apto para análisis tradicional."
                )

