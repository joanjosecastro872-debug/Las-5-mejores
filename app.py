import streamlit as st
import json
import os
import numpy as np
import pandas as pd
from scipy.stats import poisson

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Zohan Pronostic v2 - Análisis Avanzado",
    page_icon="⚽",
    layout="wide"
)

DB_FILE = "zohan_pronostic_db.json"

# ==========================================
# BASE DE DATOS OFICIAL DE LIGAS Y EQUIPOS
# ==========================================
TEAMS_DATA = {
    "LaLiga": [
        "Athletic Club", "Atlético de Madrid", "CA Osasuna", "Deportivo Alavés",
        "Elche CF", "FC Barcelona", "Getafe CF", "Levante UD", "Málaga CF",
        "Rayo Vallecano", "RCD Espanyol", "Real Betis", "Real Celta de Vigo",
        "Real Deportivo de La Coruña", "Real Madrid", "Real Racing Club de Santander",
        "Real Sociedad", "Sevilla FC", "Valencia CF", "Villarreal CF"
    ],
    "Serie A": [
        "AC Milan", "AC Monza", "AS Roma", "Atalanta BC", "Bologna FC",
        "Cagliari Calcio", "Como 1907", "Fiorentina", "Frosinone Calcio",
        "Genoa CFC", "Inter de Milán", "Juventus", "Parma Calcio 1913",
        "Sassuolo", "SS Lazio", "SSC Napoli", "Torino FC", "Udinese Calcio",
        "US Lecce", "Venezia"
    ],
    "Premier League": [
        "Arsenal FC", "Aston Villa FC", "AFC Bournemouth", "Brentford FC",
        "Brighton & Hove Albion", "Chelsea FC", "Coventry City", "Crystal Palace",
        "Everton FC", "Fulham FC", "Hull City", "Ipswich Town",
        "Leeds United", "Liverpool FC", "Manchester City", "Manchester United",
        "Newcastle United", "Nottingham Forest", "Sunderland AFC", "Tottenham Hotspur"
    ],
    "Championship": [
        "Birmingham City", "Blackburn Rovers", "Bolton Wanderers", "Bristol City",
        "Burnley FC", "Cardiff City", "Charlton Athletic", "Derby County",
        "Lincoln City", "Middlesbrough FC", "Millwall FC", "Norwich City",
        "Portsmouth FC", "Preston North End", "Queens Park Rangers (QPR)",
        "Sheffield United", "Southampton FC", "Stoke City", "Swansea City",
        "Watford FC", "West Bromwich Albion", "West Ham United",
        "Wolverhampton Wanderers", "Wrexham AFC"
    ],
    "Bundesliga": [
        "FC Union Berlin", "FSV Mainz 05", "Bayer 04 Leverkusen", "Bayern de Múnich",
        "Borussia Dortmund", "Borussia Mönchengladbach", "Eintracht Frankfurt",
        "FC Augsburgo", "FC Schalke 04", "FC Köln", "Hamburgo SV",
        "RasenBallsport Leipzig (RB Leipzig)", "SC Friburgo", "SC Paderborn 07",
        "SV Elversberg", "TSG 1899 Hoffenheim", "VfB Stuttgart", "Werder Bremen"
    ],
    "Ligue 1": [
        "AJ Auxerre", "Angers SCO", "AS Monaco", "ES Troyes AC",
        "FC Lorient", "Le Havre AC", "Le Mans FC", "LOSC Lille",
        "OGC Niza", "Olympique de Marsella", "Olympique de Lyon",
        "Paris FC", "París Saint-Germain (PSG)", "Racing Club de Lens",
        "Racing Club de Estrasburgo", "Stade Brestois 29", "Stade Rennais FC", "Toulouse"
    ]
}

def init_db():
    db = {}
    for league, teams in TEAMS_DATA.items():
        db[league] = {}
        for t in teams:
            db[league][t] = {
                "victorias": 0,
                "empates": 0,
                "derrotas": 0,
                "gf": 0,
                "gc": 0,
                "ultimos_resultados": []
            }
    return db

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for league, teams in TEAMS_DATA.items():
                    if league not in data:
                        data[league] = {}
                    for t in teams:
                        if t not in data[league]:
                            data[league][t] = {
                                "victorias": 0,
                                "empates": 0,
                                "derrotas": 0,
                                "gf": 0,
                                "gc": 0,
                                "ultimos_resultados": []
                            }
                return data
        except Exception:
            return init_db()
    else:
        db = init_db()
        save_db(db)
        return db

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if "db" not in st.session_state:
    st.session_state.db = load_db()

# ==========================================
# CÁLCULOS MATEMÁTICOS Y FIBONACCI
# ==========================================
FIBONACCI = [1, 1, 2, 3, 5, 8, 13, 21]

def calculate_fibonacci_momentum(results_list):
    if not results_list:
        return 0.0
    recent = results_list[-len(FIBONACCI):]
    weights = FIBONACCI[:len(recent)]
    score_map = {'V': 3, 'E': 1, 'D': 0}
    weighted_score = sum(score_map.get(res, 0) * w for res, w in zip(recent, weights))
    max_score = sum(3 * w for w in weights)
    return round((weighted_score / max_score) * 100, 2) if max_score > 0 else 0.0

def calculate_poisson_matrix(home_data, away_data, max_goals=6):
    pj_h = max(1, home_data.get("victorias", 0) + home_data.get("empates", 0) + home_data.get("derrotas", 0))
    pj_a = max(1, away_data.get("victorias", 0) + away_data.get("empates", 0) + away_data.get("derrotas", 0))

    gf_h_avg = home_data.get("gf", 0) / pj_h
    gc_h_avg = home_data.get("gc", 0) / pj_h

    gf_a_avg = away_data.get("gf", 0) / pj_a
    gc_a_avg = away_data.get("gc", 0) / pj_a

    lambda_home = max(0.25, (gf_h_avg * 0.6 + gc_a_avg * 0.4) * 1.12)
    lambda_away = max(0.25, (gf_a_avg * 0.6 + gc_h_avg * 0.4) * 0.88)

    matrix = np.zeros((max_goals, max_goals))
    for i in range(max_goals):
        for j in range(max_goals):
            matrix[i, j] = poisson.pmf(i, lambda_home) * poisson.pmf(j, lambda_away)
            
    return matrix, lambda_home, lambda_away

# ==========================================
# INTERFAZ DE USUARIO STREAMLIT
# ==========================================
st.title("⚽ Zohan Pronostic v2 - Análisis Avanzado")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚡ Ingreso Directo", 
    "📊 Matriz de Poisson", 
    "🎲 Monte Carlo (10k)", 
    "🌀 Racha (Fibonacci)", 
    "💾 Base de Datos JSON"
])

# ------------------------------------------
# TAB 1: CARGA RÁPIDA DE FOJA Y GOLES
# ------------------------------------------
with tab1:
    st.header("⚡ Carga Rápida (Ganados, Empatados, Perdidos y Goles)")
    st.caption("Actualiza directamente la foja general y goles acumulados de cada equipo.")
    
    col_l, col_t = st.columns(2)
    with col_l:
        selected_league = st.selectbox("Selecciona la Liga", list(st.session_state.db.keys()), key="entry_league")
    with col_t:
        teams_list = list(st.session_state.db[selected_league].keys())
        selected_team = st.selectbox("Selecciona el Equipo", teams_list, key="entry_team")

    team_data = st.session_state.db[selected_league][selected_team]

    with st.form("quick_entry_form"):
        st.subheader(f"Datos Registrados: **{selected_team}**")
        
        c1, c2, c3 = st.columns(3)
        v = c1.number_input("Partidos Ganados (V)", min_value=0, value=team_data.get("victorias", 0))
        e = c2.number_input("Partidos Empatados (E)", min_value=0, value=team_data.get("empates", 0))
        d = c3.number_input("Partidos Perdidos (D)", min_value=0, value=team_data.get("derrotas", 0))
        
        pj_totales = v + e + d
        pts_totales = (v * 3) + e
        
        st.info(f"📊 **Partidos Jugados (PJ):** {pj_totales} | 🏆 **Puntos Totales:** {pts_totales}")
        
        cg1, cg2 = st.columns(2)
        gf = cg1.number_input("Goles a Favor Totales (GF)", min_value=0, value=team_data.get("gf", 0))
        gc = cg2.number_input("Goles en Contra Totales (GC)", min_value=0, value=team_data.get("gc", 0))

        streak_str = ",".join(team_data.get("ultimos_resultados", []))
        streak_input = st.text_input("Últimos resultados (Separados por comas: V, E, D)", value=streak_str)

        submitted = st.form_submit_button("💾 Guardar Datos del Equipo")
        if submitted:
            new_streak = [x.strip().upper() for x in streak_input.split(",") if x.strip() in ['V', 'E', 'D', 'v', 'e', 'd']]
            st.session_state.db[selected_league][selected_team] = {
                "victorias": v,
                "empates": e,
                "derrotas": d,
                "gf": gf,
                "gc": gc,
                "ultimos_resultados": new_streak
            }
            save_db(st.session_state.db)
            st.success(f"¡{selected_team} actualizado correctamente!")

# ------------------------------------------
# TAB 2: MATRIZ DE POISSON
# ------------------------------------------
with tab2:
    st.header("📊 Matriz de Probabilidades (Poisson)")
    
    col_l2, col_h, col_a = st.columns(3)
    with col_l2:
        l_p = st.selectbox("Liga", list(st.session_state.db.keys()), key="p_league")
    with col_h:
        home_t = st.selectbox("Equipo Local", list(st.session_state.db[l_p].keys()), key="p_home")
    with col_a:
        away_options = [t for t in st.session_state.db[l_p].keys() if t != home_t]
        away_t = st.selectbox("Equipo Visitante", away_options, key="p_away")

    h_data = st.session_state.db[l_p][home_t]
    a_data = st.session_state.db[l_p][away_t]

    matrix, lh, la = calculate_poisson_matrix(h_data, a_data)

    home_win_prob = np.sum(np.tril(matrix, -1)) * 100
    draw_prob = np.sum(np.diag(matrix)) * 100
    away_win_prob = np.sum(np.triu(matrix, 1)) * 100

    st.subheader(f"Encuentro: **{home_t}** vs **{away_t}**")
    m1, m2, m3 = st.columns(3)
    m1.metric("Victoria Local", f"{home_win_prob:.2f}%")
    m2.metric("Empate", f"{draw_prob:.2f}%")
    m3.metric("Victoria Visitante", f"{away_win_prob:.2f}%")

    st.write("---")
    df_matrix = pd.DataFrame(matrix, columns=[f"Vis {i}" for i in range(6)], index=[f"Loc {i}" for i in range(6)])
    st.dataframe(df_matrix.style.highlight_max(axis=None, color='lightgreen'))

# ------------------------------------------
# TAB 3: SIMULACIÓN MONTE CARLO
# ------------------------------------------
with tab3:
    st.header("🎲 Simulación Monte Carlo (10,000 Iteraciones)")
    
    col_mc_l, col_mc_h, col_mc_a = st.columns(3)
    with col_mc_l:
        l_mc = st.selectbox("Liga", list(st.session_state.db.keys()), key="mc_league")
    with col_mc_h:
        home_mc = st.selectbox("Equipo Local", list(st.session_state.db[l_mc].keys()), key="mc_home")
    with col_mc_a:
        away_mc_opts = [t for t in st.session_state.db[l_mc].keys() if t != home_mc]
        away_mc = st.selectbox("Equipo Visitante", away_mc_opts, key="mc_away")

    h_data_mc = st.session_state.db[l_mc][home_mc]
    a_data_mc = st.session_state.db[l_mc][away_mc]
    _, lh_mc, la_mc = calculate_poisson_matrix(h_data_mc, a_data_mc)

    if st.button("🚀 Ejecutar 10,000 Simulaciones"):
        sim_home = np.random.poisson(lh_mc, 10000)
        sim_away = np.random.poisson(la_mc, 10000)
        
        h_wins = np.sum(sim_home > sim_away)
        draws = np.sum(sim_home == sim_away)
        a_wins = np.sum(sim_home < sim_away)
        
        over25 = np.sum((sim_home + sim_away) > 2.5)
        btts = np.sum((sim_home > 0) & (sim_away > 0))

        st.subheader(f"Resultados de la Simulación: {home_mc} vs {away_mc}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Victoria Local (%)", f"{(h_wins/10000)*100:.2f}%")
        c2.metric("Empate (%)", f"{(draws/10000)*100:.2f}%")
        c3.metric("Victoria Visitante (%)", f"{(a_wins/10000)*100:.2f}%")

        c4, c5 = st.columns(2)
        c4.metric("Más de 2.5 Goles", f"{(over25/10000)*100:.2f}%")
        c5.metric("Ambos Anotan (BTTS)", f"{(btts/10000)*100:.2f}%")

# ------------------------------------------
# TAB 4: FIBONACCI MOMENTUM
# ------------------------------------------
with tab4:
    st.header("🌀 Tabla de Posiciones y Racha (Fibonacci)")
    l_fib = st.selectbox("Liga a Analizar", list(st.session_state.db.keys()), key="fib_league")
    
    fib_list = []
    for team, data in st.session_state.db[l_fib].items():
        mom = calculate_fibonacci_momentum(data.get("ultimos_resultados", []))
        v = data.get("victorias", 0)
        e = data.get("empates", 0)
        d = data.get("derrotas", 0)
        pts = (v * 3) + e
        pj = v + e + d
        dg = data.get("gf", 0) - data.get("gc", 0)
        
        fib_list.append({
            "Equipo": team,
            "PJ": pj,
            "Puntos": pts,
            "DG": dg,
            "Momentum (%)": mom,
            "GF": data.get("gf", 0),
            "GC": data.get("gc", 0),
            "Racha": ", ".join(data.get("ultimos_resultados", []))
        })
    
    df_fib = pd.DataFrame(fib_list).sort_values(by=["Puntos", "DG"], ascending=[False, False])
    st.dataframe(df_fib, use_container_width=True)

# ------------------------------------------
# TAB 5: GESTIÓN JSON
# ------------------------------------------
with tab5:
    st.header("💾 Importar y Exportar Base de Datos JSON")

    json_data = json.dumps(st.session_state.db, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 Descargar zohan_pronostic_db.json",
        file_name="zohan_pronostic_db.json",
        mime="application/json",
        data=json_data
    )

    file_up = st.file_uploader("Subir archivo zohan_pronostic_db.json", type=["json"])
    if file_up is not None:
        try:
            db_loaded = json.load(file_up)
            st.session_state.db = db_loaded
            save_db(db_loaded)
            st.success("¡Base de datos cargada e integrada con éxito!")
        except Exception as err:
            st.error(f"Error al procesar el archivo: {err}")

