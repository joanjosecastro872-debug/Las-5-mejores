import json
import os
import time
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from scipy.stats import poisson
import streamlit as st

DB_FILE = "zohan_pronostic_db.json"

# Token autenticado de Football-Data.org
FOOTBALL_DATA_TOKEN = "9c49e385dc2044439975c26190b17ed9"

# Mapeo de ligas con códigos oficiales de Football-Data.org
LEAGUES_FOOTBALL_DATA = {
    "🇪🇸 LaLiga": "PD",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "PL",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": "ELC",
    "🇮🇹 Serie A": "SA",
    "🇩🇪 Bundesliga": "BL1",
    "🇫🇷 Ligue 1": "FL1",
}


def obtener_estructura_equipo():
  """Retorna la estructura base de métricas para un equipo."""
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


def realizar_peticion_football_data(league_code):
  """Consulta la tabla oficial de Football-Data.org."""
  url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
  headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}

  try:
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
      return response.json()
    else:
      try:
        err_msg = response.json().get("message", response.text)
      except Exception:
        err_msg = response.text
      st.sidebar.error(
          f"Error HTTP {response.status_code} [{league_code}]: {err_msg}"
      )
      return None
  except Exception as e:
    st.sidebar.error(f"Error de conexión de red: {e}")
    return None


def sincronizar_con_football_data(db_data):
  """Sincroniza respetando el límite estricto de 10 peticiones/minuto del plan gratuito."""
  hubo_actualizacion = False

  for liga_nombre, league_code in LEAGUES_FOOTBALL_DATA.items():
    data_api = realizar_peticion_football_data(league_code)

    if not data_api or "standings" not in data_api or not data_api["standings"]:
      time.sleep(6)
      continue

    try:
      standings_total = data_api["standings"][0]["table"]
    except (KeyError, IndexError):
      time.sleep(6)
      continue

    if liga_nombre not in db_data:
      db_data[liga_nombre] = {"tabla": {}, "historial": []}

    tabla_liga = {}

    for item in standings_total:
      team_name = item["team"]["name"]

      pj = item["playedGames"]
      pg = item["won"]
      pe = item["draw"]
      pp = item["lost"]
      gf = item["goalsFor"]
      gc = item["goalsAgainst"]
      dg = item["goalDifference"]
      pts = item["points"]

      # Estimación proporcional para métricas de Local y Visitante
      pj_l = max(1, pj // 2)
      pg_l, pe_l, pp_l = pg // 2, pe // 2, pp // 2
      gf_l, gc_l = gf // 2, gc // 2

      pj_v = max(1, pj - pj_l)
      pg_v, pe_v, pp_v = pg - pg_l, pe - pe_l, pp - pp_l
      gf_v, gc_v = gf - gf_l, gc - gc_l

      tabla_liga[team_name] = {
          "PJ": pj,
          "PG": pg,
          "PE": pe,
          "PP": pp,
          "GF": gf,
          "GC": gc,
          "DG": dg,
          "Pts": pts,
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

    if tabla_liga:
      db_data[liga_nombre]["tabla"] = tabla_liga
      hubo_actualizacion = True

    # Pausa de 6 segundos para garantizar no exceder 10 llamadas/minuto
    time.sleep(6)

  return db_data, hubo_actualizacion


def cargar_base_datos():
  """Carga la base de datos local JSON asegurando la estructura completa de equipos."""
  data = {}
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    except Exception:
      data = {}

  estructura_base = obtener_estructura_equipo()

  for liga in LEAGUES_FOOTBALL_DATA.keys():
    if liga not in data or not isinstance(data[liga], dict):
      data[liga] = {"tabla": {}, "historial": []}

    tabla = data[liga].get("tabla", {})
    for eq, stats in tabla.items():
      for k, v in estructura_base.items():
        if k not in stats:
          stats[k] = v
      tabla[eq] = stats
    data[liga]["tabla"] = tabla

  return data


def guardar_base_datos(data):
  """Guarda el objeto en el archivo JSON local."""
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


def calcular_elo_snapshot(stats_eq):
  """Calcula la puntuación Elo acumulada de un equipo."""
  pj = max(1, stats_eq.get("PJ", 1))
  pts = stats_eq.get("Pts", 0)
  dg = stats_eq.get("DG", 0)
  promedio_pts = pts / pj
  elo = 1500 + (promedio_pts * 110) + (dg * 10)
  return round(elo)


def aplicar_partido_a_tabla(tabla, local, visitante, gl, gv, revertir=False):
  """Aplica los cambios de un marcador manual a la tabla de posiciones."""
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

  if local in tabla:
    eq_l = tabla[local]
    eq_l["PJ"] += factor * 1
    eq_l["PG"] += factor * pg_l
    eq_l["PE"] += factor * pe_l
    eq_l["PP"] += factor * pp_l
    eq_l["GF"] += factor * gl
    eq_l["GC"] += factor * gv
    eq_l["DG"] = eq_l["GF"] - eq_l["GC"]
    eq_l["Pts"] += factor * pts_l

  if visitante in tabla:
    eq_v = tabla[visitante]
    eq_v["PJ"] += factor * 1
    eq_v["PG"] += factor * pg_v
    eq_v["PE"] += factor * pe_v
    eq_v["PP"] += factor * pp_v
    eq_v["GF"] += factor * gv
    eq_v["GC"] += factor * gl
    eq_v["DG"] = eq_v["GF"] - eq_v["GC"]
    eq_v["Pts"] += factor * pts_v


def calcular_fibonacci_y_tendencia(stats_eq, equipo):
  """Evalúa la eficiencia bajo la curva de Fibonacci."""
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


def analizar_racha_automatica(historial, equipo):
  """Analiza la tendencia de los últimos partidos del equipo."""
  partidos_equipo = []
  for m in reversed(historial):
    if m["local"] == equipo or m["visitante"] == equipo:
      is_local = m["local"] == equipo
      goles_favor = m["goles_local"] if is_local else m["goles_visita"]
      goles_contra = m["goles_visita"] if is_local else m["goles_local"]
      if goles_favor > goles_contra:
        res = "G"
      elif goles_favor < goles_contra:
        res = "P"
      else:
        res = "E"
      partidos_equipo.append(res)
    if len(partidos_equipo) >= 5:
      break

  if not partidos_equipo:
    return "Racha Normal / Estable (Sin historial registrado)", 1.0

  ultimos_3 = partidos_equipo[:3]
  if len(ultimos_3) >= 3 and all(r in ["P", "E"] for r in ultimos_3):
    return (
        "Acumula 3+ partidos sin ganar (Busca Rebote / Urgencia)",
        1.05,
    )
  elif all(r == "G" for r in ultimos_3) and len(ultimos_3) >= 2:
    return "En plena racha ganadora", 1.0
  else:
    return "Racha Normal / Estable", 1.0


def simular_monte_carlo(lambda_l, lambda_v, n_simulaciones=10000):
  """Ejecuta simulación de probabilidades mediante Poisson y Monte Carlo."""
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
  """Calcula la matriz de probabilidades de marcadores exactos."""
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


def generar_grafico_macd_y_rsi(historial, equipo, stats_eq=None):
  """Genera el gráfico técnico de MACD y RSI."""
  puntos_partidos = []
  for m in historial:
    if m["local"] == equipo or m["visitante"] == equipo:
      is_local = m["local"] == equipo
      gf = m["goles_local"] if is_local else m["goles_visita"]
      gc = m["goles_visita"] if is_local else m["goles_local"]
      pts = 3 if gf > gc else (1 if gf == gc else 0)
      puntos_partidos.append(pts)

  if len(puntos_partidos) < 4 and stats_eq and stats_eq.get("PJ", 0) > 0:
    pg = stats_eq.get("PG", 0)
    pe = stats_eq.get("PE", 0)
    pp = stats_eq.get("PP", 0)
    secuencia_tabla = [3] * pg + [1] * pe + [0] * pp
    if len(secuencia_tabla) >= 4:
      puntos_partidos = secuencia_tabla[-10:]
    else:
      prom_pts = stats_eq["Pts"] / max(1, stats_eq["PJ"])
      puntos_partidos = [round(prom_pts, 1)] * max(4, stats_eq["PJ"])

  if len(puntos_partidos) < 4:
    puntos_partidos = [1.5, 1.0, 2.0, 1.5, 3.0]

  s = pd.Series(puntos_partidos)
  ema_fast = s.ewm(span=3, adjust=False).mean()
  ema_slow = s.ewm(span=6, adjust=False).mean()
  macd_line = ema_fast - ema_slow
  signal_line = macd_line.ewm(span=3, adjust=False).mean()
  rolling_pts = s.rolling(window=3, min_periods=1).mean()
  rsi_line = (rolling_pts / 3.0) * 100

  fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
  fig.patch.set_facecolor("#0E1117")
  for ax in [ax1, ax2]:
    ax.set_facecolor("#262730")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
      spine.set_edgecolor("#555555")

  ax1.plot(
      macd_line.values,
      label="Línea MACD (Impulso Rápido)",
      color="#00FFCC",
      linewidth=2,
  )
  ax1.plot(
      signal_line.values,
      label="Línea de Señal (Tendencia Lenta)",
      color="#FF007F",
      linewidth=2,
      linestyle="--",
  )
  ax1.axhline(0, color="white", linestyle=":", alpha=0.5)
  ax1.set_title(f"MACD - Impulso de Racha: {equipo}", fontsize=12)
  ax1.legend(loc="upper left", facecolor="#0E1117", labelcolor="white")
  ax1.grid(True, alpha=0.2)

  ax2.plot(
      rsi_line.values,
      label="RSI Futbolístico (%)",
      color="#FFD700",
      linewidth=2,
  )
  ax2.axhline(
      70, color="red", linestyle="--", alpha=0.7, label="Zona Sobrecompra (Techo)"
  )
  ax2.axhline(
      30,
      color="green",
      linestyle="--",
      alpha=0.7,
      label="Zona Sobrevendido (Suelo)",
  )
  ax2.set_title(f"RSI - Termómetro de Sobrecompra/Suelo: {equipo}", fontsize=12)
  ax2.set_xlabel("Partidos Recientes (Cronológico)", fontsize=10)
  ax2.legend(loc="upper left", facecolor="#0E1117", labelcolor="white")
  ax2.grid(True, alpha=0.2)

  plt.tight_layout()
  st.pyplot(fig)


# Configuración e Interfaz Principal
st.set_page_config(
    page_title="Zohan Pronostic v8.0 - Football-Data",
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

# Inicialización de Base de Datos
db = cargar_base_datos()

liga_sel = st.sidebar.selectbox(
    "⚽ Seleccionar Liga",
    list(LEAGUES_FOOTBALL_DATA.keys()),
    key="select_liga_main",
)
datos_liga = db[liga_sel]

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Sincronización Football-Data")
if st.sidebar.button("🔄 Actualizar Tabla Actual", type="primary"):
  with st.spinner("Descargando tablas oficiales en vivo..."):
    db, exito = sincronizar_con_football_data(db)
    if exito:
      guardar_base_datos(db)
      st.sidebar.success("¡Tabla de la temporada actual descargada!")
      st.rerun()
    else:
      st.sidebar.error("No se obtuvieron datos. Verifica la conexión.")

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
      st.sidebar.success("¡Base de datos restaurada!")
      if st.sidebar.button("🔄 Recargar"):
        st.rerun()
  except Exception:
    st.sidebar.error("Archivo .txt inválido.")

# Renderizado de Pestañas
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Tabla & Elo",
    "⚙️ Carga Directa",
    "📝 Registrar Partido",
    "🔬 Auditoría Global",
    "🎯 Analizador Elite",
    "🌍 Analizador Universal",
    "📈 Trading MACD & RSI",
])

with tab1:
  st.header(f"Tabla de Posiciones y Jerarquía Elo - {liga_sel}")
  if not datos_liga["tabla"]:
    st.warning(
        "⚠️ No hay equipos cargados. Presiona **'🔄 Actualizar Tabla Actual'**"
        " en la barra lateral."
    )
  else:
    if "vista_tabla" not in st.session_state:
      st.session_state.vista_tabla = "General"

    b_col1, b_col2, b_col3 = st.columns(3)
    with b_col1:
      if st.button(
          "🌐 Ver General",
          use_container_width=True,
          type=(
              "primary"
              if st.session_state.vista_tabla == "General"
              else "secondary"
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

    elos_lista = [
        calcular_elo_snapshot(datos_liga["tabla"][eq]) for eq in df_v.index
    ]
    df_v["Elo"] = elos_lista
    df_v = df_v.sort_values(by=["Pts", "DG", "GF", "Elo"], ascending=False)
    st.dataframe(df_v, use_container_width=True)

with tab2:
  st.header("⚙️ Carga Directa Avanzada por Equipo")
  if not datos_liga["tabla"]:
    st.info("Sincroniza primero para ver los equipos.")
  else:
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

with tab3:
  st.header("Registrar Partido")
  if not datos_liga["tabla"]:
    st.info("Sincroniza primero para ver los equipos.")
  else:
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
          st.error("⚠️ El local y visitante no pueden ser iguales.")
        else:
          aplicar_partido_a_tabla(datos_liga["tabla"], eq_l, eq_v, gl, gv)
          datos_liga["historial"].append({
              "local": eq_l,
              "visitante": eq_v,
              "goles_local": gl,
              "goles_visita": gv,
          })
          guardar_base_datos(db)
          st.success("¡Partido registrado con éxito!")
          st.rerun()

with tab4:
  st.header("🔬 Auditoría Global")
  if not datos_liga["tabla"]:
    st.info("Sincroniza primero para ver los equipos.")
  else:
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    eq_audit = st.selectbox(
        "Seleccionar Equipo a Examinar:",
        equipos_disponibles,
        key="select_audit_eq",
    )
    if eq_audit:
      stats_audit = datos_liga["tabla"][eq_audit]
      fibo_audit = calcular_fibonacci_y_tendencia(stats_audit, eq_audit)
      elo_audit = calcular_elo_snapshot(stats_audit)
      st.markdown("---")
      st.subheader(f"📋 Radiografía Global: {eq_audit}")
      m1, m2, m3, m4 = st.columns(4)
      m1.metric("Eficiencia Total", f"{fibo_audit['eficiencia']}%")
      m2.metric("Puntaje Elo", f"{elo_audit} pts")
      m3.metric("Tendencia Actual", fibo_audit["tendencia"])
      m4.metric("Nivel Fibonacci", fibo_audit["fibo_estado"])
      st.info(f"💡 **Nota Táctica:** {fibo_audit['fibo_mensaje']}")

with tab5:
  st.header(f"🎯 Analizador Elite ({liga_sel})")
  if not datos_liga["tabla"]:
    st.info("Sincroniza primero para ver los equipos.")
  else:
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
    elo_l = calcular_elo_snapshot(stats_l_base)
    elo_v = calcular_elo_snapshot(stats_v_base)
    racha_l_txt, mult_l = analizar_racha_automatica(
        datos_liga["historial"], p_local
    )
    racha_v_txt, mult_v = analizar_racha_automatica(
        datos_liga["historial"], p_visita
    )

    if p_local == p_visita:
      st.warning("⚠️ Selecciona dos equipos diferentes.")
    else:
      if st.button("🔥 Ejecutar Simulación", type="primary"):
        m_pj_l = max(1, stats_l_base["PJ_L"])
        m_gf_l = stats_l_base["GF_L"]
        m_gc_l = stats_l_base["GC_L"]
        m_pj_v = max(1, stats_v_base["PJ_V"])
        m_gf_v = stats_v_base["GF_V"]
        m_gc_v = stats_v_base["GC_V"]

        gf_l_prom = m_gf_l / m_pj_l
        gc_l_prom = m_gc_l / m_pj_l
        gf_v_prom = m_gf_v / m_pj_v
        gc_v_prom = m_gc_v / m_pj_v

        lambda_local = max(0.2, (gf_l_prom + gc_v_prom) / 2) * mult_l
        lambda_visita = max(0.2, (gf_v_prom + gc_l_prom) / 2) * mult_v

        mc_prob_l, mc_prob_e, mc_prob_v, sim_gl, sim_gv = simular_monte_carlo(
            lambda_local, lambda_visita, 10000
        )
        top_marcadores = calcular_top_marcadores_exactos(
            lambda_local, lambda_visita, 5
        )

        st.markdown("---")
        st.subheader("📋 Resultados de Simulación Monte Carlo")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric(f"Victoria {p_local}", f"{mc_prob_l:.1f}%")
        col_m2.metric("Empate", f"{mc_prob_e:.1f}%")
        col_m3.metric(f"Victoria {p_visita}", f"{mc_prob_v:.1f}%")

        st.markdown("---")
        st.subheader("🎯 Top 5 Marcadores Exactos")
        st.dataframe(
            pd.DataFrame(top_marcadores),
            use_container_width=True,
            hide_index=True,
        )

with tab6:
  st.header("🌍 Analizador Universal")
  st.info("Pestaña disponible para cálculos manuales globales.")

with tab7:
  st.header(f"📈 Gráficos Trading (MACD & RSI) - {liga_sel}")
  if not datos_liga["tabla"]:
    st.info("Sincroniza primero para ver los equipos.")
  else:
    equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
    eq_trading = st.selectbox(
        "Seleccionar Equipo:", equipos_disponibles, key="eq_trading_sel"
    )
    if eq_trading:
      generar_grafico_macd_y_rsi(
          datos_liga["historial"], eq_trading, datos_liga["tabla"][eq_trading]
      )
