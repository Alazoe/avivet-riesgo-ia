# AviVet — Escala de Riesgo de Influenza Aviar 🦠

Herramienta geoespacial para evaluar el riesgo de Influenza Aviar (H5N1) en planteles avícolas, desarrollada por **AviVet** para médicos veterinarios y asesores avícolas.

---

## ¿Qué hace?

Calcula un puntaje de riesgo (0–15 puntos) combinando cinco factores epidemiológicos validados en la literatura:

| Factor | Puntaje máx. | Fundamento |
|--------|:---:|---|
| Distancia a cuerpos de agua | 3 | Yoo et al. 2021 — humedales como 33.78% del riesgo |
| Planteles industriales en radio 5 km | 3 | Gkrinia et al. 2025 — OR 6.0 mismo tipo de granja |
| Temporada del año (austral) | 3 | Jindal et al. 2026 — verano austral = pico global |
| Tipo de producción | 3 | Yoo et al. 2021 — aves acuáticas/exterior, mayor contacto con silvestres |
| Brotes IA cercanos (filtrable por año/tipo) | 3 | 158 brotes WAHIS/OMSA 2022–2026; Cárdenas 2026 — OR 6.0 por proximidad |

**Niveles de riesgo:**

| Puntaje | Nivel | Recomendación |
|:---:|---|---|
| 0–4 | 🟢 BAJO | Vigilancia rutinaria |
| 5–8 | 🟡 MEDIO | Reforzar bioseguridad, registro quincenal |
| 9–11 | 🟠 ALTO | Plan de contingencia activo, SAG notificado |
| 12–15 | 🔴 MUY ALTO | Alerta máxima, evaluación presencial urgente |

---

## Versiones

### 🌐 HTML (recomendada para el sitio web)

Archivo: `index.html`

- Sin servidor, funciona directamente en el navegador
- Mapa interactivo con Leaflet.js
- **Cuerpos de agua automáticos** desde dos fuentes en vivo:
  - **OpenStreetMap** (Overpass API)
  - **Red Hidrográfica oficial de la DGA / MOP** (ArcGIS REST, ríos 1:250.000 + sistema lacustre) — se consulta en tiempo real y se dibuja como líneas/polígonos; alimenta el cálculo de distancia al agua
- **Capa satelital** (Esri World Imagery) para identificar visualmente esteros, tranques y humedales que ninguna fuente mapea
- **Marcado manual de agua**: clic en el mapa para agregar cuerpos de agua que entran al cálculo de distancia (recálculo en vivo)
- **Marcado de planteles/sectores industriales**: identifícalos a ojo en el satélite y márcalos con un clic; se **guardan** (localStorage), se dibujan siempre y **cuentan automáticamente** en el factor "planteles cercanos"
- **Capa de brotes HPAI H5N1 Chile 2026** (SAG / WAHIS) precargada: planteles comerciales y humedales con aves silvestres positivas
- **Registro de brotes propios** (comercial / traspatio / silvestre) guardados en `localStorage` y superpuestos a los oficiales
- Base de datos de planteles en `localStorage`
- Compatible con cualquier hosting estático

**Uso:** Abrir `index.html` en el navegador o subir al servidor junto al resto del sitio AviVet.

**En vivo:** [avivet.cl/avivet/riesgo-ia/](https://avivet.cl/avivet/riesgo-ia/)

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

## Actualizar los brotes oficiales del mapa

Los brotes precargados están en el arreglo `WAHIS_BROTES` dentro de `index.html`
(fuente SAG / WAHIS). Para agregar o corregir uno, editar esa lista:

```js
{ lat:-41.4693, lon:-72.9424, tipo:'comercial', fecha:'20 may 2026',
  region:'Los Lagos', detalle:'Plantel de postura, ~40.000 aves, comuna X' },
```

`tipo` puede ser `comercial`, `traspatio` o `silvestre`. No existe API pública de
WAHIS (está tras Cloudflare y requiere token), por lo que la carga es manual.
El usuario también puede registrar brotes desde la app (pestaña **Brotes IA**),
que se guardan solo en su navegador (`localStorage`).

---

## Parte de

Este repositorio es parte del ecosistema **[AviVet](https://avivet.cl)** — herramientas de medicina veterinaria aviar para Chile.

---

*Desarrollado con ❤️ para la medicina aviar — AviVet 2026*
