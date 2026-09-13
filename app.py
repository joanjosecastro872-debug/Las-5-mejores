import streamlit as st
import json
import os
import numpy as np
import pandas as pd

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
    .horizontal-scroll {
        display: flex;
        overflow-x: auto;
        white-space: nowrap;
        padding: 10px 0;
        gap: 15px;
        -webkit-overflow-scrolling: touch;
    }
    .horizontal-card {
        min-width: 250px;
        max-width: 300px;
        background-color: #1E293B;
        color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        display: inline-block;
    }
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

# Listas Oficiales Verificadas
LIGAS_EQUIPOS = {
    "🇪🇸 LaLiga": [
        "Athletic Club", "Atlético de Madrid", "CA Osasuna", "Celta de Vigo", 
        "Deportivo Alavés", "Deportivo de La Coruña", "Elche CF", "FC Barcelona", 
        "Getafe CF", "Girona FC", "Levante UD", "Málaga CF", 
        "Racing de Santander", "Rayo Vallecano", "RCD Espanyol", "Real Betis", 
        "Real Madrid", "Real Sociedad", "Sevilla FC", "Valencia CF"
    ],
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": [
        "AFC Bournemouth", "Arsenal FC", "Aston Villa", "Brentford FC", 
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
        "Bologna FC", "Cagliari Calcio", "Como 1907", "Cremonese", 
        "Fiorentina", "Frosinone Calcio", "Genoa CFC", "Inter de Milán", 
        "Juventus", "Parma Calcio", "Sassuolo", "SS Lazio", 
        "SSC Napoli", "Torino FC", "Udinese Calcio", "US Lecce"
    ],
    "🇩🇪 Bundesliga": [
        "1. FC Colonia", "1. FC Union Berlin", "1. FSV Mainz 05", "Bayer 04 Leverkusen", 
        "Bayern Múnich", "Borussia Dortmund", "Borussia Mönchengladbach", "Eintracht Frankfurt", 
        "FC Augsburg", "FC St. Pauli", "Hamburger SV", "RB Leipzig", 
        "SC Friburgo", "Schalke 04", "SV Elversberg", "SV Werder Bremen", 
        "TSG Hoffenheim", "VfB Stuttgart"
    ],
    "🇫🇷 Ligue 1": [
        "AJ Auxerre", "Angers SCO", "AS Mónaco", "ESTAC Troyes", 
        "FC Lorient", "HAC Le Havre", "Le Mans FC", "LOSC Lille", 
        "OGC Niza", "Olympique de Lyon", "Olympique de Marsella", "Paris FC", 
        "Paris Saint-Germain", "RC Estrasburgo", "RC Lens", "Stade Brestois 29", 
        "Stade Rennais", "Toulouse FC"
    ]
}

# ==========================================
# 2. BASE DE DATOS Y MEMORIA JSON BLINDADA
# ==========================================
def obtener_estructura_equipo():
    return {
        "PJ": 0, "PG": 0, "PE": 0, "PP": 0, "GF": 0, "GC": 0, "DG": 0, "Pts": 0,
        "PJ_L": 0, "PG_L": 0, "PE_L": 0, "PP_L": 0, "GF_L": 0, "GC_L": 0, "DG_L": 0, "Pts_L": 0,
        "PJ_V": 0, "PG_V": 0, "PE_V": 0, "PP_V": 0, "GF_V": 0, "GC_V": 0, "DG_V": 0, "Pts_V": 0,
        "Racha": []
    }

def inicializar_liga_vacia(equipos):
    tabla = {}
    for eq in equipos:
        tabla[eq] = obtener_estructura_equipo()
    return {"tabla": tabla, "historial": []}

def cargar_base_datos():
    keys_requeridas = obtener_estructura_equipo()
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for liga in LIGAS_EQUIPOS.keys():
                    if liga not in data:
                        data[liga] = inicializar_liga_vacia(LIGAS_EQUIPOS[liga])
                    else:
                        if "tabla" not in data[liga]:
                            data[liga]["tabla"] = {}
                        if "historial" not in data[liga]:
                            data[liga]["historial"] = []
                            
                        for eq in LIGAS_EQUIPOS[liga]:
                            if eq not in data[liga]["tabla"]:
                                data[liga]["tabla"][eq] = keys_requeridas.copy()
                            else:
                                for k, v in keys_requeridas.items():
                                    if k not in data[liga]["tabla"][eq]:
                                        data[liga]["tabla"][eq][k] = v
                return data
        except Exception:
            pass
    
    db = {}
    for liga, equipos in LIGAS_EQUIPOS.items():
        db[liga] = inicializar_liga_vacia(equipos)
    return db

def guardar_base_datos(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db_data = cargar_base_datos()

# ==========================================
# 3. INTERFAZ Y NAVEGACIÓN PRINCIPAL
# ==========================================
st.sidebar.title("⚙️ Zohan Panel")
liga_seleccionada = st.sidebar.selectbox("Selecciona la Liga", list(LIGAS_EQUIPOS.keys()))

# --- BOTONES DE RESETEO EN LA BARRA LATERAL ---
st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Reiniciar Liga Actual a Ceros"):
    db_data[liga_seleccionada] = inicializar_liga_vacia(LIGAS_EQUIPOS[liga_seleccionada])
    guardar_base_datos(db_data)
    st.sidebar.success(f"¡Datos de {liga_seleccionada} borrados!")
    st.rerun()

if st.sidebar.button("🔥 Reiniciar TODAS las Ligas"):
    for l in LIGAS_EQUIPOS.keys():
        db_data[l] = inicializar_liga_vacia(LIGAS_EQUIPOS[l])
    guardar_base_datos(db_data)
    st.sidebar.success("¡Todas las ligas en ceros!")
    st.rerun()

equipos_liga = LIGAS_EQUIPOS[liga_seleccionada]
tabla_actual = db_data[liga_seleccionada]["tabla"]

st.title(f"⚽ Zohan Pronostic v2 - {liga_seleccionada}")

tab_sim, tab_reg_directo, tab_tabla, tab_hist = st.tabs([
    "🔮 Simular Partido", 
    "📝 Registro Directo Equipo", 
    "📊 Tabla de Posiciones", 
    "📜 Historial"
])

# --- PESTAÑA 1: SIMULAR PARTIDO ---
with tab_sim:
    st.subheader("Simulador de Enfrentamiento (Partido Individual)")
    with st.form("form_simulacion"):
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Equipo Local", equipos_liga, index=0)
        with col2:
            visitante = st.selectbox("Equipo Visitante", equipos_liga, index=1 if len(equipos_liga) > 1 else 0)
        
        btn_simular = st.form_submit_button("Simular y Guardar Encuentro")

    if btn_simular:
        if local == visitante:
            st.warning("⚠️ El equipo local y visitante no pueden ser el mismo.")
        else:
            np.random.seed()
            goles_local = np.random.poisson(1.5)
            goles_visitante = np.random.poisson(1.1)
            
            st.success(f"Resultado Simulado: **{local} {goles_local} - {goles_visitante} {visitante}**")
            
            # Actualizar estadísticas Local
            t_loc = tabla_actual[local]
            t_loc["PJ_L"] += 1
            t_loc["GF_L"] += goles_local
            t_loc["GC_L"] += goles_visitante
            t_loc["DG_L"] = t_loc["GF_L"] - t_loc["GC_L"]

            # Actualizar estadísticas Visitante
            t_vis = tabla_actual[visitante]
            t_vis["PJ_V"] += 1
            t_vis["GF_V"] += goles_visitante
            t_vis["GC_V"] += goles_local
            t_vis["DG_V"] = t_vis["GF_V"] - t_vis["GC_V"]
            
            if goles_local > goles_visitante:
                t_loc["PG_L"] += 1
                t_loc["Pts_L"] += 3
                t_vis["PP_V"] += 1
                res_str = "Victoria Local"
            elif goles_local < goles_visitante:
                t_vis["PG_V"] += 1
                t_vis["Pts_V"] += 3
                t_loc["PP_L"] += 1
                res_str = "Victoria Visitante"
            else:
                t_loc["PE_L"] += 1
                t_loc["Pts_L"] += 1
                t_vis["PE_V"] += 1
                t_vis["Pts_V"] += 1
                res_str = "Empate"

            # Recalcular totales generales
            for eq_key in [local, visitante]:
                e = tabla_actual[eq_key]
                e["PJ"] = e["PJ_L"] + e["PJ_V"]
                e["PG"] = e["PG_L"] + e["PG_V"]
                e["PE"] = e["PE_L"] + e["PE_V"]
                e["PP"] = e["PP_L"] + e["PP_V"]
                e["GF"] = e["GF_L"] + e["GF_V"]
                e["GC"] = e["GC_L"] + e["GC_V"]
                e["DG"] = e["GF"] - e["GC"]
                e["Pts"] = e["Pts_L"] + e["Pts_V"]

            # Registrar en historial
            db_data[liga_seleccionada]["historial"].insert(0, {
                "local": local,
                "visitante": visitante,
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "resultado": res_str
            })
            
            guardar_base_datos(db_data)
            st.rerun()

# --- PESTAÑA 2: REGISTRO DIRECTO DE EQUIPO (LOCAL Y VISITANTE) ---
with tab_reg_directo:
    st.subheader("Registro Directo / Actualización de Equipo")
    st.info("Ingresa los acumulados reales de la temporada divididos por condición (Local y Visitante).")

    with st.form("form_registro_directo"):
        equipo_sel = st.selectbox("Selecciona el Equipo a Actualizar", equipos_liga)
        
        st.markdown("---")
        st.markdown("### 🏠 Rendimiento como LOCAL")
        col_l1, col_l2, col_l3 = st.columns(3)
        with col_l1:
            pj_l = st.number_input("PJ Local", min_value=0, value=int(tabla_actual[equipo_sel].get("PJ_L", 0)), step=1)
            pg_l = st.number_input("PG Local", min_value=0, value=int(tabla_actual[equipo_sel].get("PG_L", 0)), step=1)
        with col_l2:
            pe_l = st.number_input("PE Local", min_value=0, value=int(tabla_actual[equipo_sel].get("PE_L", 0)), step=1)
            pp_l = st.number_input("PP Local", min_value=0, value=int(tabla_actual[equipo_sel].get("PP_L", 0)), step=1)
        with col_l3:
            gf_l = st.number_input("GF Local", min_value=0, value=int(tabla_actual[equipo_sel].get("GF_L", 0)), step=1)
            gc_l = st.number_input("GC Local", min_value=0, value=int(tabla_actual[equipo_sel]["GC_L"], 0), step=1)

        st.markdown("---")
        st.markdown("### ✈️ Rendimiento como VISITANTE")
        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            pj_v = st.number_input("PJ Visitante", min_value=0, value=int(tabla_actual[equipo_sel].get("PJ_V", 0)), step=1)
            pg_v = st.number_input("PG Visitante", min_value=0, value=int(tabla_actual[equipo_sel].get("PG_V", 0)), step=1)
        with col_v2:
            pe_v = st.number_input("PE Visitante", min_value=0, value=int(tabla_actual[equipo_sel].get("PE_V", 0)), step=1)
            pp_v = st.number_input("PP Visitante", min_value=0, value=int(tabla_actual[equipo_sel].get("PP_V", 0)), step=1)
        with col_v3:
            gf_v = st.number_input("GF Visitante", min_value=0, value=int(tabla_actual[equipo_sel].get("GF_V", 0)), step=1)
            gc_v = st.number_input("GC Visitante", min_value=0, value=int(tabla_actual[equipo_sel].get("GC_V", 0)), step=1)

        btn_guardar_directo = st.form_submit_button("Guardar Estadísticas del Equipo")

    if btn_guardar_directo:
        eq_data = tabla_actual[equipo_sel]
        
        # Asignar Local
        eq_data["PJ_L"] = pj_l
        eq_data["PG_L"] = pg_l
        eq_data["PE_L"] = pe_l
        eq_data["PP_L"] = pp_l
        eq_data["GF_L"] = gf_l
        eq_data["GC_L"] = gc_l
        eq_data["DG_L"] = gf_l - gc_l
        eq_data["Pts_L"] = (pg_l * 3) + (pe_l * 1)

        # Asignar Visitante
        eq_data["PJ_V"] = pj_v
        eq_data["PG_V"] = pg_v
        eq_data["PE_V"] = pe_v
        eq_data["PP_V"] = pp_v
        eq_data["GF_V"] = gf_v
        eq_data["GC_V"] = gc_v
        eq_data["DG_V"] = gf_v - gc_v
        eq_data["Pts_V"] = (pg_v * 3) + (pe_v * 1)

        # Calcular Totales Generales Automáticos
        eq_data["PJ"] = pj_l + pj_v
        eq_data["PG"] = pg_l + pg_v
        eq_data["PE"] = pe_l + pe_v
        eq_data["PP"] = pp_l + pp_v
        eq_data["GF"] = gf_l + gf_v
        eq_data["GC"] = gc_l + gc_v
        eq_data["DG"] = eq_data["GF"] - eq_data["GC"]
        eq_data["Pts"] = eq_data["Pts_L"] + eq_data["Pts_V"]

        guardar_base_datos(db_data)
        st.success(f"✅ ¡Estadísticas de **{equipo_sel}** actualizadas con éxito!")
        st.rerun()

# --- PESTAÑA 3: TABLA DE POSICIONES (GENERAL, LOCAL, VISITANTE) ---
with tab_tabla:
    st.subheader("Clasificación de la Liga")
    
    tipo_tabla = st.radio(
        "Ver tabla por:",
        ["🌐 General", "🏠 Solo Local", "✈️ Solo Visitante"],
        horizontal=True
    )
    
    lista_tabla = []
    for eq, stats in tabla_actual.items():
        row = {"Equipo": eq}
        row.update(stats)
        lista_tabla.append(row)
    
    df_tabla = pd.DataFrame(lista_tabla)
    
    if not df_tabla.empty:
        if tipo_tabla == "🌐 General":
            df_tabla = df_tabla.sort_values(by=["Pts", "DG", "GF"], ascending=False).reset_index(drop=True)
            df_tabla.index = df_tabla.index + 1
            df_mostrar = df_tabla[["Equipo", "PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]]
        elif tipo_tabla == "🏠 Solo Local":
            df_tabla = df_tabla.sort_values(by=["Pts_L", "DG_L", "GF_L"], ascending=False).reset_index(drop=True)
            df_tabla.index = df_tabla.index + 1
            df_mostrar = df_tabla[["Equipo", "PJ_L", "PG_L", "PE_L", "PP_L", "GF_L", "GC_L", "DG_L", "Pts_L"]]
            df_mostrar.columns = ["Equipo", "PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]
        else:
            df_tabla = df_tabla.sort_values(by=["Pts_V", "DG_V", "GF_V"], ascending=False).reset_index(drop=True)
            df_tabla.index = df_tabla.index + 1
            df_mostrar = df_tabla[["Equipo", "PJ_V", "PG_V", "PE_V", "PP_V", "GF_V", "GC_V", "DG_V", "Pts_V"]]
            df_mostrar.columns = ["Equipo", "PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]

        st.dataframe(df_mostrar, use_container_width=True)
    else:
        st.info("No hay datos en la tabla aún.")

# --- PESTAÑA 4: HISTORIAL ---
with tab_hist:
    st.subheader("Historial de Partidos Simulados")
    historial = db_data[liga_seleccionada]["historial"]
    if historial:
        for match in historial[:15]:
            l = match.get('local', 'Local')
            gl = match.get('goles_local', 0)
            gv = match.get('goles_visitante', 0)
            v = match.get('visitante', 'Visitante')
            res = match.get('resultado', '')
            st.markdown(f"- **{l}** {gl} - {gv} **{v}** ({res})")
    else:
        st.info("No hay historial registrado todavía.")
