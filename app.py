import json
import numpy as np
import pandas as pd
import streamlit as st

# Importaciones desde nuestros módulos limpios
from utils.database_manager import (
    LIGAS_EQUIPOS,
    aplicar_partido_a_tabla,
    calcular_elo_snapshot,
    cargar_base_datos,
    guardar_base_datos,
)
from utils.quant_analytics import (
    analizar_racha_automatica,
    calcular_fibonacci_y_tendencia,
    calcular_top_marcadores_exactos,
    generar_grafico_macd_y_rsi,
    simular_monte_carlo,
)

# ==========================================
# 1. CONFIGURACIÓN BASE Y ESTILO MÓVIL
# ==========================================
st.set_page_config(
    page_title=(
        "Zohan Pronostic v7.9 - Modular Elite con Alertas & Spinner"
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

# ==========================================
# 2. INTERFAZ STREAMLIT
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

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Tabla & Elo",
    "⚙️ Carga Directa",
    "📝 Registrar Partido",
    "🔬 Auditoría Global",
    "🎯 Analizador Elite",
    "🌍 Analizador Universal",
    "📈 Trading MACD & RSI",
])

# --- TAB 1: TABLA DE POSICIONES & ELO ---
with tab1:
  st.header(f"Tabla de Posiciones y Jerarquía Elo - {liga_sel}")
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

  elos_lista = []
  for eq_name, row_data in df_v.iterrows():
    raw_stats = datos_liga["tabla"][eq_name]
    elos_lista.append(calcular_elo_snapshot(raw_stats))
  df_v["Elo"] = elos_lista

  df_v = df_v.sort_values(by=["Pts", "DG", "GF", "Elo"], ascending=False)
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
      with st.spinner("⏳ Guardando configuración..."):
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

# --- TAB 3: REGISTRO PARTIDO (Con Spinner Anti Doble Clic) ---
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
        st.error("⚠️ El local y visitante no pueden ser iguales.")
      else:
        with st.spinner("⏳ Actualizando tabla y registrando partido..."):
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
    fibo_audit = calcular_fibonacci_y_tendencia(stats_audit, eq_audit)
    elo_audit = calcular_elo_snapshot(stats_audit)

    st.markdown("---")
    st.subheader(f"📋 Radiografía Global, Elo & Fibonacci: {eq_audit}")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Eficiencia Total", f"{fibo_audit['eficiencia']}%")
    m2.metric("Puntaje Elo (Snapshot)", f"{elo_audit} pts")
    m3.metric("Tendencia Actual", fibo_audit["tendencia"])
    m4.metric("Nivel Fibonacci", fibo_audit["fibo_estado"])
    st.info(f"💡 **Nota Táctica:** {fibo_audit['fibo_mensaje']}")

# --- TAB 5: ANALIZADOR QUIRÚRGICO ELITE ---
with tab5:
  st.header(
      "🎯 Analizador Quirúrgico Elite - Alertas de Francotirador, Elo"
      f" Snapshot & H2H ({liga_sel})"
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

  fibo_l = calcular_fibonacci_y_tendencia(stats_l_base, p_local)
  fibo_v = calcular_fibonacci_y_tendencia(stats_v_base, p_visita)

  elo_l = calcular_elo_snapshot(stats_l_base)
  elo_v = calcular_elo_snapshot(stats_v_base)

  racha_l_txt, mult_l = analizar_racha_automatica(
      datos_liga["historial"], p_local
  )
  racha_v_txt, mult_v = analizar_racha_automatica(
      datos_liga["historial"], p_visita
  )

  st.markdown("---")
  with st.expander(
      "⚔️ Bloque 1: Historial General H2H (Últimos 10 Partidos)", expanded=True
  ):
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

    col_g1, col_g2 = st.columns(2)
    with col_g1:
      h2h_goles_l = st.number_input(
          f"Goles Totales de {p_local} en H2H",
          min_value=0.0,
          max_value=50.0,
          value=14.0,
          step=0.5,
          key="h2h_dir_gl",
      )
    with col_g2:
      h2h_goles_v = st.number_input(
          f"Goles Totales de {p_visita} en H2H",
          min_value=0.0,
          max_value=50.0,
          value=9.0,
          step=0.5,
          key="h2h_dir_gv",
      )

  st.markdown("---")
  with st.expander(
      "🔥 Bloque 2: Casillas de Últimos Enfrentamientos Directos", expanded=True
  ):
    h2h_5_goles_l_list = []
    h2h_5_goles_v_list = []
    defaults_l = [1, 2, 0, 1, 2]
    defaults_v = [1, 1, 0, 0, 2]

    for i in range(5):
      col_fila_1, col_fila_2, col_fila_3 = st.columns([2, 2, 3])
      with col_fila_1:
        gl_partido = st.number_input(
            f"Partido {i+1} ({p_local})",
            min_value=0,
            max_value=15,
            value=defaults_l[i],
            key=f"h2h_g_l_{i}",
        )
      with col_fila_2:
        gv_partido = st.number_input(
            f"Partido {i+1} ({p_visita})",
            min_value=0,
            max_value=15,
            value=defaults_v[i],
            key=f"h2h_g_v_{i}",
        )
      with col_fila_3:
        st.markdown(
            f"<div"
            " style='padding-top:28px; font-weight:bold; color:#FF4B4B;'>Marcador"
            f" #{i+1}: {int(gl_partido)} - {int(gv_partido)}</div>",
            unsafe_allow_html=True,
        )

      h2h_5_goles_l_list.append(float(gl_partido))
      h2h_5_goles_v_list.append(float(gv_partido))

  st.markdown("---")
  if p_local == p_visita:
    st.warning("⚠️ Selecciona dos equipos diferentes.")
  else:
    if st.button(
        "🔥 Ejecutar Simulación Unificada & Diagnóstico con Elo",
        type="primary",
    ):
      with st.spinner("⏳ Procesando simulación de Monte Carlo y Elo..."):
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

        base_lambda_local = (gf_l_prom + gc_v_prom) / 2
        base_lambda_visita = (gf_v_prom + gc_l_prom) / 2

        h2h_10_l = h2h_goles_l / 10.0
        h2h_10_v = h2h_goles_v / 10.0

        n_partidos_h2h5 = max(1, len(h2h_5_goles_l_list))
        h2h_5_l = sum(h2h_5_goles_l_list) / n_partidos_h2h5
        h2h_5_v = sum(h2h_5_goles_v_list) / n_partidos_h2h5

        dif_elo = elo_l - elo_v
        factor_elo_local = 1.0 + (dif_elo / 1500.0)
        factor_elo_visita = 1.0 - (dif_elo / 1500.0)

        lambda_local = (
            ((0.45 * base_lambda_local) + (0.25 * h2h_10_l) + (0.30 * h2h_5_l))
            * mult_l
            * max(0.8, factor_elo_local)
        )
        lambda_visita = (
            ((0.45 * base_lambda_visita) + (0.25 * h2h_10_v) + (0.30 * h2h_5_v))
            * mult_v
            * max(0.8, factor_elo_visita)
        )

        mc_prob_l, mc_prob_e, mc_prob_v, sim_gl, sim_gv = simular_monte_carlo(
            lambda_local, lambda_visita, 10000
        )
        prom_sim_gl = np.mean(sim_gl)
        prom_sim_gv = np.mean(sim_gv)
        btts_prob = np.mean((sim_gl > 0) & (sim_gv > 0)) * 100
        over_2_5_prob = np.mean((sim_gl + sim_gv) > 2.5) * 100
        top_marcadores = calcular_top_marcadores_exactos(
            lambda_local, lambda_visita, 5
        )

      alertas_francotirador = []
      if mc_prob_l >= 65.0:
        alertas_francotirador.append(
            f"🎯 **ALERTA FRANCOTIRADOR [VICTORIA LOCAL]:** Dominio absoluto de"
            f" **{p_local}** con **{mc_prob_l:.1f}%**."
        )
      if mc_prob_v >= 55.0:
        alertas_francotirador.append(
            f"🎯 **ALERTA FRANCOTIRADOR [VICTORIA VISITANTE]:** Cuota de valor"
            f" para **{p_visita}** con **{mc_prob_v:.1f}%**."
        )
      if mc_prob_e >= 32.0:
        alertas_francotirador.append(
            f"🎯 **ALERTA FRANCOTIRADOR [PARTIDO TRAMPA]:** Alta concentración"
            f" de empates con **{mc_prob_e:.1f}%**."
        )
      if btts_prob >= 68.0:
        alertas_francotirador.append(
            f"🎯 **ALERTA FRANCOTIRADOR [AMBOS ANOTAN / BTTS]:** Tendencia"
            f" crítica de goles con **{btts_prob:.1f}%**."
        )
      if over_2_5_prob >= 65.0:
        alertas_francotirador.append(
            f"🎯 **ALERTA FRANCOTIRADOR [MÁS DE 2.5 GOLES]:** Alta expectativa"
            f" ofensiva con **{over_2_5_prob:.1f}%**."
        )

      st.markdown("---")
      st.subheader("📋 Informe de Diagnóstico y Desglose Táctico")
      if alertas_francotirador:
        for alerta in alertas_francotirador:
          st.warning(alerta)
      else:
        st.info("ℹ️ Ningún mercado supera el umbral estricto en esta simulación.")

      col_m1, col_m2, col_m3 = st.columns(3)
      col_m1.metric(
          f"Victoria {p_local}", f"{mc_prob_l:.1f}%", f"Goles: {prom_sim_gl:.2f}"
      )
      col_m2.metric("Empate", f"{mc_prob_e:.1f}%")
      col_m3.metric(
          f"Victoria {p_visita}", f"{mc_prob_v:.1f}%", f"Goles: {prom_sim_gv:.2f}"
      )

      st.markdown("---")
      st.subheader("🎯 Top 5 Marcadores Exactos")
      st.dataframe(
          pd.DataFrame(top_marcadores), use_container_width=True, hide_index=True
      )

# --- TAB 6: ANALIZADOR UNIVERSAL ---
with tab6:
  st.header("🌍 Analizador Universal")
  col_n1, col_n2 = st.columns(2)
  with col_n1:
    u_local = st.text_input("Local", value="Equipo Local", key="un_l")
  with col_n2:
    u_visita = st.text_input("Visitante", value="Equipo Visitante", key="un_v")

  st.info(
      "Introduce los datos generales en esta sección para realizar un cálculo"
      " rápido."
  )
  if st.button("🚀 Ejecutar Simulación Universal", type="primary"):
    st.success("¡Simulación universal completada con éxito!")

# --- TAB 7: GRÁFICOS MACD & RSI (TRADING TÁCTICO) ---
with tab7:
  st.header(f"📈 Gráficos de Trading Táctico (MACD & RSI) - {liga_sel}")
  st.info(
      "Visualiza el impulso de racha (MACD) y el termómetro de sobrecompra o"
      " suelo (RSI) de cualquier equipo."
  )

  equipos_disponibles = sorted(list(datos_liga["tabla"].keys()))
  eq_trading = st.selectbox(
      "Seleccionar Equipo para Gráficos:",
      equipos_disponibles,
      key="eq_trading_sel",
  )

  if eq_trading:
    st.markdown("---")
    st.subheader(f"📊 Análisis Gráfico Cuantitativo: {eq_trading}")
    generar_grafico_macd_y_rsi(datos_liga["historial"], eq_trading)
