# /mount/src/las-5-mejores/app.py
import json
import os
import numpy as np
import pandas as pd
from scipy.stats import poisson
import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN BASE Y ESTILO MÓVIL
# ==========================================
st.set_page_config(
    page_title=(
        "Zohan Pronostic v6.8 - Elite Fibonacci, H2H Directo & Detector de"
        " Trampas"
    ),
    page_icon="⚽",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        flex-wrap: wrap;
        white-space: normal;
    }
    .stTabs [data-baseweb="tab"] {
        height: auto;
        min-height: 40px;
        white-space: normal;
        text-align: center;
        padding: 6px 12px;
        font-size: 13px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

DB_FILE = "zohan_pronostic_db.json"

LIGAS_EQUIPOS = {
    "🇪🇸 LaLiga": [
        "Athletic Club",
        "Atlético de Madrid",
        "CA Osasuna",
        "Celta de Vigo",
        "Deportivo Alavés",
        "Deportivo de La Coruña",
        "Elche CF",
        "FC Barcelona",
        "Getafe CF",
        "Levante UD",
        "Málaga CF",
        "Racing de Santander",
        "Rayo Vallecano",
        "RCD Espanyol",
        "Real Betis",
        "Real Madrid",
        "Real Sociedad",
        "Sevilla FC",
        "Valencia CF",
        "Villarreal CF",
    ],
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": [
        "Arsenal FC",
        "Aston Villa",
        "AFC Bournemouth",
        "Brentford FC",
        "Brighton & Hove Albion",
        "Chelsea FC",
        "Coventry City",
        "Crystal Palace",
        "Everton FC",
        "Fulham FC",
        "Hull City",
        "Ipswich Town",
        "Leeds United",
        "Liverpool FC",
        "Manchester City",
        "Manchester United",
        "Newcastle United",
        "Nottingham Forest",
        "Sunderland AFC",
        "Tottenham Hotspur",
    ],
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": [
        "Birmingham City",
        "Blackburn Rovers",
        "Bolton Wanderers",
        "Bristol City",
        "Burnley FC",
        "Cardiff City",
        "Charlton Athletic",
        "Derby County",
        "Lincoln City",
        "Middlesbrough FC",
        "Millwall FC",
        "Norwich City",
        "Portsmouth FC",
        "Preston North End",
        "Queens Park Rangers (QPR)",
        "Sheffield United",
        "Southampton FC",
        "Stoke City",
        "Swansea City",
        "Watford FC",
        "West Bromwich Albion",
        "West Ham United",
        "Wolverhampton Wanderers",
        "Wrexham AFC",
    ],
    "🇮🇹 Serie A": [
        "AC Milan",
        "AC Monza",
        "AS Roma",
        "Atalanta BC",
        "Bologna FC",
        "Cagliari Calcio",
        "Como 1907",
        "Fiorentina",
        "Frosinone Calcio",
        "Genoa CFC",
        "Inter de Milán",
        "Juventus",
        "Parma Calcio",
        "Sassuolo",
        "SS Lazio",
        "SSC Napoli",
        "Torino FC",
        "Udinese Calcio",
        "US Lecce",
        "Venezia FC",
    ],
    "🇩🇪 Bundesliga": [
        "1. FC Colonia",
        "1. FC Union Berlin",
        "1. FSV Mainz 05",
        "Bayer 04 Leverkusen",
        "Bayern Múnich",
        "Borussia Dortmund",
        "Borussia Mönchengladbach",
        "Eintracht Frankfurt",
        "FC Augsburg",
        "Hamburger SV",
        "Holstein Kiel",
        "RB Leipzig",
        "SC Friburgo",
        "Schalke 04",
        "SV Werder Bremen",
        "TSG Hoffenheim",
        "VfB Stuttgart",
        "VfL Wolfsburg",
    ],
    "🇫🇷 Ligue 1": [
        "AJ Auxerre",
        "Angers SCO",
        "AS Mónaco",
        "ESTAC Troyes",
        "FC Lorient",
        "HAC Le Havre",
        "LOSC Lille",
        "OGC Niza",
        "Olympique de Lyon",
        "Olympique de Marsella",
        "Paris FC",
        "Paris Saint-Germain",
        "RC Estrasburgo",
        "RC Lens",
        "Stade Brestois 29",
        "Stade Rennais",
        "Toulouse FC",
        "Stade de Reims",
    ],
}

# ==========================================
# 2. GESTIÓN DE BASE DE DATOS Y LÓGICA
# ==========================================


def obtener_estructura_equipo():
  return {
      "PJ": 0,
      "PG": 0,
      "PE": 0,
      "PP": 0,
      "GF": 0,
      "GC": 0,
      "DG": 0,
      "Pts": 0,
      "PJ_L": 0,
      "PG_L": 0,
      "PE_L": 0,
      "PP_L": 0,
      "GF_L": 0,
      "GC_L": 0,
      "DG_L": 0,
      "Pts_L": 0,
      "PJ_V": 0,
      "PG_V": 0,
      "PE_V": 0,
      "PP_V": 0,
      "GF_V": 0,
      "GC_V": 0,
      "DG_V": 0,
      "Pts_V": 0,
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
    fibo_mensaje = (
        "Zona de soporte profundo en retroceso de Fibonacci. Acumula presión"
        " extrema, ideal para rebote alcista."
    )
    tendencia = "Bajista Agotada (Alta probabilidad de corrección positiva)"
  elif ratio_rendimiento >= 0.70:
    fibo_estado = "Zona de Resistencia Alta (0.236) - Techo de Rendimiento"
    fibo_mensaje = (
        "Parte alta de la curva de Fibonacci. Muestra máxima solidez pero con"
        " riesgo de corrección a la baja si decae la intensidad."
    )
    tendencia = "Alcista Sólida (Inercia ganadora dominante)"
  else:
    fibo_estado = "Zona de Transición Neutral (0.500 - 0.618)"
    fibo_mensaje = (
        "Rango de equilibrio intermedio en la onda de Fibonacci, dependiente"
        " de los ajustes tácticos del encuentro."
    )
    tendencia = "Estable / Transición Moderada"

  return {
      "eficiencia": eficiencia,
      "fibo_estado": fibo_estado,
      "fibo_mensaje": fibo_mensaje,
      "tendencia": tendencia,
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
          "Probabilidad (%)": round(prob, 2),
      })

  resultados_ordenados = sorted(
      resultados, key=lambda x: x["Probabilidad (%)"], reverse=True
  )
  return resultados_ordenados[:top_n]


# ==========================================
# 3. INTERFAZ STREAMLIT
# ==========================================
db = cargar_base_datos()

liga_sel = st.sidebar.selectbox(
    "⚽ Seleccionar Liga", list(LIGAS_EQUIPOS.keys()), key="select_liga_main"
)
datos_liga = db[liga_sel]

st.sidebar.markdown("---")
st.sidebar.subheader("📱 Gestión de Archivo .TXT")
db_string = json.dumps(db, ensure_ascii=False, indent=4)
st.sidebar.download_button(
    label="📥 Descargar Base de Datos (.TXT)",
    data=db_string,
    file_name="zohan_pronostic_db.txt",
    mime="text/plain",
)

archivo_subido = st.sidebar.file_uploader(
    "📤 Cargar Base de Datos (.TXT)", type=["txt"]
)
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

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Tabla de Posiciones",
    "⚙️ Carga Directa Avanzada",
    "📝 Registrar Partido",
    "🔬 Auditoría Global y Cruzada",
    "🎯 Analizador Quirúrgico Elite",
    "🌍 Analizador Universal",
])

# --- TAB 1: TABLA DE POSICIONES ---
with tab1:
  st.header(f"Tabla de Posiciones - {liga_sel}")
  if "vista_tabla" not in st.session_state:
    st.session_state.vista_tabla = "General"

  b_col1, b_col2, b_col3 = st.columns(3)
  with b_col1:
    if st.button(
        "🌐 Ver General",
        use_container_width=True,
        type=(
            "primary" if st.session_state.vista_tabla == "General" else "secondary"
        ),
    ):
      st.session_state.vista_tabla = "General"
      st.rerun()
  with b_col2:
    if st.button(
        "🏠 Ver Local",
        use_container_width=True,
        type=(
            "primary" if st.session_state.vista_tabla == "Local" else "secondary"
        ),
    ):
      st.session_state.vista_tabla = "Local"
      st.rerun()
  with b_col3:
    if st.button(
        "✈️ Ver Visitante",
        use_container_width=True,
        type=(
            "primary"
            if st.session_state.vista_tabla == "Visitante"
            else "secondary"
        ),
    ):
      st.session_state.vista_tabla = "Visitante"
      st.rerun()

  filtro_vista = st.session_state.vista_tabla
  df_tabla = pd.DataFrame.from_dict(datos_liga["tabla"], orient="index")
  cols = (
      ["PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]
      if filtro_vista == "General"
      else (
          ["PJ_L", "PG_L", "PE_L", "PP_L", "GF_L", "GC_L", "DG_L", "Pts_L"]
          if filtro_vista == "Local"
          else [
              "PJ_V",
              "PG_V",
              "PE_V",
              "PP_V",
              "GF_V",
              "GC_V",
              "DG_V",
              "Pts_V",
          ]
      )
  )
  df_v = df_tabla[cols].copy()
  df_v.columns = ["PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]
  df_v = df_v.sort_values(by=["Pts", "DG", "GF"], ascending=False)
  st.dataframe(df_v, use_container_width=True)

# --- TAB 2: CARGA DIRECTA AVANZADA ---
with tab2:
  st.header("⚙️ Carga Directa Avanzada por Equipo")
  equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
  eq_target = st.selectbox(
      "Seleccionar Equipo a Configurar:",
      equipos_disponibles,
      key="eq_avanzado",
  )
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
          "PJ": pj_l + pj_v,
          "PG": pg_l + pg_v,
          "PE": pe_l + pe_v,
          "PP": pp_l + pp_v,
          "GF": gf_l + gf_v,
          "GC": gc_l + gc_v,
          "DG": (gf_l + gf_v) - (gc_l + gc_v),
          "Pts": (pg_l + pg_v) * 3 + (pe_l + pe_v),
          "PJ_L": pj_l,
          "PG_L": pg_l,
          "PE_L": pe_l,
          "PP_L": pp_l,
          "GF_L": gf_l,
          "GC_L": gc_l,
          "DG_L": gf_l - gc_l,
          "Pts_L": pg_l * 3 + pe_l,
          "PJ_V": pj_v,
          "PG_V": pg_v,
          "PE_V": pe_v,
          "PP_V": pp_v,
          "GF_V": gf_v,
          "GC_V": gc_v,
          "DG_V": gf_v - gc_v,
          "Pts_V": pg_v * 3 + pe_v,
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
      eq_v = st.selectbox(
          "Visitante",
          equipos_disponibles,
          index=1 if len(equipos_disponibles) > 1 else 0,
      )
      gv = st.number_input("Goles Visitante", min_value=0, step=1, value=0)

    if st.form_submit_button("⚽ Registrar", type="primary"):
      if eq_l == eq_v:
        st.error("El local y visitante no pueden ser iguales.")
      else:
        aplicar_partido_a_tabla(datos_liga["tabla"], eq_l, eq_v, gl, gv)
        datos_liga["historial"].append({
            "local": eq_l,
            "visitante": eq_v,
            "goles_local": gl,
            "goles_visita": gv,
        })
        guardar_base_datos(db)
        st.success("¡Partido registrado!")
        st.rerun()

# --- TAB 4: AUDITORÍA GLOBAL Y CRUZADA ---
with tab4:
  st.header("🔬 Auditoría Global y Examen Cruzado por Equipo")
  equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
  eq_audit = st.selectbox(
      "Seleccionar Equipo a Examinar:",
      equipos_disponibles,
      key="select_audit_eq",
  )

  if eq_audit:
    stats_audit = datos_liga["tabla"][eq_audit]
    fibo_audit = calcular_fibonacci_y_tendencia(
        stats_audit, datos_liga["historial"], eq_audit
    )

    st.markdown("---")
    st.subheader(f"📋 Radiografía Global & Fibonacci: {eq_audit}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Eficiencia Total", f"{fibo_audit['eficiencia']}%")
    m2.metric("Tendencia Actual", fibo_audit["tendencia"])
    m3.metric("Nivel Fibonacci", fibo_audit["fibo_estado"])
    st.info(f"💡 **Nota Táctica:** {fibo_audit['fibo_mensaje']}")

# --- TAB 5: ANALIZADOR QUIRÚRGICO ELITE ---
with tab5:
  st.header(
      "🎯 Analizador Quirúrgico Elite - Fibonacci, H2H Directo & Detector de"
      f" Trampas ({liga_sel})"
  )
  st.info(
      "Los datos de temporada se extraen automáticamente de la tabla. Ingresa"
      " directamente los datos de los últimos 10 enfrentamientos directos que"
      " tú hayas extraído."
  )

  equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
  cp1, cp2 = st.columns(2)
  with cp1:
    p_local = st.selectbox("Equipo Local", equipos_disponibles, key="sync_loc")
  with cp2:
    p_visita = st.selectbox(
        "Equipo Visitante",
        equipos_disponibles,
        index=1 if len(equipos_disponibles) > 1 else 0,
        key="sync_vis",
    )

  stats_l_base = datos_liga["tabla"][p_local]
  stats_v_base = datos_liga["tabla"][p_visita]

  # Extracción automática desde la tabla
  m_pj_l = max(1, stats_l_base["PJ_L"])
  m_gf_l = stats_l_base["GF_L"]
  m_gc_l = stats_l_base["GC_L"]

  m_pj_v = max(1, stats_v_base["PJ_V"])
  m_gf_v = stats_v_base["GF_V"]
  m_gc_v = stats_v_base["GC_V"]

  with st.expander(
      "📊 Datos Extraídos Automáticamente de la Tabla", expanded=False
  ):
    ex_c1, ex_c2 = st.columns(2)
    with ex_c1:
      st.markdown(f"**🏠 Local ({p_local}) [Como Local]:**")
      st.write(f"- PJ: `{m_pj_l}` | GF: `{m_gf_l}` | GC: `{m_gc_l}`")
    with ex_c2:
      st.markdown(f"**✈️ Visitante ({p_visita}) [Como Visitante]:**")
      st.write(f"- PJ: `{m_pj_v}` | GF: `{m_gf_v}` | GC: `{m_gc_v}`")

  st.markdown("---")
  with st.expander(
      "⚔️ Bloque Cara a Cara: Ingreso Directo de Últimos 10 Partidos H2H",
      expanded=True,
  ):
    st.write(
        "Ingresa directamente el balance de resultados y los goles totales de"
        " los **últimos 10 enfrentamientos directos** que extrajiste:"
    )

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
      h2h_wins_l = st.number_input(
          f"Victorias de {p_local}",
          min_value=0,
          max_value=10,
          value=5,
          key="h2h_dir_wl",
      )
    with col_b2:
      h2h_draws = st.number_input(
          "Empates", min_value=0, max_value=10, value=3, key="h2h_dir_e"
      )
    with col_b3:
      h2h_wins_v = st.number_input(
          f"Victorias de {p_visita}",
          min_value=0,
          max_value=10,
          value=2,
          key="h2h_dir_wv",
      )

    st.markdown("---")
    st.write(
        "Ingresa los **goles totales** anotados por cada bando en esos 10"
        " partidos (para calcular las medias de goles):"
    )
    col_g1, col_g2 = st.columns(2)
    with col_g1:
      h2h_goles_l = st.number_input(
          f"Goles Totales de {p_local} en los 10 duelos",
          min_value=0.0,
          max_value=50.0,
          value=14.0,
          step=0.5,
          key="h2h_dir_gl",
      )
    with col_g2:
      h2h_goles_v = st.number_input(
          f"Goles Totales de {p_visita} en los 10 duelos",
          min_value=0.0,
          max_value=50.0,
          value=9.0,
          step=0.5,
          key="h2h_dir_gv",
      )

    h2h_pj = 10

  st.markdown("---")
  if p_local == p_visita:
    st.warning(
        "⚠️ Selecciona dos equipos diferentes para realizar el análisis"
        " cruzado."
    )
  else:
    if st.button(
        "🔥 Ejecutar Simulación Estocástica & Análisis H2H Directo",
        type="primary",
    ):
      fibo_l = calcular_fibonacci_y_tendencia(
          stats_l_base, datos_liga["historial"], p_local
      )
      fibo_v = calcular_fibonacci_y_tendencia(
          stats_v_base, datos_liga["historial"], p_visita
      )

      # Promedios de la tabla general
      gf_l_prom = m_gf_l / m_pj_l
      gc_l_prom = m_gc_l / m_pj_l
      gf_v_prom = m_gf_v / m_pj_v
      gc_v_prom = m_gc_v / m_pj_v

      base_lambda_local = (gf_l_prom + gc_v_prom) / 2
      base_lambda_visita = (gf_v_prom + gc_l_prom) / 2

      # Promedios del Cara a Cara ingresado directamente
      h2h_lambda_l = h2h_goles_l / h2h_pj
      h2h_lambda_v = h2h_goles_v / h2h_pj

      # Ponderación final: 70% rendimiento de tabla + 30% tendencia directa H2H
      lambda_local = (0.7 * base_lambda_local) + (0.3 * h2h_lambda_l)
      lambda_visita = (0.7 * base_lambda_visita) + (0.3 * h2h_lambda_v)

      mc_prob_l, mc_prob_e, mc_prob_v, sim_gl, sim_gv = simular_monte_carlo(
          lambda_local, lambda_visita, 10000
      )
      prom_sim_gl = np.mean(sim_gl)
      prom_sim_gv = np.mean(sim_gv)

      # Cálculo de Ambos Anotan (BTTS)
      btts_prob = np.mean((sim_gl > 0) & (sim_gv > 0)) * 100

      top_marcadores = calcular_top_marcadores_exactos(
          lambda_local, lambda_visita, 5
      )

      st.markdown("---")
      st.subheader(
          "📋 Mensaje y Desglose Táctico Integral (Fibonacci & H2H Directo)"
      )

      msg_clima = (
          "### 🏟️ Radiografía y Contraste del Enfrentamiento:"
          f" {p_local} vs {p_visita}\n\n"
      )

      msg_clima += f"#### 1️⃣ Tendencias y Niveles de Fibonacci\n"
      msg_clima += (
          f"- **{p_local} (Local):** Tendencia: *{fibo_l['tendencia']}* | Nivel:"
          f" **{fibo_l['fibo_estado']}**.\n  > *{fibo_l['fibo_mensaje']}*\n"
      )
      msg_clima += (
          f"- **{p_visita} (Visitante):** Tendencia: *{fibo_v['tendencia']}* |"
          f" Nivel: **{fibo_v['fibo_estado']}**.\n  > *{fibo_v['fibo_mensaje']}*\n\n"
      )

      msg_clima += (
          "#### 2️⃣ Análisis del Bloque H2H (Últimos 10 Duelos Ingresados"
          " Directamente)\n"
      )
      msg_clima += (
          f"- **Balance Directo (Resultados):** `{p_local}` ganó"
          f" **{h2h_wins_l}** partidos, se registraron **{h2h_draws}** empates,"
          f" y `{p_visita}` ganó **{h2h_wins_v}** partidos.\n"
      )
      msg_clima += (
          f"- **Goles Totales y Promedios:** El local anotó `{h2h_goles_l}` goles"
          f" (`{h2h_lambda_l:.2f}` p.p.) y el visitante `{h2h_goles_v}` goles"
          f" (`{h2h_lambda_v:.2f}` p.p.).\n"
      )
      msg_clima += (
          "- **Calibración Matemática:** El sistema integra este balance"
          " directo con el rendimiento de la temporada para refinar la"
          " expectativa estocástica.\n\n"
      )

      msg_clima += (
          "#### 3️⃣ Motor Matemático (Monte Carlo & Poisson Integrado)\n"
      )
      msg_clima += (
          "- **Expectativa de Goles (Lambda Final Ponderado):** Local:"
          f" `{prom_sim_gl:.2f}` | Visitante: `{prom_sim_gv:.2f}`.\n"
      )
      msg_clima += (
          "- **Probabilidades de Resultado:** Victoria Local:"
          f" **{mc_prob_l:.1f}%** | Empate: **{mc_prob_e:.1f}%** | Victoria"
          f" Visitante: **{mc_prob_v:.1f}%**.\n"
      )
      msg_clima += (
          f"- **Probabilidad de Ambos Equipos Anotan (BTTS):**"
          f" **{btts_prob:.1f}%**\n\n"
      )

      msg_clima += f"#### 4️⃣ Top 5 Posibles Marcadores Exactos\n"
      for idx, m in enumerate(top_marcadores, 1):
        msg_clima += (
            f"  {idx}. **{m['Marcador']}** (Probabilidad:"
            f" **{m['Probabilidad (%)']}%**)\n"
        )
      msg_clima += "\n"

      if mc_prob_l > mc_prob_v and mc_prob_l > mc_prob_e:
        veredicto_final = (
            "**Veredicto Táctico:** Escenario inclinado a favor del anfitrión"
            f" (**{p_local}**). La inercia y los antecedentes directos"
            " respaldan el favoritismo."
        )
      elif mc_prob_v > mc_prob_l and mc_prob_v > mc_prob_e:
        veredicto_final = (
            "**Veredicto Táctico:** Alerta de golpe foráneo. El visitante"
            f" (**{p_visita}**) muestra argumentos numéricos idóneos para"
            " puntuar fuera de casa."
        )
      else:
        veredicto_final = (
            "**Veredicto Táctico:** Partido de máxima paridad. Las curvas de"
            " Fibonacci y el historial apuntan a un duelo cerrado donde los"
            " detalles definirán el marcador."
        )

      msg_clima += f"#### 🎯 Conclusión del Analizador\n{veredicto_final}"

      st.success(msg_clima)

      st.markdown("---")
      col_m1, col_m2, col_m3 = st.columns(3)
      col_m1.metric(
          f"Victoria {p_local}", f"{mc_prob_l:.1f}%", f"Goles: {prom_sim_gl:.2f}"
      )
      col_m2.metric("Empate Probable", f"{mc_prob_e:.1f}%")
      col_m3.metric(
          f"Victoria {p_visita}", f"{mc_prob_v:.1f}%", f"Goles: {prom_sim_gv:.2f}"
      )

      st.markdown("---")
      st.subheader("🎯 Tabla de los 5 Posibles Marcadores Exactos")
      df_marcadores = pd.DataFrame(top_marcadores)
      st.dataframe(df_marcadores, use_container_width=True, hide_index=True)

      st.markdown("---")
      st.subheader("🚨 Radar de Alerta Roja & Detector de Partidos Trampa")

      UMBRAL_FRANCOTIRADOR = 60.0
      UMBRAL_VISITANTE_ELITE = 53.0
      UMBRAL_EMPATE_TRAMPA = 28.0

      if mc_prob_l >= UMBRAL_FRANCOTIRADOR:
        st.error(
            f"🎯 **¡ALERTA ROJA (FAVORITO CLARO / FRANCOTIRADOR)!** El anfitrión"
            f" **{p_local}** domina con un **{mc_prob_l:.1f}%** en la simulación"
            " estocástica."
        )
      elif mc_prob_v >= UMBRAL_VISITANTE_ELITE:
        st.error(
            "🎯 **¡ALERTA ROJA (ASALTO FORÁNEO)!** El visitante"
            f" **{p_visita}** muestra una fuerza del **{mc_prob_v:.1f}%**, ideal"
            " para buscar valor afuera."
        )
      elif mc_prob_e >= UMBRAL_EMPATE_TRAMPA:
        st.warning(
            "⚠️ **¡PARTIDO TRAMPA / ALERTA DE EMPATE!** La probabilidad de"
            f" empate se dispara al **{mc_prob_e:.1f}%**. Las matemáticas y el"
            " historial H2H directo muestran un choque muy cerrado donde el"
            " favorito está propenso a caer o repartir puntos."
        )
      else:
        st.info(
            "🛡️ **Carril Normal:** Partido dentro de parámetros estándar de"
            " paridad moderada. Sin alertas extremas en el radar."
        )

      # ==========================================
      # 🛡️ PANEL DE BLINDAJE AUTOMÁTICO PARA PARLAYS (LIGAS)
      # ==========================================
      st.markdown("---")
      st.subheader("🛡️ Panel de Blindaje Automático para Parlays")

      t_sub1, t_sub2, t_sub3, t_sub4 = st.tabs([
          "🛡️ Termómetro de Hándicap",
          "⚽ Filtro Automático de Goles",
          "🔥 Mercado BTTS (Ambos Anotan)",
          "🌟 Fortaleza Relativa vs Liga",
      ])

      with t_sub1:
        st.markdown(
            "### Análisis de Holgura y Hándicap (Derivado de Monte Carlo)"
        )
        win_by_2_plus_l = np.mean(sim_gl - sim_gv >= 2) * 100
        win_by_2_plus_v = np.mean(sim_gl - sim_gv <= -2) * 100
        win_by_1 = np.mean(np.abs(sim_gl - sim_gv) == 1) * 100

        st.write(
            f"- **Probabilidad de victoria holgada Local (-1.5 Hándicap):**"
            f" **{win_by_2_plus_l:.1f}%**"
        )
        st.write(
            f"- **Probabilidad de victoria holgada Visitante (+1.5 Hándicap):**"
            f" **{win_by_2_plus_v:.1f}%**"
        )
        st.write(
            f"- **Probabilidad de partido ajustado (por 1 gol):**"
            f" {win_by_1:.1f}%"
        )

        if win_by_2_plus_l > 45:
          st.success(
              "💡 **Sugerencia de Parlay:** El local muestra solidez para un"
              " Hándicap Asiático -1 o victoria simple segura."
          )
        elif win_by_2_plus_v > 40:
          st.warning(
              "💡 **Sugerencia de Parlay:** El visitante tiene alta inercia de"
              " victoria holgada fuera de casa."
          )
        else:
          st.info(
              "💡 **Sugerencia de Parlay:** Margen estrecho. Evitar hándicaps"
              " grandes; preferir doble oportunidad o descartar para la"
              " combinada."
          )

      with t_sub2:
        st.markdown("### Probabilidades de Líneas de Goles (Over / Under)")
        total_goles_sim = sim_gl + sim_gv
        prob_over_15 = np.mean(total_goles_sim > 1.5) * 100
        prob_over_25 = np.mean(total_goles_sim > 2.5) * 100
        prob_under_35 = np.mean(total_goles_sim < 3.5) * 100

        st.write(
            f"- **Probabilidad Más de 1.5 Goles (+1.5):** {prob_over_15:.1f}%"
        )
        st.write(
            f"- **Probabilidad Más de 2.5 Goles (+2.5):** {prob_over_25:.1f}%"
        )
        st.write(
            f"- **Probabilidad Menos de 3.5 Goles (-3.5):** {prob_under_35:.1f}%"
        )

        if prob_over_25 > 65:
          st.success(
              "🔥 **Filtro de Goles:** Alta expectativa de anotaciones."
              " Excelente candidato para 'Más de 1.5 o 2.5 goles' en tu"
              " combinada."
          )
        elif prob_over_25 < 40:
          st.warning(
              "⚠️ **Filtro de Goles:** Partido con tendencia de pocos goles."
              " Cuidado con mercados de altas."
          )
        else:
          st.info("⚖️ **Filtro de Goles:** Comportamiento estándar de goles.")

      with t_sub3:
        st.markdown("### Análisis del Mercado Ambos Equipos Anotan (BTTS)")
        st.metric("Probabilidad de BTTS (Sí Marcan Ambos)", f"{btts_prob:.1f}%")
        if btts_prob >= 62:
          st.success(
              "🔥 **Mercado BTTS:** Excelente opción para combinada. Alta"
              " probabilidad de intercambio de goles."
          )
        elif btts_prob <= 40:
          st.warning(
              "⚠️ **Mercado BTTS:** Tendencia baja. Riesgo de que uno de los"
              " dos equipos se quede sin anotar."
          )
        else:
          st.info(
              "⚖️ **Mercado BTTS:** Comportamiento estándar sin polarización"
              " extrema."
          )

      with t_sub4:
        st.markdown("### Comparativa de Desempeño Relativo vs Media")
        media_liga_goles = (
            (m_gf_l + m_gf_v) / (m_pj_l + m_pj_v)
            if (m_pj_l + m_pj_v) > 0
            else 1.3
        )
        fuerza_ataque_l = lambda_local / max(0.5, media_liga_goles)
        fuerza_ataque_v = lambda_visita / max(0.5, media_liga_goles)

        st.write(
            f"- **Índice de Fuerza Ofensiva Local vs Media:**"
            f" **{fuerza_ataque_l:.2f}x**"
        )
        st.write(
            f"- **Índice de Fuerza Ofensiva Visitante vs Media:**"
            f" **{fuerza_ataque_v:.2f}x**"
        )

        if fuerza_ataque_l > 1.25 and mc_prob_l > 55:
          st.success(
              "🌟 **Fortaleza Relativa:** El local está muy por encima de la"
              " media de su liga. Categoría **Francotirador Aprobado** para"
              " parlay."
          )
        elif mc_prob_e > 33:
          st.warning(
              "🚨 **Alerta de Fortaleza:** Desequilibrio mínimo con alto riesgo"
              " de empate."
          )
        else:
          st.info(
              "ℹ️ **Fortaleza Relativa:** Comportamiento competitivo normal sin"
              " anomalías extremas."
          )

# --- TAB 6: ANALIZADOR UNIVERSAL ---
with tab6:
  st.header("🌍 Analizador Universal (Datos Completos de Ambos Equipos + H2H)")
  st.info(
      "Introduce los nombres y todas las estadísticas de ambos equipos"
      " (rendimiento en casa y de visitante para los dos) junto con el"
      " historial directo."
  )

  col_n1, col_n2 = st.columns(2)
  with col_n1:
    u_local = st.text_input(
        "Nombre del Equipo Local", value="Equipo Local", key="un_l"
    )
  with col_n2:
    u_visita = st.text_input(
        "Nombre del Equipo Visitante", value="Equipo Visitante", key="un_v"
    )

  st.markdown("---")
  st.subheader(f"📊 1. Radiografía Completa de {u_local} (Casa y Afuera)")
  uc_l1, uc_l2 = st.columns(2)
  with uc_l1:
    st.markdown(f"**🏠 ¿Cómo juega {u_local} en su CASA?**")
    ul_pj_c = st.number_input(
        "Partidos Jugados en Casa", min_value=1, value=10, key="ul_pjc"
    )
    ul_gf_c = st.number_input(
        "Goles a Favor en Casa", min_value=0.0, value=18.0, key="ul_gfc"
    )
    ul_gc_c = st.number_input(
        "Goles en Contra en Casa", min_value=0.0, value=8.0, key="ul_gcc"
    )
  with uc_l2:
    st.markdown(f"**✈️ ¿Cómo juega {u_local} cuando va de VISITANTE?**")
    ul_pj_f = st.number_input(
        "Partidos Jugados Afuera", min_value=1, value=10, key="ul_pjf"
    )
    ul_gf_f = st.number_input(
        "Goles a Favor Afuera", min_value=0.0, value=12.0, key="ul_gff"
    )
    ul_gc_f = st.number_input(
        "Goles en Contra Afuera", min_value=0.0, value=14.0, key="ul_gcf"
    )

  st.markdown("---")
  st.subheader(f"📊 2. Radiografía Completa de {u_visita} (Casa y Afuera)")
  uc_v1, uc_v2 = st.columns(2)
  with uc_v1:
    st.markdown(f"**🏠 ¿Cómo juega {u_visita} en su CASA?**")
    uv_pj_c = st.number_input(
        "Partidos Jugados en Casa", min_value=1, value=10, key="uv_pjc"
    )
    uv_gf_c = st.number_input(
        "Goles a Favor en Casa", min_value=0.0, value=15.0, key="uv_gfc"
    )
    uv_gc_c = st.number_input(
        "Goles en Contra en Casa", min_value=0.0, value=10.0, key="uv_gcc"
    )
  with uc_v2:
    st.markdown(f"**✈️ ¿Cómo juega {u_visita} cuando va de VISITANTE?**")
    uv_pj_f = st.number_input(
        "Partidos Jugados Afuera", min_value=1, value=10, key="uv_pjf"
    )
    uv_gf_f = st.number_input(
        "Goles a Favor Afuera", min_value=0.0, value=10.0, key="uv_gff"
    )
    uv_gc_f = st.number_input(
        "Goles en Contra Afuera", min_value=0.0, value=15.0, key="uv_gcf"
    )

  st.markdown("---")
  st.subheader("⚔️ 3. Historial Cara a Cara (H2H - Últimos 10 Duelos)")
  st.write(
      "Indica quién ha ganado más, los empates y los goles totales de esos"
      " duelos directos:"
  )

  uh_1, uh_2, uh_3 = st.columns(3)
  with uh_1:
    uh_wins_l = st.number_input(
        f"Victorias de {u_local}", min_value=0, max_value=10, value=4, key="uh_wl"
    )
  with uh_2:
    uh_draws = st.number_input(
        "Empates", min_value=0, max_value=10, value=3, key="uh_d"
    )
  with uh_3:
    uh_wins_v = st.number_input(
        f"Victorias de {u_visita}", min_value=0, max_value=10, value=3, key="uh_wv"
    )

  uh_g1, uh_g2 = st.columns(2)
  with uh_g1:
    uh_goles_l = st.number_input(
        f"Goles totales de {u_local} en el H2H",
        min_value=0.0,
        value=14.0,
        key="uh_gl",
    )
  with uh_g2:
    uh_goles_v = st.number_input(
        f"Goles totales de {u_visita} en el H2H",
        min_value=0.0,
        value=11.0,
        key="uh_gv",
    )

  u_media_liga = st.slider(
      "🌐 Promedio de Goles Esperado de esta Liga (Baseline)",
      min_value=1.0,
      max_value=2.0,
      value=1.35,
      step=0.05,
      key="u_slider_liga",
  )

  st.markdown("---")
  if st.button("🚀 Ejecutar Simulación Universal Completa", type="primary"):
    lambda_l_base = ((ul_gf_c / ul_pj_c) + (uv_gc_f / uv_pj_f)) / 2
    lambda_v_base = ((uv_gf_f / uv_pj_f) + (ul_gc_c / ul_pj_c)) / 2

    h2h_l = uh_goles_l / 10.0
    h2h_v = uh_goles_v / 10.0

    lambda_local_final = (lambda_l_base * 0.7) + (h2h_l * 0.3)
    lambda_visita_final = (lambda_v_base * 0.7) + (h2h_v * 0.3)

    p_l, p_e, p_v, sim_gl_u, sim_gv_u = simular_monte_carlo(
        lambda_local_final, lambda_visita_final, 10000
    )
    btts_u = np.mean((sim_gl_u > 0) & (sim_gv_u > 0)) * 100
    top_m_u = calcular_top_marcadores_exactos(
        lambda_local_final, lambda_visita_final, 5
    )

    st.subheader(
        f"🎯 Resultados del Análisis Universal: {u_local} vs {u_visita}"
    )
    ur1, ur2, ur3 = st.columns(3)
    ur1.metric(
        f"Victoria {u_local}",
        f"{p_l:.1f}%",
        f"Goles: {np.mean(sim_gl_u):.2f}",
    )
    ur2.metric("Empate", f"{p_e:.1f}%")
    ur3.metric(
        f"Victoria {u_visita}",
        f"{p_v:.1f}%",
        f"Goles: {np.mean(sim_gv_u):.2f}",
    )

    st.markdown("---")
    st.subheader("📊 Top 5 Marcadores Exactos Más Probables")
    st.dataframe(pd.DataFrame(top_m_u), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🛡️ Panel de Blindaje y Mercados (Universal)")

    ut1, ut2, ut3, ut4 = st.tabs([
        "🛡️ Hándicap",
        "⚽ Goles (Over/Under)",
        "🔥 Ambos Anotan (BTTS)",
        "🌟 Fortaleza Relativa",
    ])

    with ut1:
      w_2_l = np.mean(sim_gl_u - sim_gv_u >= 2) * 100
      w_2_v = np.mean(sim_gl_u - sim_gv_u <= -2) * 100
      st.write(
          f"- **Probabilidad de victoria holgada Local (-1.5 Hándicap):**"
          f" **{w_2_l:.1f}%**"
      )
      st.write(
          f"- **Probabilidad de victoria holgada Visitante (+1.5 Hándicap):**"
          f" **{w_2_v:.1f}%**"
      )

    with ut2:
      tot_g_u = sim_gl_u + sim_gv_u
      st.write(
          f"- **Más de 1.5 Goles (+1.5):**"
          f" **{np.mean(tot_g_u > 1.5) * 100:.1f}%**"
      )
      st.write(
          f"- **Más de 2.5 Goles (+2.5):**"
          f" **{np.mean(tot_g_u > 2.5) * 100:.1f}%**"
      )
      st.write(
          f"- **Menos de 3.5 Goles (-3.5):**"
          f" **{np.mean(tot_g_u < 3.5) * 100:.1f}%**"
      )

    with ut3:
      st.metric(
          "Probabilidad de Ambos Equipos Anotan (BTTS)", f"{btts_u:.1f}%"
      )
      if btts_u >= 62:
        st.success(
            "🔥 Alta tendencia a que ambos equipos marquen en este encuentro."
        )
      else:
        st.info("⚖️ Comportamiento estándar para el mercado de goles.")

    with ut4:
      f_l_rel = lambda_local_final / u_media_liga
      f_v_rel = lambda_visita_final / u_media_liga
      st.write(f"- **Fuerza Ofensiva Local vs Media:** **{f_l_rel:.2f}x**")
      st.write(f"- **Fuerza Ofensiva Visitante vs Media:** **{f_v_rel:.2f}x**")

