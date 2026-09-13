import streamlit as st
import json
import os
import numpy as np
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN BASE Y ESTILO MÓVIL (HORIZONTAL)
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

# Listas Oficiales Verificadas (Incluyendo la Championship de 24 equipos)
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
# 2. BASE DE DATOS Y MEMORIA JSON
# ==========================================
def inicializar_liga_vacia(equipos):
    tabla = {}
    for eq in equipos:
        tabla[eq] = {"PJ": 0, "PG": 0, "PE": 0, "PP": 0, "GF": 0, "GC": 0, "DG": 0, "Pts": 0, "Racha": []}
    return {"tabla": tabla, "historial": []}

def cargar_base_datos():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
        except Exception:
            db = {}
    else:
        db = {}
    
    for liga, equipos in LIGAS_EQUIPOS.items():
        if liga not in db:
            db[liga] = inicializar_liga_vacia(equipos)
        else:
            for eq in equipos:
                if eq not in db[liga]["tabla"]:
                    db[liga]["tabla"][eq] = {"PJ": 0, "PG": 0, "PE": 0, "PP": 0, "GF": 0, "GC": 0, "DG": 0, "Pts": 0, "Racha": []}
    return db

def guardar_base_datos(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = cargar_base_datos()

# ==========================================
# 3. GESTOR DE ARCHIVOS EN SIDEBAR
# ==========================================
st.sidebar.title("📁 Respaldo JSON")
db_bytes = json.dumps(st.session_state.db, ensure_ascii=False, indent=4).encode('utf-8')
st.sidebar.download_button(
    label="💾 Descargar Respaldo JSON",
    data=db_bytes,
    file_name="zohan_pronostic_advanced_db.json",
    mime="application/json"
)

archivo_subido = st.sidebar.file_uploader("📂 Cargar Respaldo", type=["json"])
if archivo_subido is not None:
    try:
        contenido = json.load(archivo_subido)
        for liga in LIGAS_EQUIPOS.keys():
            if liga in contenido:
                st.session_state.db[liga] = contenido[liga]
        guardar_base_datos(st.session_state.db)
        st.sidebar.success("✅ Respaldo restaurado.")
    except Exception:
        st.sidebar.error("❌ Archivo JSON no válido.")

# ==========================================
# 4. MOTORES MATEMÁTICOS AVANZADOS (EMA & Análisis)
# ==========================================
def calcular_ema_racha(racha):
    """Media Móvil Exponencial (EMA) para ponderar más los partidos recientes[span_1](start_span)[span_1](end_span)."""
    if not racha:
        return 0.5
    pesos = np.exp(np.linspace(-1, 0, len(racha)))
    pesos /= pesos.sum()
    puntos_ponderados = np.dot(racha, pesos)
    return min(max(puntos_ponderados / 3.0, 0.0), 1.0)

def analizar_fibonacci_y_ema(racha):
    impulso = calcular_ema_racha(racha)
    
    if impulso >= 0.70:
        diag = "🟢 **Forma Imparable (EMA):** Dinámica reciente muy sólida y en ascenso."
        alerta = "🚨 **ALERTA MÁXIMA (Techo de Rendimiento):** Riesgo de corrección o relajación."
        factor = 0.90
    elif 0.35 <= impulso <= 0.55:
        diag = "🟡 **Rendimiento Estable / Inflexión:** Zona óptima de continuidad o quiebre."
        alerta = "🚀 **PUNTO DE QUIEBRE (Fibonacci 38.2%):** Alta probabilidad de impulso ofensivo."
        factor = 1.12
    elif impulso < 0.30:
        diag = "🔴 **Tendencia Crítica:** Dinámica reciente negativa."
        alerta = "📉 **ZONA BAJISTA:** Requiere reacción táctica urgente."
        factor = 0.92
    else:
        diag = "🛡️ **Consolidación Estable:** Comportamiento regular."
        alerta = "⚖️ **ESTABILIDAD:** Flujo de rendimiento neutral."
        factor = 1.00
        
    return diag, alerta, factor

def generar_radiografia_equipo(nombre, stats, es_local=True):
    """Genera el texto descriptivo del rendimiento del equipo en su faceta local o visitante[span_2](start_span)[span_2](end_span)."""
    pj = max(stats["PJ"], 1)
    gf_partido = stats["GF"] / pj
    gc_partido = stats["GC"] / pj
    condicion = "en condición de local (Casa)" if es_local else "jugando en condición de visitante (Fuera)"
    
    if gf_partido >= 1.6:
        ofensiva = "despliega un volumen ofensivo muy alto, generando ocasiones con gran frecuencia"
    elif gf_partido >= 1.0:
        ofensiva = "mantiene una producción de goles estándar y equilibrada"
    else:
        ofensiva = "muestra serios problemas para concretar ocasiones de gol"
        
    if gc_partido <= 0.8:
        defensa = "exhibe una estructura defensiva sumamente sólida y difícil de vulnerar"
    elif gc_partido <= 1.3:
        defensa = "muestra un comportamiento defensivo regular con desajustes esporádicos"
    else:
        defensa = "deja espacios críticos en defensa que suelen costar goles en contra"
        
    return f"**Radiografía {nombre} ({condicion}):** Acumula {stats['PJ']} partidos registrados, promediando **{gf_partido:.2f} GF** y **{gc_partido:.2f} GC** por encuentro. Tácticamente, el equipo {ofensiva} y {defensa}."

def ejecutar_monte_carlo_avanzado(l_gf, l_gc, v_gf, v_gc, factor_loc, factor_vis, sims=10000):
    """Simulador Monte Carlo avanzado con aislamiento de contexto y calibración[span_3](start_span)[span_3](end_span)."""
    lambda_loc = max((l_gf * 0.5 + v_gc * 0.5) * factor_loc, 0.4)
    mu_vis = max((v_gf * 0.5 + l_gc * 0.5) * factor_vis, 0.4)
    
    goles_l = np.random.poisson(lambda_loc, sims)
    goles_v = np.random.poisson(mu_vis, sims)
    
    vic_loc = np.sum(goles_l > goles_v)
    empates = np.sum(goles_l == goles_v)
    vic_vis = np.sum(goles_l < goles_v)
    
    btts = (goles_l > 0) & (goles_v > 0)
    mas_2_5 = (goles_l + goles_v) > 2.5
    menos_2_5 = ~mas_2_5
    
    return {
        "vic_loc_cnt": vic_loc, "vic_loc_pct": (vic_loc / sims) * 100,
        "emp_cnt": empates, "emp_pct": (empates / sims) * 100,
        "vic_vis_cnt": vic_vis, "vic_vis_pct": (vic_vis / sims) * 100,
        "btts_gana_l": (np.sum(btts & (goles_l > goles_v)) / sims) * 100,
        "btts_gana_v": (np.sum(btts & (goles_l < goles_v)) / sims) * 100,
        "btts_alta": (np.sum(btts & mas_2_5) / sims) * 100,
        "btts_baja": (np.sum(btts & menos_2_5) / sims) * 100,
        "no_btts_baja": (np.sum(~btts & menos_2_5) / sims) * 100
    }

# ==========================================
# 5. INTERFAZ MULTILIGA HORIZONTAL
# ==========================================
st.title("⚽ Zohan Pronostic v2")
st.caption("Motor avanzado con Medias Móviles Exponenciales (EMA), Aislamiento Local/Visita y Simulación de Monte Carlo.")

pestanas_ligas = st.tabs(list(LIGAS_EQUIPOS.keys()))

for i, (nombre_liga, equipos) in enumerate(LIGAS_EQUIPOS.items()):
    with pestanas_ligas[i]:
        tab_pred, tab_reg, tab_tabla = st.tabs([
            "🔮 Predecir Partido", "📝 Registrar Partido", "📊 Tabla / Edición Rápida"
        ])
        
        datos_liga = st.session_state.db[nombre_liga]
        tabla = datos_liga["tabla"]
        
        # 1. PREDECIR PRÓXIMO PARTIDO
        with tab_pred:
            st.subheader("Simulador Avanzado de Partidos")
            col1, col2 = st.columns(2)
            with col1:
                loc = st.selectbox("Local", equipos, key=f"pred_loc_{nombre_liga}")
            with col2:
                vis = st.selectbox("Visitante", [e for e in equipos if e != loc], key=f"pred_vis_{nombre_liga}")
                
            if st.button("🚀 Ejecutar Pronóstico y Análisis Completo", key=f"btn_pred_{nombre_liga}"):
                stats_l, stats_v = tabla[loc], tabla[vis]
                pj_l, pj_v = max(stats_l["PJ"], 1), max(stats_v["PJ"], 1)
                
                l_gf, l_gc = stats_l["GF"] / pj_l, stats_l["GC"] / pj_l
                v_gf, v_gc = stats_v["GF"] / pj_v, stats_v["GC"] / pj_v
                
                diag_l, fibo_l, f_loc = analizar_fibonacci_y_ema(stats_l["Racha"])
                diag_v, fibo_v, f_vis = analizar_fibonacci_y_ema(stats_v["Racha"])
                
                # Despliegue de textos analíticos detallados de ambas facetas
                st.markdown("---")
                st.subheader("📋 Radiografía Táctica de las Dos Facetas")
                st.write(generar_radiografia_equipo(loc, stats_l, es_local=True))
                st.write(generar_radiografia_equipo(vis, stats_v, es_local=False))
                
                st.markdown("---")
                st.subheader("📈 Diagnóstico Dinámico (EMA & Tendencias)")
                st.info(f"**{loc}:** {diag_l} — {fibo_l}")
                st.info(f"**{vis}:** {diag_v} — {fibo_v}")
                
                # Ejecución de Monte Carlo con calibración avanzada
                res = ejecutar_monte_carlo_avanzado(l_gf, l_gc, v_gf, v_gc, f_loc, f_vis)
                
                st.markdown("---")
                st.subheader("👈 Desliza horizontalmente los resultados probabilísticos 👉")
                
                html_cards = f"""
                <div class="horizontal-scroll">
                    <div class="horizontal-card">
                        <h4>🏠 Victoria {loc}</h4>
                        <h2>{res['vic_loc_pct']:.1f}%</h2>
                        <p>{res['vic_loc_cnt']} / 10,000 sims</p>
                    </div>
                    <div class="horizontal-card">
                        <h4>🤝 Empate</h4>
                        <h2>{res['emp_pct']:.1f}%</h2>
                        <p>{res['emp_cnt']} / 10,000 sims</p>
                    </div>
                    <div class="horizontal-card">
                        <h4>🚀 Victoria {vis}</h4>
                        <h2>{res['vic_vis_pct']:.1f}%</h2>
                        <p>{res['vic_vis_cnt']} / 10,000 sims</p>
                    </div>
                    <div class="horizontal-card">
                        <h4>⚽ BTTS y Gana Local</h4>
                        <h2>{res['btts_gana_l']:.1f}%</h2>
                        <p>Ambos marcan + Local</p>
                    </div>
                    <div class="horizontal-card">
                        <h4>⚽ BTTS y Gana Visita</h4>
                        <h2>{res['btts_gana_v']:.1f}%</h2>
                        <p>Ambos marcan + Visita</p>
                    </div>
                    <div class="horizontal-card">
                        <h4>🔥 BTTS y Alta (>2.5)</h4>
                        <h2>{res['btts_alta']:.1f}%</h2>
                        <p>Ambos marcan + Over 2.5</p>
                    </div>
                    <div class="horizontal-card">
                        <h4>🔒 BTTS y Baja (<2.5)</h4>
                        <h2>{res['btts_baja']:.1f}%</h2>
                        <p>Marcador cerrado 1-1</p>
                    </div>
                    <div class="horizontal-card">
                        <h4>🛑 No BTTS y Baja (<2.5)</h4>
                        <h2>{res['no_btts_baja']:.1f}%</h2>
                        <p>Marcador ajustado 0-0 / 1-0</p>
                    </div>
                </div>
                """
                st.markdown(html_cards, unsafe_allow_html=True)

        # 2. REGISTRAR PARTIDO ÚNICO
        with tab_reg:
            st.subheader("Registrar Partido Reciente")
            col_l, col_v = st.columns(2)
            with col_l:
                eq_l = st.selectbox("Equipo Local", equipos, key=f"reg_loc_{nombre_liga}")
                g_l = st.number_input(f"Goles {eq_l}", min_value=0, max_value=20, value=0, key=f"gl_{nombre_liga}")
            with col_v:
                eq_v = st.selectbox("Equipo Visitante", [e for e in equipos if e != eq_l], key=f"reg_vis_{nombre_liga}")
                g_v = st.number_input(f"Goles {eq_v}", min_value=0, max_value=20, value=0, key=f"gv_{nombre_liga}")
                
            if st.button("💾 Guardar Partido", key=f"btn_reg_{nombre_liga}"):
                tabla[eq_l]["PJ"] += 1; tabla[eq_l]["GF"] += g_l; tabla[eq_l]["GC"] += g_v
                tabla[eq_l]["DG"] = tabla[eq_l]["GF"] - tabla[eq_l]["GC"]
                
                tabla[eq_v]["PJ"] += 1; tabla[eq_v]["GF"] += g_v; tabla[eq_v]["GC"] += g_l
                tabla[eq_v]["DG"] = tabla[eq_v]["GF"] - tabla[eq_v]["GC"]
                
                if g_l > g_v:
                    tabla[eq_l]["PG"] += 1; tabla[eq_l]["Pts"] += 3; tabla[eq_l]["Racha"].append(3)
                    tabla[eq_v]["PP"] += 1; tabla[eq_v]["Racha"].append(0)
                elif g_l < g_v:
                    tabla[eq_v]["PG"] += 1; tabla[eq_v]["Pts"] += 3; tabla[eq_v]["Racha"].append(3)
                    tabla[eq_l]["PP"] += 1; tabla[eq_l]["Racha"].append(0)
                else:
                    tabla[eq_l]["PE"] += 1; tabla[eq_l]["Pts"] += 1; tabla[eq_l]["Racha"].append(1)
                    tabla[eq_v]["PE"] += 1; tabla[eq_v]["Pts"] += 1; tabla[eq_v]["Racha"].append(1)
                    
                datos_liga["historial"].append({"local": eq_l, "goles_local": g_l, "visitante": eq_v, "goles_visitante": g_v})
                guardar_base_datos(st.session_state.db)
                st.success(f"¡Guardado! {eq_l} {g_l} - {g_v} {eq_v}")

        # 3. TABLA E INICIALIZACIÓN RÁPIDA
        with tab_tabla:
            st.subheader(f"Tabla de Posiciones - {nombre_liga}")
            df_tabla = pd.DataFrame.from_dict(tabla, orient="index").drop(columns=["Racha"])
            df_tabla = df_tabla.sort_values(by=["Pts", "DG", "GF"], ascending=False)
            df_tabla.index.name = "Equipo"
            st.dataframe(df_tabla, use_container_width=True)
            
            st.markdown("---")
            st.subheader("⚙️ Edición Rápida de Tabla")
            st.caption("Ingresa directamente los acumulados actuales si deseas omitir el registro jornada a jornada.")
            
            eq_edit = st.selectbox("Selecciona Equipo a Modificar", equipos, key=f"eq_edit_{nombre_liga}")
            e_pj = st.number_input("Partidos Jugados (PJ)", min_value=0, value=int(tabla[eq_edit]["PJ"]), key=f"e_pj_{nombre_liga}")
            e_pts = st.number_input("Puntos Totales (Pts)", min_value=0, value=int(tabla[eq_edit]["Pts"]), key=f"e_pts_{nombre_liga}")
            e_gf = st.number_input("Goles a Favor (GF)", min_value=0, value=int(tabla[eq_edit]["GF"]), key=f"e_gf_{nombre_liga}")
            e_gc = st.number_input("Goles en Contra (GC)", min_value=0, value=int(tabla[eq_edit]["GC"]), key=f"e_gc_{nombre_liga}")
            
            if st.button("🔄 Actualizar Datos del Equipo", key=f"btn_edit_{nombre_liga}"):
                tabla[eq_edit]["PJ"] = e_pj
                tabla[eq_edit]["Pts"] = e_pts
                tabla[eq_edit]["GF"] = e_gf
                tabla[eq_edit]["GC"] = e_gc
                tabla[eq_edit]["DG"] = e_gf - e_gc
                guardar_base_datos(st.session_state.db)
                st.success(f"¡Datos de {eq_edit} actualizados correctamente en la tabla!")

