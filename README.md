# AviVet — Escala de Riesgo de Influenza Aviar 🦠

Herramienta geoespacial para evaluar el riesgo de Influenza Aviar (H5N1) en planteles avícolas, desarrollada por **AviVet** para médicos veterinarios y asesores avícolas.

---

## ¿Qué hace?

Calcula un puntaje de riesgo (0–12 puntos) combinando cuatro factores epidemiológicos validados en la literatura:

| Factor | Puntaje máx. | Fundamento |
|--------|:---:|---|
| Distancia a cuerpos de agua | 3 | Yoo et al. 2021 — humedales como 33.78% del riesgo |
| Planteles industriales en radio 5 km | 3 | Gkrinia et al. 2025 — OR 6.0 mismo tipo de granja |
| Temporada del año (austral) | 3 | Jindal et al. 2026 — verano austral = pico global |
| Tipo de producción | 3 | Yoo et al. 2021 — aves acuáticas/exterior, mayor contacto con silvestres |

**Niveles de riesgo:**

| Puntaje | Nivel | Recomendación |
|:---:|---|---|
| 0–3 | 🟢 BAJO | Vigilancia rutinaria |
| 4–6 | 🟡 MEDIO | Reforzar bioseguridad, registro quincenal |
| 7–9 | 🟠 ALTO | Plan de contingencia activo, SAG notificado |
| 10–12 | 🔴 MUY ALTO | Alerta máxima, evaluación presencial urgente |

---

## Versiones

### 🌐 HTML (recomendada para el sitio web)

Archivo: `index.html`

- Sin servidor, funciona directamente en el navegador
- Mapa interactivo con Leaflet.js
- Cuerpos de agua desde OpenStreetMap (Overpass API)
- Base de datos de planteles en `localStorage`
- Compatible con cualquier hosting estático

**Uso:** Abrir `index.html` en el navegador o subir al servidor junto al resto del sitio AviVet.

---

### 🐍 Python / Streamlit

Archivos: `python/`

```bash
cd python
pip install -r requirements.txt
python3 -m streamlit run app.py
```

Disponible en `http://localhost:8501`

**Archivos:**
- `app.py` — interfaz Streamlit con mapa Folium
- `risk_calculator.py` — lógica de cálculo pura
- `water_fetcher.py` — consulta Overpass API
- `data/planteles.csv` — base de datos de planteles (CSV)

---

## Fuentes epidemiológicas

1. **Yoo et al. 2021** — Distancia a humedales como factor de riesgo (33.78% del puntaje predictivo)
2. **Azat et al. 2024** — Análisis espacio-temporal H5N1 en Chile
3. **Jindal et al. 2026** — Modelo ML global H5N1; verano austral como período de mayor riesgo
4. **Cárdenas et al. 2026** — Red de planteles; retraso de 3 días → 4 planteles afectados, 10 días → 34
5. **Gkrinia et al. 2025** — Revisión sistemática de factores OR de bioseguridad; OR 6.0 mismo tipo de granja

---

## Parte de

Este repositorio es parte del ecosistema **[AviVet](https://avivet.cl)** — herramientas de medicina veterinaria aviar para Chile.

---

*Desarrollado con ❤️ para la medicina aviar — AviVet 2026*
