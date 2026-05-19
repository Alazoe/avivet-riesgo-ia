"""
AviVet — Escala de Riesgo de Influenza Aviar
Herramienta de evaluación geoespacial para planteles avícolas.
"""
from __future__ import annotations

import math
from datetime import date
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from geopy.distance import geodesic
from streamlit_folium import st_folium

from risk_calculator import FarmType, RiskScore, calculate_risk
from water_fetcher import fetch_water_bodies

# ── Configuración ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Riesgo IA Aviar — AviVet",
    page_icon="🦠",
    layout="wide",
)

DB_PATH = Path("data/planteles.csv")
DB_COLS = ["nombre", "lat", "lon", "tipo", "notas"]
FARM_SEARCH_RADIUS_KM = 5.0  # radio para contar planteles cercanos


# ── Base de datos de planteles ─────────────────────────────────────────────────

def load_db() -> pd.DataFrame:
    if DB_PATH.exists() and DB_PATH.stat().st_size > 0:
        return pd.read_csv(DB_PATH)
    return pd.DataFrame(columns=DB_COLS)


def save_db(df: pd.DataFrame) -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(DB_PATH, index=False)


def nearby_farms(lat: float, lon: float, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    mask = df.apply(
        lambda r: geodesic((lat, lon), (r["lat"], r["lon"])).km <= FARM_SEARCH_RADIUS_KM,
        axis=1,
    )
    return df[mask]


# ── Mapa Folium ────────────────────────────────────────────────────────────────

def build_map(
    lat: float,
    lon: float,
    score: RiskScore,
    water_features: list[dict],
    db: pd.DataFrame,
    eval_name: str,
) -> folium.Map:
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="CartoDB positron")

    # Anillos de buffer
    ring_cfg = [
        (500,  "#E74C3C", 0.10, "Radio 500 m — riesgo muy alto"),
        (2000, "#E67E22", 0.07, "Radio 2 km — riesgo alto"),
        (5000, "#F1C40F", 0.04, "Radio 5 km — radio de búsqueda"),
    ]
    for radius, color, opacity, tooltip in ring_cfg:
        folium.Circle(
            location=[lat, lon],
            radius=radius,
            color=color,
            weight=1.5,
            fill=True,
            fill_color=color,
            fill_opacity=opacity,
            tooltip=tooltip,
        ).add_to(m)

    # Cuerpos de agua (hasta los 8 más cercanos)
    for w in water_features[:8]:
        label = w["name"] or w["water_type"]
        folium.CircleMarker(
            location=[w["lat"], w["lon"]],
            radius=7,
            color="#1A6EBF",
            fill=True,
            fill_color="#5DADE2",
            fill_opacity=0.75,
            tooltip=f"💧 {label} ({w['dist_km']} km)",
        ).add_to(m)

    # Línea al agua más cercana
    if water_features:
        nearest = water_features[0]
        folium.PolyLine(
            locations=[[lat, lon], [nearest["lat"], nearest["lon"]]],
            color="#1A6EBF",
            weight=1.5,
            dash_array="6",
            tooltip=f"Dist. mínima al agua: {nearest['dist_km']} km",
        ).add_to(m)

    # Otros planteles registrados en la DB (dentro del radio)
    near = nearby_farms(lat, lon, db)
    for _, row in near.iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            tooltip=f"🏭 {row['nombre']} — {row['tipo']}",
            icon=folium.Icon(color="gray", icon="home", prefix="fa"),
        ).add_to(m)

    # Plantel evaluado
    folium.Marker(
        location=[lat, lon],
        tooltip=f"{score.tier_emoji} {eval_name} — {score.tier} ({score.total}/12)",
        popup=folium.Popup(
            f"<b>{eval_name}</b><br>"
            f"Tier: <b>{score.tier_emoji} {score.tier}</b><br>"
            f"Puntaje: <b>{score.total}/12</b><br>"
            f"Agua más cercana: {score.water_distance_km:.2f} km",
            max_width=200,
        ),
        icon=folium.Icon(color=score.tier_folium_color, icon="warning-sign"),
    ).add_to(m)

    return m


# ── Helpers de UI ──────────────────────────────────────────────────────────────

def score_card(score: RiskScore) -> None:
    bg = score.tier_color
    st.markdown(
        f"""
        <div style="
            background:{bg}22;
            border:2px solid {bg};
            border-radius:12px;
            padding:18px 24px;
            text-align:center;
        ">
            <span style="font-size:2.8rem;">{score.tier_emoji}</span>
            <h2 style="margin:4px 0;color:{bg};">RIESGO {score.tier}</h2>
            <p style="font-size:1.6rem;margin:0;"><b>{score.total} / 12 puntos</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def breakdown_table(score: RiskScore) -> None:
    rows = ""
    for factor, pts, max_pts in score.breakdown:
        bar_pct = int(pts / max_pts * 100)
        bar_color = "#E74C3C" if pts >= 3 else "#E67E22" if pts >= 2 else "#2ECC71"
        rows += f"""
        <tr>
            <td style="padding:6px 8px;">{factor}</td>
            <td style="padding:6px 8px;text-align:center;font-weight:bold;">{pts}/{max_pts}</td>
            <td style="padding:6px 8px;width:120px;">
                <div style="background:#eee;border-radius:4px;height:12px;">
                    <div style="background:{bar_color};width:{bar_pct}%;height:12px;border-radius:4px;"></div>
                </div>
            </td>
        </tr>"""

    st.markdown(
        f"""
        <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
            <thead>
                <tr style="background:#f0f0f0;">
                    <th style="padding:6px 8px;text-align:left;">Factor</th>
                    <th style="padding:6px 8px;">Pts</th>
                    <th style="padding:6px 8px;">Nivel</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


# ── Páginas ────────────────────────────────────────────────────────────────────

def page_evaluation(db: pd.DataFrame) -> None:
    st.header("Evaluación de riesgo")

    col_form, col_map = st.columns([1, 2], gap="large")

    with col_form:
        st.subheader("Datos del plantel")
        nombre = st.text_input("Nombre del plantel", value="Mi plantel")
        lat    = st.number_input("Latitud",  value=-39.8196, format="%.6f",
                                 help="Latitud decimal (ej. -39.8196 para Valdivia)")
        lon    = st.number_input("Longitud", value=-73.2452, format="%.6f",
                                 help="Longitud decimal (ej. -73.2452 para Valdivia)")
        farm_type = st.selectbox(
            "Tipo de producción",
            options=[ft.value for ft in FarmType],
        )
        manual_farms = st.number_input(
            "Planteles industriales identificados visualmente (radio 5 km)",
            min_value=0, max_value=20, value=0,
            help="Planteles que hayas identificado en satélite o por conocimiento local "
                 "(no registrados en la base de datos).",
        )
        eval_date = st.date_input("Fecha de evaluación", value=date.today())

        run = st.button("⚡ Calcular riesgo", type="primary", use_container_width=True)

    # Estado de sesión para persistir resultados entre rerenders
    if "result" not in st.session_state:
        st.session_state.result = None

    if run:
        with st.spinner("Consultando cuerpos de agua (OpenStreetMap)…"):
            nearest_km, water_features = fetch_water_bodies(lat, lon)

        # Planteles cercanos = registrados en DB + identificados manualmente
        db_nearby_count = len(nearby_farms(lat, lon, db))
        total_nearby    = db_nearby_count + manual_farms

        score = calculate_risk(
            water_distance_km=nearest_km if math.isfinite(nearest_km) else 6.0,
            nearby_farms=total_nearby,
            farm_type=FarmType(farm_type),
            eval_date=eval_date,
        )
        st.session_state.result = {
            "lat": lat, "lon": lon, "nombre": nombre,
            "score": score, "water": water_features,
            "nearest_km": nearest_km,
            "db_nearby": db_nearby_count,
        }

    with col_map:
        res = st.session_state.result
        if res is None:
            # Mapa base vacío centrado en Valdivia
            m = folium.Map(location=[-39.8196, -73.2452], zoom_start=10,
                           tiles="CartoDB positron")
            st.caption("Completa el formulario y presiona **Calcular riesgo** para ver el resultado.")
        else:
            score = res["score"]

            # Resultado principal
            st.subheader("Resultado")
            score_card(score)
            st.write("")
            breakdown_table(score)

            # Detalle agua
            if math.isfinite(res["nearest_km"]):
                st.caption(
                    f"💧 Agua más cercana: **{res['nearest_km']:.2f} km** "
                    f"({len(res['water'])} cuerpos de agua encontrados en 6 km)"
                )
            else:
                st.caption("💧 No se encontraron cuerpos de agua dentro de 6 km.")

            if res["db_nearby"] > 0:
                st.caption(
                    f"🏭 Planteles en base de datos a ≤5 km: **{res['db_nearby']}**"
                )

            m = build_map(
                res["lat"], res["lon"], score,
                res["water"], db, res["nombre"],
            )

        st_folium(m, width=700, height=480, returned_objects=[])


def page_database(db: pd.DataFrame) -> pd.DataFrame:
    st.header("Base de datos de planteles")

    tab_view, tab_add = st.tabs(["📋 Ver planteles", "➕ Agregar plantel"])

    with tab_view:
        if db.empty:
            st.info("Aún no hay planteles registrados. Agrega el primero en la pestaña de arriba.")
        else:
            st.dataframe(db, use_container_width=True)

            # Mini mapa con todos los planteles
            if not db.empty:
                center_lat = db["lat"].mean()
                center_lon = db["lon"].mean()
                m = folium.Map(location=[center_lat, center_lon], zoom_start=9,
                               tiles="CartoDB positron")
                for _, row in db.iterrows():
                    folium.Marker(
                        location=[row["lat"], row["lon"]],
                        tooltip=f"🏭 {row['nombre']} — {row['tipo']}",
                        icon=folium.Icon(color="blue", icon="home", prefix="fa"),
                    ).add_to(m)
                st_folium(m, width=700, height=360, returned_objects=[])

            # Eliminar plantel
            st.write("---")
            to_delete = st.selectbox("Eliminar plantel", ["— seleccionar —"] + db["nombre"].tolist())
            if st.button("🗑️ Eliminar", type="secondary"):
                if to_delete != "— seleccionar —":
                    db = db[db["nombre"] != to_delete].reset_index(drop=True)
                    save_db(db)
                    st.success(f"Plantel «{to_delete}» eliminado.")
                    st.rerun()

    with tab_add:
        with st.form("add_farm"):
            st.subheader("Nuevo plantel")
            f_nombre = st.text_input("Nombre *")
            c1, c2   = st.columns(2)
            f_lat    = c1.number_input("Latitud *",  value=-39.82, format="%.6f")
            f_lon    = c2.number_input("Longitud *", value=-73.24, format="%.6f")
            f_tipo   = st.selectbox("Tipo", [ft.value for ft in FarmType])
            f_notas  = st.text_area("Notas (opcional)", height=80)
            submitted = st.form_submit_button("Guardar plantel", type="primary")

        if submitted:
            if not f_nombre.strip():
                st.error("El nombre es obligatorio.")
            elif f_nombre in db["nombre"].values:
                st.error(f"Ya existe un plantel con el nombre «{f_nombre}».")
            else:
                new_row = {
                    "nombre": f_nombre.strip(),
                    "lat":    f_lat,
                    "lon":    f_lon,
                    "tipo":   f_tipo,
                    "notas":  f_notas.strip(),
                }
                db = pd.concat([db, pd.DataFrame([new_row])], ignore_index=True)
                save_db(db)
                st.success(f"✅ Plantel «{f_nombre}» guardado.")
                st.rerun()

    return db


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    st.sidebar.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/"
        "Chicken_Gallus_gallus_domesticus_Walking_MWNH2.png/240px-"
        "Chicken_Gallus_gallus_domesticus_Walking_MWNH2.png",
        width=80,
    )
    st.sidebar.title("AviVet — Riesgo IA")
    st.sidebar.caption("Escala de riesgo de Influenza Aviar\npara planteles avícolas")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "Navegación",
        ["🗺️ Evaluación", "🏭 Gestión de planteles"],
        label_visibility="collapsed",
    )

    st.sidebar.divider()
    st.sidebar.markdown(
        """
        **Fuentes epidemiológicas**
        - Yoo et al. 2021 — distancia a humedales
        - Azat et al. 2024 — Chile H5N1
        - Jindal et al. 2026 — ML global H5N1
        - Cárdenas et al. 2026 — red de planteles
        """
    )

    db = load_db()

    if page == "🗺️ Evaluación":
        page_evaluation(db)
    else:
        page_database(db)


if __name__ == "__main__":
    main()
