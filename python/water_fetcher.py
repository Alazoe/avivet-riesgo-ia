"""
Consulta la Overpass API (OpenStreetMap) para obtener cuerpos de agua
cercanos a unas coordenadas dadas.
"""
from __future__ import annotations

import requests
from geopy.distance import geodesic

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "AviVet-IA-Risk/1.0 (veterinaria-aviar)"}

# Etiquetas OSM que se consideran "agua relevante para IA"
WATER_TAGS = [
    '["natural"="water"]',
    '["natural"="wetland"]',
    '["waterway"="river"]',
    '["waterway"="stream"]',
    '["landuse"="reservoir"]',
]


def _build_query(lat: float, lon: float, radius_m: int) -> str:
    lines = []
    for tag in WATER_TAGS:
        lines.append(f'  way{tag}(around:{radius_m},{lat},{lon});')
        lines.append(f'  relation{tag}(around:{radius_m},{lat},{lon});')
        lines.append(f'  node{tag}(around:{radius_m},{lat},{lon});')
    body = "\n".join(lines)
    return f"[out:json][timeout:25];\n(\n{body}\n);\nout center tags;"


def fetch_water_bodies(
    lat: float, lon: float, radius_m: int = 6000
) -> tuple[float, list[dict]]:
    """
    Devuelve (distancia_km_al_más_cercano, lista_de_features).

    Cada feature: {"lat", "lon", "water_type", "name", "dist_km"}
    Si no hay cuerpos de agua o la API falla, devuelve (inf, []).
    """
    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": _build_query(lat, lon, radius_m)},
            timeout=30,
            headers=HEADERS,
        )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except Exception:
        return float("inf"), []

    features: list[dict] = []
    for el in elements:
        etype = el.get("type")
        tags  = el.get("tags", {})

        if etype == "node":
            clat, clon = el["lat"], el["lon"]
        elif etype in ("way", "relation"):
            center = el.get("center")
            if not center:
                continue
            clat, clon = center["lat"], center["lon"]
        else:
            continue

        water_type = (
            tags.get("natural")
            or tags.get("waterway")
            or tags.get("landuse")
            or "water"
        )
        dist = geodesic((lat, lon), (clat, clon)).km
        features.append({
            "lat":        clat,
            "lon":        clon,
            "water_type": water_type,
            "name":       tags.get("name", ""),
            "dist_km":    round(dist, 3),
        })

    if not features:
        return float("inf"), []

    nearest_km = min(f["dist_km"] for f in features)
    # Ordenar por distancia para la tabla
    features.sort(key=lambda x: x["dist_km"])
    return nearest_km, features
