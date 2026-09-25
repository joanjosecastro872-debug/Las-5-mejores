import json
import os
import requests

DB_FILE = "zohan_pronostic_db.json"

LEAGUES_ESPN = {
    "🇪🇸 LaLiga": "esp.1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "eng.1",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Championship": "eng.2",
    "🇮🇹 Serie A": "ita.1",
    "🇩🇪 Bundesliga": "ger.1",
    "🇫🇷 Ligue 1": "fra.1",
}


def actualizar_desde_espn():
  if not os.path.exists(DB_FILE):
    print("No se encontró la base de datos local.")
    return

  with open(DB_FILE, "r", encoding="utf-8") as f:
    db = json.load(f)

  for liga_nombre, slug in LEAGUES_ESPN.items():
    if liga_nombre not in db:
      continue

    url = f"https://site.api.espn.com/apis/v2/sports/soccer/{slug}/standings"
    try:
      response = requests.get(url, timeout=10)
      if response.status_code != 200:
        continue
      data = response.json()

      standings = data.get("standings", [])
      if not standings:
        continue

      entries = standings[0].get("entries", [])
      tabla_liga = db[liga_nombre]["tabla"]

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

        for eq_key in tabla_liga.keys():
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
            break
    except Exception as e:
      print(f"Error actualizando {liga_nombre}: {e}")

  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=4)
  print("¡Base de datos sincronizada con éxito!")


if __name__ == "__main__":
  actualizar_desde_espn()
