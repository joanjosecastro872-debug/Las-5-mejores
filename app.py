def cargar_base_datos():
  data = {}
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    except Exception:
      data = {}

   estructura_base = obtener_estructura_equipo()

  for liga in LEAGUES_ESPN_SLUGS.keys():
    if liga not in data or not isinstance(data[liga], dict):
      data[liga] = {"tabla": {}, "historial": []}
    
    # Asegurar que cada equipo tenga todas las claves necesarias
    tabla = data[liga].get("tabla", {})
    for eq, stats in tabla.items():
      for k, v in estructura_base.items():
        if k not in stats:
          stats[k] = v
      tabla[eq] = stats
    data[liga]["tabla"] = tabla

  if all(len(data[l].get("tabla", {})) == 0 for l in LEAGUES_ESPN_SLUGS.keys()):
    data = sincronizar_con_espn(data)
    guardar_base_datos(data)

  return data
