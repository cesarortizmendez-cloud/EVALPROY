"""
apps.core.graficos
====================
Gráficos generados como SVG puro en el servidor, sin dependencias externas
(sin Chart.js, sin CDN, sin JavaScript). Se usan en toda la plataforma
porque garantizan que el gráfico se vea siempre: el SVG se inserta
directamente en el HTML, igual que cualquier otro elemento de la página.

Funciones disponibles:
- svg_barras_con_linea: barras (ej. flujo del período) + línea (ej. acumulado)
- svg_multilinea: una o más líneas (ej. comparación de VAN entre proyectos)
- svg_barras: barras simples (ej. VAN por escenario)
"""
from __future__ import annotations

COLORES_SERIE = ["#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed", "#0891b2"]


def _escala(valores: list[float]) -> tuple[float, float]:
    v_min, v_max = min(valores), max(valores)
    rango = (v_max - v_min) or (abs(v_max) or 1)
    return v_min - rango * 0.12, v_max + rango * 0.12


def _grid(margen_izq, margen_sup, ancho_grafico, alto_grafico, piso, techo, prefijo="$"):
    lineas, etiquetas = [], []
    for k in range(5):
        frac = k / 4
        y = margen_sup + frac * alto_grafico
        valor = techo - frac * (techo - piso)
        lineas.append(f'<line x1="{margen_izq}" y1="{y:.1f}" x2="{margen_izq + ancho_grafico}" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1" />')
        etiquetas.append(f'<text x="{margen_izq - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="#64748b">{prefijo}{valor:,.0f}</text>')
    return "".join(lineas), "".join(etiquetas)


def svg_barras_con_linea(
    labels: list[str], valores_barra: list[float], valores_linea: list[float],
    nombre_barra: str = "Flujo del período", nombre_linea: str = "Flujo acumulado",
    color_barra: str = "#d97706", color_linea: str = "#16a34a",
    ancho: int = 700, alto: int = 320,
) -> str:
    if not labels:
        return ""
    margen_izq, margen_der, margen_sup, margen_inf = 80, 30, 25, 55
    ancho_grafico = ancho - margen_izq - margen_der
    alto_grafico = alto - margen_sup - margen_inf

    todos = valores_barra + valores_linea
    piso, techo = _escala(todos)
    n = len(labels)
    paso_x = ancho_grafico / n

    def x_centro(idx):
        return margen_izq + paso_x * idx + paso_x / 2

    def y_de(v):
        return margen_sup + (1 - (v - piso) / (techo - piso)) * alto_grafico

    y_cero = y_de(0) if piso <= 0 <= techo else margen_sup + alto_grafico

    grid_lines, grid_labels = _grid(margen_izq, margen_sup, ancho_grafico, alto_grafico, piso, techo)

    barras = []
    ancho_barra = paso_x * 0.55
    for idx, v in enumerate(valores_barra):
        x = x_centro(idx) - ancho_barra / 2
        y_v = y_de(v)
        y_top = min(y_v, y_cero)
        h = abs(y_v - y_cero)
        barras.append(f'<rect x="{x:.1f}" y="{y_top:.1f}" width="{ancho_barra:.1f}" height="{max(h,1):.1f}" fill="{color_barra}" opacity="0.75" rx="2" />')

    puntos_linea = " ".join(f"{x_centro(i):.1f},{y_de(v):.1f}" for i, v in enumerate(valores_linea))
    circulos = "".join(f'<circle cx="{x_centro(i):.1f}" cy="{y_de(v):.1f}" r="3.5" fill="{color_linea}" />' for i, v in enumerate(valores_linea))

    x_labels = "".join(
        f'<text x="{x_centro(i):.1f}" y="{margen_sup + alto_grafico + 18}" text-anchor="middle" font-size="10.5" fill="#64748b">{lbl}</text>'
        for i, lbl in enumerate(labels)
    )

    leyenda = (
        f'<rect x="{margen_izq}" y="{alto - 18}" width="12" height="10" fill="{color_barra}" opacity="0.75" />'
        f'<text x="{margen_izq + 18}" y="{alto - 10}" font-size="11" fill="#334155">{nombre_barra}</text>'
        f'<circle cx="{margen_izq + 200}" cy="{alto - 13}" r="4" fill="{color_linea}" />'
        f'<text x="{margen_izq + 212}" y="{alto - 10}" font-size="11" fill="#334155">{nombre_linea}</text>'
    )

    return f'''<svg viewBox="0 0 {ancho} {alto}" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto; font-family:'Segoe UI',sans-serif;">
  <rect width="{ancho}" height="{alto}" fill="white" />
  {grid_lines}{grid_labels}
  <line x1="{margen_izq}" y1="{y_cero:.1f}" x2="{margen_izq + ancho_grafico}" y2="{y_cero:.1f}" stroke="#94a3b8" stroke-width="1" />
  {''.join(barras)}
  <polyline points="{puntos_linea}" fill="none" stroke="{color_linea}" stroke-width="2.5" />
  {circulos}
  {x_labels}
  {leyenda}
</svg>'''


def svg_multilinea(
    labels: list, series: list[dict], ancho: int = 700, alto: int = 320,
    prefijo_y: str = "$", titulo_x: str = "",
) -> str:
    """
    series: lista de dicts {"nombre": str, "valores": list[float], "color": str, "dash": str opcional}
    """
    if not labels or not series:
        return ""
    margen_izq, margen_der, margen_sup, margen_inf = 80, 30, 25, 55
    ancho_grafico = ancho - margen_izq - margen_der
    alto_grafico = alto - margen_sup - margen_inf

    todos = [v for s in series for v in s["valores"]]
    piso, techo = _escala(todos)
    n = len(labels)

    def x_de(idx):
        if n <= 1:
            return margen_izq + ancho_grafico / 2
        return margen_izq + idx / (n - 1) * ancho_grafico

    def y_de(v):
        return margen_sup + (1 - (v - piso) / (techo - piso)) * alto_grafico

    grid_lines, grid_labels = _grid(margen_izq, margen_sup, ancho_grafico, alto_grafico, piso, techo, prefijo=prefijo_y)

    paso_etq = 1 if n <= 14 else max(1, n // 10)
    x_labels = "".join(
        f'<text x="{x_de(i):.1f}" y="{margen_sup + alto_grafico + 18}" text-anchor="middle" font-size="10.5" fill="#64748b">{lbl}</text>'
        for i, lbl in enumerate(labels) if i % paso_etq == 0
    )

    lineas_svg, leyenda_items = [], []
    for s_idx, serie in enumerate(series):
        color = serie.get("color") or COLORES_SERIE[s_idx % len(COLORES_SERIE)]
        dash = serie.get("dash", "")
        pts = " ".join(f"{x_de(i):.1f},{y_de(v):.1f}" for i, v in enumerate(serie["valores"]))
        dash_attr = f'stroke-dasharray="{dash}"' if dash else ""
        lineas_svg.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5" {dash_attr} />')
        x_leg = margen_izq + s_idx * 200
        leyenda_items.append(
            f'<rect x="{x_leg}" y="{alto - 18}" width="14" height="4" fill="{color}" />'
            f'<text x="{x_leg + 20}" y="{alto - 12}" font-size="11" fill="#334155">{serie["nombre"]}</text>'
        )

    titulo_svg = f'<text x="{margen_izq + ancho_grafico/2:.1f}" y="{alto - 32}" text-anchor="middle" font-size="11" fill="#334155">{titulo_x}</text>' if titulo_x else ""

    return f'''<svg viewBox="0 0 {ancho} {alto}" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto; font-family:'Segoe UI',sans-serif;">
  <rect width="{ancho}" height="{alto}" fill="white" />
  {grid_lines}{grid_labels}
  {''.join(lineas_svg)}
  {x_labels}
  {titulo_svg}
  {''.join(leyenda_items)}
</svg>'''


def svg_barras(labels: list[str], valores: list[float], color: str = "#7c3aed", ancho: int = 700, alto: int = 300) -> str:
    if not labels:
        return ""
    margen_izq, margen_der, margen_sup, margen_inf = 80, 30, 25, 45
    ancho_grafico = ancho - margen_izq - margen_der
    alto_grafico = alto - margen_sup - margen_inf

    piso, techo = _escala(valores)
    n = len(labels)
    paso_x = ancho_grafico / n

    def y_de(v):
        return margen_sup + (1 - (v - piso) / (techo - piso)) * alto_grafico

    y_cero = y_de(0) if piso <= 0 <= techo else margen_sup + alto_grafico
    grid_lines, grid_labels = _grid(margen_izq, margen_sup, ancho_grafico, alto_grafico, piso, techo)

    barras, x_labels = [], []
    ancho_barra = paso_x * 0.55
    for idx, (lbl, v) in enumerate(zip(labels, valores)):
        x_centro = margen_izq + paso_x * idx + paso_x / 2
        x = x_centro - ancho_barra / 2
        y_v = y_de(v)
        y_top = min(y_v, y_cero)
        h = abs(y_v - y_cero)
        barras.append(f'<rect x="{x:.1f}" y="{y_top:.1f}" width="{ancho_barra:.1f}" height="{max(h,1):.1f}" fill="{color}" opacity="0.8" rx="3" />')
        x_labels.append(f'<text x="{x_centro:.1f}" y="{margen_sup + alto_grafico + 18}" text-anchor="middle" font-size="10.5" fill="#64748b">{lbl}</text>')

    return f'''<svg viewBox="0 0 {ancho} {alto}" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto; font-family:'Segoe UI',sans-serif;">
  <rect width="{ancho}" height="{alto}" fill="white" />
  {grid_lines}{grid_labels}
  <line x1="{margen_izq}" y1="{y_cero:.1f}" x2="{margen_izq + ancho_grafico}" y2="{y_cero:.1f}" stroke="#94a3b8" stroke-width="1" />
  {''.join(barras)}
  {''.join(x_labels)}
</svg>'''
