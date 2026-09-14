import streamlit as st
import json
import os
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

# Listas base (si ya tienes equipos guardados en tu JSON con otros nombres, el sistema los respetará)
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
# 2. BASE DE DATOS Y MEMORIA JSON BLINDADA
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
                            
                        # Respetamos los equipos que ya están en el JSON, y agregamos si falta alguno oficial
                        equipos_json = list(data[liga]["tabla"].keys())
                        for eq in LIGAS_EQUIPOS[liga]:
                            if eq not in equipos_json:
                                data[liga]["tabla"][eq] = keys_requeridas.copy()
                                
                        # Actualizar la estructura de las estadísticas por si faltan llaves
                        for eq in data[liga]["tabla"].keys():
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
liga_seleccionada = st.sidebar.selectbox("Selecciona la Liga", list(db_data.keys()))

st.sidebar.markdown("---")
st.sidebar.markdown("### 📱 Respaldar y Transferir")

# 1. Botón para DESCARGAR el archivo (PC -> Teléfono)
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        json_data = f.read()
    st.sidebar.download_button(
        label="📥 Descargar Base de Datos",
        data=json_data,
        file_name="zohan_pronostic_db.json",
        mime="application/json"
    )

# 2. Botón para SUBIR el archivo (Teléfono -> PC)
archivo_subido = st.sidebar.file_uploader("📤 Subir archivo de respaldo", type=["json"])
if archivo_subido is not None:
    if st.sidebar.button("⚠️ Cargar y Sobrescribir Datos"):
        try:
            datos_nuevos = json.load(archivo_subido)
            guardar_base_datos(datos_nuevos)
            st.sidebar.success("¡Datos cargados con éxito!")
            st.rerun()
        except Exception:
            st.sidebar.error("Error al cargar el archivo.")
            
st.sidebar.markdown("---")

if st.sidebar.button("🗑️ Reiniciar Liga Actual a Ceros"):
    db_data[liga_seleccionada] = inicializar_liga_vacia(list(db_data[liga_seleccionada]["tabla"].keys()))
    guardar_base_datos(db_data)
    st.sidebar.success(f"¡Datos de {liga_seleccionada} borrados!")
    st.rerun()

equipos_liga = list(db_data[liga_seleccionada]["tabla"].keys())

st.title(f"⚽ Zohan Pronostic v2 - {liga_seleccionada}")

tab_reg_partido, tab_tabla, tab_editar, tab_hist = st.tabs([
    "⚽ Registrar Partidos", 
    "📊 Tabla de Posiciones", 
    "✏️ Editar Equipos y Tabla",
    "📜 Historial"
])

# --- PESTAÑA 1: REGISTRAR PARTIDO ---
with tab_reg_partido:
    st.subheader("Registro de Partidos Reales")
    with st.form("form_partido_real", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            local = st.selectbox("Equipo Local", equipos_liga, index=0, key="real_local")
            goles_local = st.number_input("Goles Local", min_value=0, value=0, step=1, key="real_gl")
        with col2:
            visitante = st.selectbox("Equipo Visitante", equipos_liga, index=1 if len(equipos_liga) > 1 else 0, key="real_visitante")
            goles_visitante = st.number_input("Goles Visitante", min_value=0, value=0, step=1, key="real_gv")
        
        btn_guardar_partido = st.form_submit_button("Guardar Este Partido")

    if btn_guardar_partido:
        if local == visitante:
            st.error("⚠️ El equipo local y visitante no pueden ser el mismo.")
        else:
            db_fresh = cargar_base_datos()
            tabla_liga = db_fresh[liga_seleccionada]["tabla"]

            t_loc = tabla_liga[local]
            t_vis = tabla_liga[visitante]

            t_loc["PJ_L"] += 1
            t_loc["GF_L"] += goles_local
            t_loc["GC_L"] += goles_visitante
            t_loc["DG_L"] = t_loc["GF_L"] - t_loc["GC_L"]

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

            for eq_key in [local, visitante]:
                e = tabla_liga[eq_key]
                e["PJ"] = e["PJ_L"] + e["PJ_V"]
                e["PG"] = e["PG_L"] + e["PG_V"]
                e["PE"] = e["PE_L"] + e["PE_V"]
                e["PP"] = e["PP_L"] + e["PP_V"]
                e["GF"] = e["GF_L"] + e["GF_V"]
                e["GC"] = e["GC_L"] + e["GC_V"]
                e["DG"] = e["GF"] - e["GC"]
                e["Pts"] = e["Pts_L"] + e["Pts_V"]

            db_fresh[liga_seleccionada]["historial"].insert(0, {
                "local": local,
                "visitante": visitante,
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "resultado": res_str
            })
            
            guardar_base_datos(db_fresh)
            st.success(f"✅ ¡Guardado con éxito: **{local} {goles_local} - {goles_visitante} {visitante}**!")
            st.rerun()

# --- PESTAÑA 2: TABLA DE POSICIONES ---
with tab_tabla:
    st.subheader("Clasificación de la Liga")
    db_view = cargar_base_datos()
    tabla_actual = db_view[liga_seleccionada]["tabla"]

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

# --- PESTAÑA 3: EDITAR EQUIPOS Y TABLA ---
with tab_editar:
    st.subheader("🛠️ Control Total de Equipos y Puntuación")
    
    st.markdown("### 1. Reemplazar Nombre de un Equipo")
    st.info("Si hay un equipo mal puesto, selecciona su nombre actual y escribe el nombre del equipo correcto. Todo el historial y los puntos se trasladarán.")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        eq_viejo = st.selectbox("Selecciona el equipo a reemplazar", equipos_liga, key="sel_eq_v")
    with col_e2:
        eq_nuevo = st.text_input("Nombre del nuevo equipo", key="txt_eq_n")
        
    if st.button("🔄 Reemplazar Equipo"):
        if eq_nuevo.strip() != "" and eq_nuevo != eq_viejo:
            db_edit = cargar_base_datos()
            tabla_liga_edit = db_edit[liga_seleccionada]["tabla"]
            
            # Reemplazar en la tabla manteniendo las estadísticas existentes
            tabla_liga_edit[eq_nuevo.strip()] = tabla_liga_edit.pop(eq_viejo)
            
            # Reemplazar en el historial de partidos
            for match in db_edit[liga_seleccionada]["historial"]:
                if match["local"] == eq_viejo:
                    match["local"] = eq_nuevo.strip()
                if match["visitante"] == eq_viejo:
                    match["visitante"] = eq_nuevo.strip()
                    
            guardar_base_datos(db_edit)
            st.success(f"✅ Se cambió **{eq_viejo}** por **{eq_nuevo.strip()}** con éxito.")
            st.rerun()
        elif eq_nuevo.strip() == "":
            st.error("Ingresa un nombre válido para el nuevo equipo.")
        else:
            st.warning("El nombre nuevo es igual al viejo.")
            
    st.markdown("---")
    st.markdown("### 2. Edición Directa de Datos (Tipo Excel)")
    st.info("Haz doble clic en cualquier celda para corregir número de partidos, goles o puntos directamente. Luego presiona Guardar.")
    
    db_edit_tabla = cargar_base_datos()
    tabla_dict = db_edit_tabla[liga_seleccionada]["tabla"]
    
    df_edit = pd.DataFrame.from_dict(tabla_dict, orient="index").reset_index()
    df_edit.rename(columns={"index": "Equipo"}, inplace=True)
    
    df_modificado = st.data_editor(df_edit, key="editor_tabla_interactivo", num_rows="fixed", use_container_width=True)
    
    if st.button("💾 Guardar Cambios Realizados en la Tabla"):
        nueva_tabla = {}
        for _, row in df_modificado.iterrows():
            eq = row["Equipo"]
            stats = row.drop("Equipo").to_dict()
            
            # Recalcular Diferencia de Goles automáticamente por seguridad
            stats["DG"] = stats["GF"] - stats["GC"]
            stats["DG_L"] = stats["GF_L"] - stats["GC_L"]
            stats["DG_V"] = stats["GF_V"] - stats["GC_V"]
            nueva_tabla[eq] = stats
            
        db_edit_tabla[liga_seleccionada]["tabla"] = nueva_tabla
        guardar_base_datos(db_edit_tabla)
        st.success("✅ ¡Tabla de datos actualizada y guardada correctamente!")
        st.rerun()

# --- PESTAÑA 4: HISTORIAL ---
with tab_hist:
    st.subheader("Historial de Partidos Registrados")
    db_hist = cargar_base_datos()
    historial = db_hist[liga_seleccionada]["historial"]
    if historial:
        for match in historial:
            l = match.get('local', 'Local')
            gl = match.get('goles_local', 0)
            gv = match.get('goles_visitante', 0)
            v = match.get('visitante', 'Visitante')
            res = match.get('resultado', '')
            st.markdown(f"- **{l}** {gl} - {gv} **{v}** ({res})")
    else:
        st.info("No hay historial registrado todavía.")

