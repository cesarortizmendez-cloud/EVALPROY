"""
Generación de gráficos como SVG puro, renderizados en el servidor.

Se usa en vez de Chart.js (vía CDN) para el gráfico crítico de la curva
de CAE, porque depender de una librería externa cargada por JavaScript
introduce un punto de falla (red lenta, bloqueos corporativos, adblockers)
que deja el gráfico en blanco sin aviso. Un SVG generado en el servidor
se ve siempre, sin JavaScript y sin red externa.
"""
from __future__ import annotations


def construir_svg_curva_cae(puntos: list[tuple[int, float]], n_optimo: int, ancho: int = 700, alto: int = 320) -> str:
    """
    puntos: lista de tuplas (n, cae) en el orden del eje x.
    n_optimo: el valor de n cuyo punto se resalta como mínimo.
    Devuelve un string SVG completo y listo para insertar con |safe en el template.
    """
    if not puntos:
        return ""

    margen_izq, margen_der, margen_sup, margen_inf = 70, 30, 30, 50
    ancho_grafico = ancho - margen_izq - margen_der
    alto_grafico = alto - margen_sup - margen_inf

    valores_n = [p[0] for p in puntos]
    valores_cae = [p[1] for p in puntos]
    n_min, n_max = min(valores_n), max(valores_n)
    cae_min, cae_max = min(valores_cae), max(valores_cae)
    # Margen visual para que la curva no toque los bordes
    rango_cae = (cae_max - cae_min) or 1
    cae_piso = cae_min - rango_cae * 0.12
    cae_techo = cae_max + rango_cae * 0.12

    def x_de(n):
        if n_max == n_min:
            return margen_izq + ancho_grafico / 2
        return margen_izq + (n - n_min) / (n_max - n_min) * ancho_grafico

    def y_de(cae):
        return margen_sup + (1 - (cae - cae_piso) / (cae_techo - cae_piso)) * alto_grafico

    coords = [(x_de(n), y_de(c)) for n, c in puntos]
    polyline_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)

    area_pts = f"{coords[0][0]:.1f},{margen_sup + alto_grafico:.1f} " + polyline_pts + f" {coords[-1][0]:.1f},{margen_sup + alto_grafico:.1f}"

    # Líneas de grilla horizontales (5 niveles)
    grid_lines = []
    grid_labels = []
    for k in range(5):
        frac = k / 4
        y = margen_sup + frac * alto_grafico
        valor = cae_techo - frac * (cae_techo - cae_piso)
        grid_lines.append(f'<line x1="{margen_izq}" y1="{y:.1f}" x2="{margen_izq + ancho_grafico}" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1" />')
        grid_labels.append(f'<text x="{margen_izq - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="#64748b">${valor:,.0f}</text>')

    # Etiquetas eje X (cada punto, o cada 2 si hay muchos)
    paso_etiqueta = 1 if len(puntos) <= 14 else 2
    x_labels = []
    for idx, (n, c) in enumerate(puntos):
        if idx % paso_etiqueta == 0 or n == n_optimo:
            x_labels.append(f'<text x="{x_de(n):.1f}" y="{margen_sup + alto_grafico + 20}" text-anchor="middle" font-size="11" fill="#64748b">{n}</text>')

    # Puntos: normales en rojo, el óptimo en dorado y más grande
    puntos_svg = []
    for n, c in puntos:
        x, y = x_de(n), y_de(c)
        if n == n_optimo:
            puntos_svg.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#f59e0b" stroke="#fff" stroke-width="2" />'
                f'<text x="{x:.1f}" y="{y - 14:.1f}" text-anchor="middle" font-size="12" font-weight="700" fill="#b45309">n={n}</text>'
            )
        else:
            puntos_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#b91c1c" />')

    svg = f'''<svg viewBox="0 0 {ancho} {alto}" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto; font-family: 'Segoe UI', sans-serif;">
  <rect x="0" y="0" width="{ancho}" height="{alto}" fill="white" />
  {''.join(grid_lines)}
  {''.join(grid_labels)}
  <polygon points="{area_pts}" fill="rgba(185,28,28,0.10)" stroke="none" />
  <polyline points="{polyline_pts}" fill="none" stroke="#b91c1c" stroke-width="2.5" />
  {''.join(puntos_svg)}
  {''.join(x_labels)}
  <text x="{margen_izq + ancho_grafico / 2:.1f}" y="{alto - 8}" text-anchor="middle" font-size="12" fill="#334155">Años de uso del equipo</text>
  <text x="16" y="{margen_sup + alto_grafico / 2:.1f}" text-anchor="middle" font-size="12" fill="#334155" transform="rotate(-90 16 {margen_sup + alto_grafico / 2:.1f})">CAE ($)</text>
</svg>'''
    return svg


def construir_svg_dos_series(
    anios: list[int],
    serie_actual: list[float],
    serie_desafiante: list[float],
    nombre_actual: str,
    nombre_desafiante: str,
    n_cruce: float | None = None,
    ancho: int = 700,
    alto: int = 320,
) -> str:
    """
    Dibuja dos series (CAE de la alternativa actual creciendo vs. CAE
    constante del desafiante) y marca el punto de cruce n*, si existe
    dentro del rango graficado. Usado en el módulo de Momento Óptimo de
    Reemplazo, con el mismo enfoque de SVG generado en servidor (sin
    depender de Chart.js / CDN externo).
    """
    if not anios:
        return ""

    margen_izq, margen_der, margen_sup, margen_inf = 70, 30, 30, 60
    ancho_grafico = ancho - margen_izq - margen_der
    alto_grafico = alto - margen_sup - margen_inf

    todos_valores = serie_actual + serie_desafiante
    v_min, v_max = min(todos_valores), max(todos_valores)
    rango_v = (v_max - v_min) or 1
    piso, techo = v_min - rango_v * 0.1, v_max + rango_v * 0.1

    n_min, n_max = min(anios), max(anios)

    def x_de(n):
        if n_max == n_min:
            return margen_izq + ancho_grafico / 2
        return margen_izq + (n - n_min) / (n_max - n_min) * ancho_grafico

    def y_de(v):
        return margen_sup + (1 - (v - piso) / (techo - piso)) * alto_grafico

    def polyline(serie, color, dash=""):
        pts = " ".join(f"{x_de(a):.1f},{y_de(v):.1f}" for a, v in zip(anios, serie))
        dash_attr = f'stroke-dasharray="{dash}"' if dash else ""
        return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5" {dash_attr} />'

    grid_lines, grid_labels = [], []
    for k in range(5):
        frac = k / 4
        y = margen_sup + frac * alto_grafico
        valor = techo - frac * (techo - piso)
        grid_lines.append(f'<line x1="{margen_izq}" y1="{y:.1f}" x2="{margen_izq + ancho_grafico}" y2="{y:.1f}" stroke="#e5e7eb" stroke-width="1" />')
        grid_labels.append(f'<text x="{margen_izq - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="#64748b">${valor:,.0f}</text>')

    x_labels = [f'<text x="{x_de(a):.1f}" y="{margen_sup + alto_grafico + 20}" text-anchor="middle" font-size="11" fill="#64748b">{a}</text>' for a in anios]

    marca_cruce = ""
    if n_cruce is not None and n_min <= n_cruce <= n_max:
        x_c = x_de(n_cruce)
        marca_cruce = (
            f'<line x1="{x_c:.1f}" y1="{margen_sup}" x2="{x_c:.1f}" y2="{margen_sup + alto_grafico}" '
            f'stroke="#f59e0b" stroke-width="2" stroke-dasharray="5,4" />'
            f'<text x="{x_c:.1f}" y="{margen_sup - 8}" text-anchor="middle" font-size="11" font-weight="700" fill="#b45309">n*={n_cruce:.2f}</text>'
        )

    leyenda = (
        f'<rect x="{margen_izq}" y="{alto - 22}" width="12" height="4" fill="#0891b2" />'
        f'<text x="{margen_izq + 18}" y="{alto - 16}" font-size="11" fill="#334155">{nombre_actual}</text>'
        f'<rect x="{margen_izq + 220}" y="{alto - 22}" width="12" height="4" fill="#b91c1c" />'
        f'<text x="{margen_izq + 238}" y="{alto - 16}" font-size="11" fill="#334155">{nombre_desafiante}</text>'
    )

    svg = f'''<svg viewBox="0 0 {ancho} {alto}" xmlns="http://www.w3.org/2000/svg" style="width:100%; height:auto; font-family: 'Segoe UI', sans-serif;">
  <rect x="0" y="0" width="{ancho}" height="{alto}" fill="white" />
  {''.join(grid_lines)}
  {''.join(grid_labels)}
  {marca_cruce}
  {polyline(serie_actual, "#0891b2")}
  {polyline(serie_desafiante, "#b91c1c", dash="6,4")}
  {''.join(x_labels)}
  {leyenda}
  <text x="{margen_izq + ancho_grafico / 2:.1f}" y="{alto - 30}" text-anchor="middle" font-size="12" fill="#334155">Años desde hoy</text>
</svg>'''
    return svg
