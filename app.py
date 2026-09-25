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

# COLOCA AQUÍ TU API KEY OBTENIDA DEL DASHBOARD DE API-FOOTBALL
API_KEY_SPORTS = "TU_API_KEY_AQUI"

# Mapeo de ligas con los IDs oficiales de API-Sports
LEAGUES_API_IDS = {
    "🇪🇸 LaLiga": 140,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": 39,
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": 40,
    "🇮🇹 Serie A": 135,
    "🇩🇪 Bundesliga": 78,
    "🇫🇷 Ligue 1": 61,
}

# Encabezado exclusivo exigido por API-Sports (dashboard.api-football.com)
HEADERS_API_SPORTS = {
    "x-apisports-key": API_KEY_SPORTS,
}


def realizar_peticion_api_sports(league_id, season=2026):
  """Consulta directamente las posiciones a API-Sports."""
  url = f"https://v3.football.api-sports.io/standings?league={league_id}&season={season}"
  try:
    response = requests.get(url, headers=HEADERS_API_SPORTS, timeout=10)
    if response.status_code == 200:
      data = response.json()
      # Si la temporada 2026 aún no tiene datos cargados en alguna liga, intenta con 2025
      if not data.get("response"):
        url_prev = f"https://v3.football.api-sports.io/standings?league={league_id}&season={season-1}"
        res_prev = requests.get(
            url_prev, headers=HEADERS_API_SPORTS, timeout=10
        )
        if res_prev.status_code == 200:
          data = res_prev.json()
      return data
  except Exception as e:
    st.error(f"Error de conexión con API-Sports: {e}")
  return None


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


def sincronizar_con_api_sports(db_data):
  """Lee la tabla oficial desde API-Sports y la sincroniza en tu JSON."""
  hubo_actualizacion = False

  for liga_nombre, league_id in LEAGUES_API_IDS.items():
    data_api = realizar_peticion_api_sports(league_id)

    if not data_api or not data_api.get("response"):
      continue

    try:
      standings_list = data_api["response"][0]["league"]["standings"][0]
    except (KeyError, IndexError):
      continue

    if liga_nombre not in db_data:
      db_data[liga_nombre] = {"tabla": {}, "historial": []}

    tabla_liga = {}

    for item in standings_list:
      team_name = item["team"]["name"]

      all_s = item["all"]
      home_s = item["home"]
      away_s = item["away"]

      tabla_liga[team_name] = {
          "PJ": all_s["played"],
          "PG": all_s["win"],
          "PE": all_s["draw"],
          "PP": all_s["lose"],
          "GF": all_s["goals"]["for"],
          "GC": all_s["goals"]["against"],
          "DG": item["goalsDiff"],
          "Pts": item["points"],
          "PJ_L": home_s["played"],
          "PG_L": home_s["win"],
          "PE_L": home_s["draw"],
          "PP_L": home_s["lose"],
          "GF_L": home_s["goals"]["for"],
          "GC_L": home_s["goals"]["against"],
          "DG_L": home_s["goals"]["for"] - home_s["goals"]["against"],
          "Pts_L": home_s["win"] * 3 + home_s["draw"],
          "PJ_V": away_s["played"],
          "PG_V": away_s["win"],
          "PE_V": away_s["draw"],
          "PP_V": away_s["lose"],
          "GF_V": away_s["goals"]["for"],
          "GC_V": away_s["goals"]["against"],
          "DG_V": away_s["goals"]["for"] - away_s["goals"]["against"],
          "Pts_V": away_s["win"] * 3 + away_s["draw"],
      }

    if tabla_liga:
      db_data[liga_nombre]["tabla"] = tabla_liga
      hubo_actualizacion = True

  return db_data, hubo_actualizacion


def cargar_base_datos():
  data = {}
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    except Exception:
      data = {}

  estructura_base = obtener_estructura_equipo()

  for liga in LEAGUES_API_IDS.keys():
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
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


def calcular_elo_snapshot(stats_eq):
  pj = max(1, stats_eq.get("PJ", 1))
  pts = stats_eq.get("Pts", 0)
  dg = stats_eq.get("DG", 0)
  promedio_pts = pts / pj
  elo = 1500 + (promedio_pts * 110) + (dg * 10)
  return round(elo)


# Configuración de Streamlit
st.set_page_config(
    page_title="Zohan Pronostic v8.0 - API-Sports Direct",
    page_icon="⚽",
    layout="wide",
)

db = cargar_base_datos()

liga_sel = st.sidebar.selectbox(
    "⚽ Seleccionar Liga", list(LEAGUES_API_IDS.keys()), key="select_liga_main"
)
datos_liga = db[liga_sel]

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Sincronización API-Sports")
if st.sidebar.button("🔄 Actualizar Tabla desde API-Sports", type="primary"):
  if API_KEY_SPORTS == "TU_API_KEY_AQUI":
    st.sidebar.error("⚠️ Debes colocar tu API Key real en la variable API_KEY_SPORTS.")
  else:
    with st.spinner("Conectando con API-Sports..."):
      db, exito = sincronizar_con_api_sports(db)
      if exito:
        guardar_base_datos(db)
        st.sidebar.success("¡Tabla vinculada y actualizada con éxito!")
        st.rerun()
      else:
        st.sidebar.error(
            "No se pudieron obtener datos. Verifica tu API Key o cuota diaria."
        )

# Interfaz Principal
st.header(f"Tabla de Posiciones y Jerarquía Elo - {liga_sel}")
if not datos_liga["tabla"]:
  st.warning(
      "⚠️ No hay datos cargados para esta liga. Presiona **'🔄 Actualizar Tabla"
      " desde API-Sports'** en la barra lateral."
  )
else:
  df_tabla = pd.DataFrame.from_dict(datos_liga["tabla"], orient="index")
  cols = ["PJ", "PG", "PE", "PP", "GF", "GC", "DG", "Pts"]
  df_v = df_tabla[cols].copy()

  elos_lista = [
      calcular_elo_snapshot(datos_liga["tabla"][eq]) for eq in df_v.index
  ]
  df_v["Elo"] = elos_lista
  df_v = df_v.sort_values(by=["Pts", "DG", "GF", "Elo"], ascending=False)
  st.dataframe(df_v, use_container_width=True)
