import json
import os
import requests

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

LEAGUES_ESPN = {
    "🇪🇸 LaLiga": "esp.1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "eng.1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": "eng.2",
    "🇮🇹 Serie A": "ita.1",
    "🇩🇪 Bundesliga": "ger.1",
    "🇫🇷 Ligue 1": "fra.1",
}


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
  # Si el archivo no existe, lo crea vacío al vuelo
  if not os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=4)
    except Exception:
      pass

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


def actualizar_desde_espn():
  print(f"Buscando archivo de base de datos en: {os.path.abspath(DB_FILE)}")
  db = cargar_base_datos()
  print("✅ Base de datos local cargada correctamente.")

  cambios_realizados = False

  for liga_nombre, slug in LEAGUES_ESPN.items():
    if liga_nombre not in db:
      db[liga_nombre] = inicializar_liga_vacia(LIGAS_EQUIPOS.get(liga_nombre, []))

    url = f"https://site.api.espn.com/apis/v2/sports/soccer/{slug}/standings"
    try:
      print(f"Consultando API de ESPN para {liga_nombre}...")
      response = requests.get(url, timeout=10)
      if response.status_code != 200:
        print(f"❌ Error HTTP {response.status_code} para {liga_nombre}")
        continue
      data = response.json()

      standings = data.get("standings", [])
      if not standings:
        print(f"⚠️ No se encontraron 'standings' para {liga_nombre}")
        continue

      entries = standings[0].get("entries", [])
      tabla_liga = db[liga_nombre]["tabla"]

      actualizados_liga = 0
      for entry in entries:
        team_name_espn = entry.get("team", {}).get("displayName", "")
        stats = {
            s.get("name"): s.get("value")
            for s in entry.get("stats", [])
            if "name" in s
        }

        pj = int(stats.get("gamesPlayed", 0))
        pg = int(stats.get("wins", 0))
        pe = int(stats.get("ties", 0))
        pp = int(stats.get("losses", 0))
        gf = int(stats.get("pointsFor", 0))
        gc = int(stats.get("pointsAgainst", 0))
        dg = int(stats.get("pointDifferential", gf - gc))
        pts = int(stats.get("points", 0))

        encontrado = False
        for eq_key in list(tabla_liga.keys()):
          if (
              eq_key.lower() in team_name_espn.lower()
              or team_name_espn.lower() in eq_key.lower()
          ):
            tabla_liga[eq_key].update({
                "PJ": pj,
                "PG": pg,
                "PE": pe,
                "PP": pp,
                "GF": gf,
                "GC": gc,
                "DG": dg,
                "Pts": pts,
            })
            encontrado = True
            break

        if not encontrado and team_name_espn:
          tabla_liga[team_name_espn] = obtener_estructura_equipo()
          tabla_liga[team_name_espn].update({
              "PJ": pj,
              "PG": pg,
              "PE": pe,
              "PP": pp,
              "GF": gf,
              "GC": gc,
              "DG": dg,
              "Pts": pts,
          })
          encontrado = True

        if encontrado:
          actualizados_liga += 1
          cambios_realizados = True

      print(f"📊 {liga_nombre}: Se actualizaron {actualizados_liga} equipos.")

    except Exception as e:
      print(f"❌ Excepción actualizando {liga_nombre}: {e}")

  guardar_base_datos(db)
  print("💾 ¡Base de datos guardada y sincronizada con éxito!")
  print("¡Proceso de sincronización finalizado!")


if __name__ == "__main__":
  actualizar_desde_espn()
