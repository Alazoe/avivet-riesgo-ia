"""
Lógica de cálculo de riesgo para influenza aviar.
Escala 0–12 puntos → cuatro tiers (BAJO / MEDIO / ALTO / MUY ALTO).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class FarmType(str, Enum):
    WATERFOWL  = "Aves acuáticas / mixto con patos"
    FREE_RANGE = "Ponedoras/broilers en acceso exterior"
    CONFINED   = "Ponedoras/broilers confinadas"
    BACKYARD   = "Traspatio <50 aves"


# Configuración de tiers: rango, color hex, color folium, emoji, recomendación
TIERS = {
    "BAJO":     {"range": (0, 3),  "color": "#2ECC71", "folium": "green",   "emoji": "🟢",
                 "rec": "Vigilancia rutinaria. Mantener registro de mortalidad y bioseguridad básica."},
    "MEDIO":    {"range": (4, 6),  "color": "#F1C40F", "folium": "orange",  "emoji": "🟡",
                 "rec": "Reforzar bioseguridad. Registro quincenal de mortalidad y signología; controlar acceso de personas y vehículos."},
    "ALTO":     {"range": (7, 9),  "color": "#E67E22", "folium": "red",     "emoji": "🟠",
                 "rec": "Plan de contingencia activo. Notificar al SAG ante cualquier mortalidad anómala; restringir contacto con aves silvestres y cuerpos de agua."},
    "MUY ALTO": {"range": (10, 12),"color": "#E74C3C", "folium": "darkred", "emoji": "🔴",
                 "rec": "Alerta máxima. Evaluación presencial urgente, refuerzo inmediato de bioseguridad y coordinación con SAG."},
}


@dataclass
class RiskScore:
    water_distance_km: float
    water_points:      int
    nearby_farms:      int
    farms_points:      int
    season_points:     int
    type_points:       int
    total:             int
    tier:              str
    tier_color:        str
    tier_folium_color: str
    tier_emoji:        str
    tier_rec:          str
    eval_date:         date

    @property
    def breakdown(self) -> list[tuple[str, int, int]]:
        """(factor, puntos_obtenidos, puntos_máximos)"""
        return [
            ("💧 Distancia a agua",         self.water_points,  3),
            ("🏭 Planteles cercanos",        self.farms_points,  3),
            ("📅 Estación del año",          self.season_points, 3),
            ("🐔 Tipo de producción propia", self.type_points,   3),
        ]


# ── Funciones de puntuación individuales ──────────────────────────────────────

def _water_pts(km: float) -> int:
    if km < 0.5:  return 3
    if km < 2.0:  return 2
    if km < 5.0:  return 1
    return 0


def _farms_pts(count: int) -> int:
    if count >= 2: return 3
    if count == 1: return 2
    return 0


def _season_pts(d: date) -> int:
    # Verano austral nov–mar = peak IA en Chile (Jindal 2026, Azat 2024)
    if d.month in (11, 12, 1, 2, 3): return 3
    if d.month in (4, 5, 6):         return 2
    return 1


def _type_pts(ft: FarmType) -> int:
    return {
        FarmType.WATERFOWL:  3,
        FarmType.FREE_RANGE: 2,
        FarmType.CONFINED:   1,
        FarmType.BACKYARD:   0,
    }[ft]


def _tier_for(total: int) -> tuple[str, str, str, str, str]:
    for name, cfg in TIERS.items():
        lo, hi = cfg["range"]
        if lo <= total <= hi:
            return name, cfg["color"], cfg["folium"], cfg["emoji"], cfg["rec"]
    muy = TIERS["MUY ALTO"]
    return "MUY ALTO", muy["color"], muy["folium"], muy["emoji"], muy["rec"]


# ── API pública ────────────────────────────────────────────────────────────────

def calculate_risk(
    water_distance_km: float,
    nearby_farms: int,
    farm_type: FarmType,
    eval_date: Optional[date] = None,
) -> RiskScore:
    d = eval_date or date.today()
    w = _water_pts(water_distance_km)
    f = _farms_pts(nearby_farms)
    s = _season_pts(d)
    t = _type_pts(farm_type)
    total = w + f + s + t
    tier, color, folium_col, emoji, rec = _tier_for(total)

    return RiskScore(
        water_distance_km=water_distance_km,
        water_points=w,
        nearby_farms=nearby_farms,
        farms_points=f,
        season_points=s,
        type_points=t,
        total=total,
        tier=tier,
        tier_color=color,
        tier_folium_color=folium_col,
        tier_emoji=emoji,
        tier_rec=rec,
        eval_date=d,
    )
