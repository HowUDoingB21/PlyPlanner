# geometria.py — Áreas, arcos y algoritmo de corte óptimo
import math


# ─────────────────────────────────────────────────────────────────
# GEOMETRÍA DE SUPERFICIES
# ─────────────────────────────────────────────────────────────────

def cylinder_info(diameter, length):
    """
    Retorna:
        area      — área lateral (m²)
        perimeter — perímetro de la sección circular (m)
        length    — longitud del cilindro (m)
    """
    P = math.pi * diameter
    return {
        "area":      P * length,
        "perimeter": P,
        "length":    length,
    }


def cone_info(base_diam, height, cone_type):
    """
    Calcula área superficial y longitud del arco de perfil para 3 tipos de ogiva.

    Cónico         : área exacta π·r·s,  arco = slant height s.
    Ojiva tangente : fórmula cerrada exacta válida cuando height >= r.
    Parabólico     : y(x) = r·√(x/L). Área fórmula cerrada; arco numérico.

    Retorna:
        area    — m²
        arc     — longitud del perfil desde base hasta punta (m)
        perimeter — 2πr (m)
        warning   — cadena de advertencia si aplica
    """
    r = base_diam / 2.0
    P = math.pi * base_diam
    warning = ""

    if r <= 0 or height <= 0:
        return {"area": 0.0, "arc": 0.0, "perimeter": P, "warning": "Dimensiones inválidas"}

    if cone_type == "Cónico":
        s    = math.sqrt(r**2 + height**2)
        area = math.pi * r * s
        arc  = s

    elif cone_type == "Ojiva (tangente)":
        if height < r:
            warning = "⚠ Ojiva inválida (h < r). Usando fórmula cónica como respaldo."
            s    = math.sqrt(r**2 + height**2)
            area = math.pi * r * s
            arc  = s
        else:
            rho  = (r**2 + height**2) / (2.0 * r)
            k    = min(height / rho, 1.0)
            # Área = 2π(ρ²·arcsin(h/ρ) − ρ·h)
            area = 2.0 * math.pi * (rho**2 * math.asin(k) - rho * height)
            # Arco = ρ·arcsin(h/ρ)
            arc  = rho * math.asin(k)

    else:  # Parabólico: y(x) = r·√(x/L)
        # Área analítica: (πr / 6L²)·[(4L²+r²)^(3/2) − r³]
        val  = 4.0 * height**2 + r**2
        area = (math.pi * r / (6.0 * height**2)) * (val**1.5 - r**3)
        # Arco numérico (trapezoidal, 800 pasos)
        N = 800; dx = height / N; arc = 0.0
        for i in range(N):
            x0 = i * dx
            x1 = x0 + dx
            y0 = r * math.sqrt(x0 / height) if x0 > 0 else 0.0
            y1 = r * math.sqrt(x1 / height)
            arc += math.sqrt(dx**2 + (y1 - y0)**2)

    return {
        "area":      max(area, 0.0),
        "arc":       arc,
        "perimeter": P,
        "warning":   warning,
    }


def fin_info(root, tip, span, count, sweep_type="length", sweep_value=0.0, thickness=0.0):
    """
    Aleta trapezoidal con flechado y espesor de material.

    Coordenadas del trapecio (borde de ataque de raíz en origen):
        A (0, 0)                  — borde ataque raíz
        B (root, 0)               — borde fuga raíz
        C (sweep_length+tip, span)— borde fuga punta
        D (sweep_length, span)    — borde ataque punta

    sweep_type  : "length" (m) | "angle" (°)
    thickness   : offset de contorno para incluir espesor de la aleta (m)

    Caja contenedora con espesor:
        bnd_w = span + 2*thickness          (dimensión envergadura)
        bnd_h = max(root, sweep+tip) + 2*thickness  (dimensión cuerda máx)

    Área geométrica (trapecio, sin espesor):
        A = (root + tip) / 2 * span
    """
    if sweep_type == "angle":
        ang_rad = math.radians(abs(sweep_value))
        sweep_length = span * math.tan(ang_rad)
    else:
        sweep_length = abs(sweep_value)

    single  = (root + tip) / 2.0 * span
    chord_h = max(root, sweep_length + tip)      # cuerda máxima proyectada
    bnd_w   = span      + 2.0 * thickness        # envergadura + espesor
    bnd_h   = chord_h   + 2.0 * thickness        # cuerda      + espesor

    return {
        "single_area":   single,
        "total_area":    single * count,
        "bnd_w":         bnd_w,
        "bnd_h":         bnd_h,
        "chord_h":       chord_h,
        "count":         count,
        "sweep_length":  sweep_length,
        "thickness":     thickness,
        # Esquinas del trapecio en coords locales (origen=esquina sup-izq de la caja)
        # Eje X = cuerda, Eje Y = envergadura
        "corners": [
            (thickness,               thickness),               # A borde ataque raíz
            (thickness + root,        thickness),               # B borde fuga raíz
            (thickness + sweep_length + tip, thickness + span), # C borde fuga punta
            (thickness + sweep_length,       thickness + span), # D borde ataque punta
        ],
    }


# ─────────────────────────────────────────────────────────────────
# ALGORITMO DE CORTE ÓPTIMO
# ─────────────────────────────────────────────────────────────────

def _try_orient(fixed_w, piece_cross, piece_along, n_pieces):
    """
    Intenta colocar piezas de (piece_cross × piece_along) en un rollo
    de ancho fixed_w.

    - piece_cross  : dimensión perpendicular al sentido de avance del rollo
    - piece_along  : dimensión paralela al avance (determina cuánto 'n' se consume)
    - n_pieces     : número total de piezas requeridas

    Retorna dict o None si piece_cross > fixed_w.
    """
    if fixed_w < piece_cross - 1e-9:
        return None
    strips_per_pass = math.floor(fixed_w / piece_cross)   # piezas por fila transversal
    passes          = math.ceil(n_pieces / strips_per_pass)
    n_needed        = math.ceil(passes * piece_along)      # n entero (metros)
    return {
        "n":             n_needed,
        "strips":        strips_per_pass,
        "passes":        passes,
        "piece_cross":   piece_cross,
        "piece_along":   piece_along,
    }


def best_cut(fixed_w, pw, ph, n_pieces):
    """
    Rollo: fixed_w (fijo, m) × n metros (entero a determinar).
    Pieza: pw × ph metros.   n_pieces: cantidad total de piezas.

    Prueba ambas orientaciones y devuelve la que requiere menor n.
    Retorna dict{n, strips, passes, orient, piece_cross, piece_along}
    o None si el rollo no puede contener la pieza en ninguna orientación.
    """
    if n_pieces <= 0 or pw <= 0 or ph <= 0 or fixed_w <= 0:
        return None

    opts = []

    # Orientación A: pw cruzado, ph a lo largo
    r = _try_orient(fixed_w, pw, ph, n_pieces)
    if r:
        r["orient"] = "A"
        opts.append(r)

    # Orientación B: ph cruzado, pw a lo largo  (solo si no son iguales)
    if abs(ph - pw) > 1e-9:
        r = _try_orient(fixed_w, ph, pw, n_pieces)
        if r:
            r["orient"] = "B"
            opts.append(r)

    return min(opts, key=lambda x: x["n"]) if opts else None


# ─────────────────────────────────────────────────────────────────
# CORTE POR TIPO DE COMPONENTE
# ─────────────────────────────────────────────────────────────────

def cut_cylinder(fixed_w, overlap, perimeter, length, layers):
    """
    Una pieza por capa: (perimeter + overlap) × (length + overlap).
    """
    return best_cut(
        fixed_w,
        perimeter + overlap,
        length    + overlap,
        layers,
    )


def cut_cone(fixed_w, overlap, arc, perimeter, layers, gores):
    """
    Cada capa se divide en `gores` gajos.
    Gajo: (perimeter/gores + overlap) × (arc + overlap).
    Total piezas = layers × gores.
    """
    return best_cut(
        fixed_w,
        perimeter / gores + overlap,
        arc               + overlap,
        layers * gores,
    )


def cut_fin(fixed_w, overlap, span, root, count, layers):
    """
    Caja contenedora de cada aleta: (span + overlap) × (root + overlap).
    Total piezas = count × layers.
    """
    return best_cut(
        fixed_w,
        span + overlap,
        root + overlap,
        count * layers,
    )


# ─────────────────────────────────────────────────────────────────
# PIEZAS NECESARIAS POR COMPONENTE
# ─────────────────────────────────────────────────────────────────

def get_pieces(comp, fiber_role, overlap, gores):
    """
    Devuelve (piece_cross, piece_along, quantity, pieces_per_box) donde:
      - piece_cross × piece_along : caja de corte
      - quantity                  : número de cajas a comprar
      - pieces_per_box            : piezas reales que salen de cada caja

    EMPAREJAMIENTO (nesting):
      Aletas (trapecio): dos aletas invertidas cazan sus triángulos sobrantes
                         → 2 aletas por caja, qty = ceil(total/2)
      Gajos de cono:     dos gajos punta-con-punta usan la misma caja
                         → 2 gajos por caja, qty = ceil(total/2)
      Cilindros:         pieza rectangular exacta, sin mejora posible.
    """
    layers = comp["layers_bulk"] if fiber_role == "bulk" else comp["layers_aesthetic"]
    if layers == 0:
        return None

    p  = comp["params"]
    ct = comp["comp_type"]
    ov = overlap

    if ct == "Cilindro":
        gi  = cylinder_info(p["diameter"], p["length"])
        pw  = gi["perimeter"] + ov
        ph  = gi["length"]    + ov
        qty = layers
        ppb = 1   # pieces per box — cilindro ocupa toda la caja

    elif ct == "Cono / Ogiva":
        ci  = cone_info(p["base_diam"], p["height"], p["cone_type"])
        pw  = ci["perimeter"] / gores + ov
        ph  = ci["arc"]               + ov
        total = layers * gores
        # 2 gajos por caja (punta con punta)
        qty = math.ceil(total / 2)
        ppb = 2

    else:  # Aleta
        fi  = fin_info(p["root"], p["tip"], p["span"], p["count"],
                       p.get("sweep_type", "length"), p.get("sweep_value", 0.0),
                       p.get("thickness", 0.0))
        pw  = fi["bnd_w"] + ov
        ph  = fi["bnd_h"] + ov
        total = fi["count"] * layers
        qty = total
        ppb = 1   # 1 aleta por caja — trapecio general no anida sin solapamiento

    if pw <= ph:
        cross, along = pw, ph
    else:
        cross, along = ph, pw

    # shape_info: datos para dibujar la forma real en el canvas
    shape_info = None
    if ct == "Aleta":
        fi2 = fin_info(p["root"], p["tip"], p["span"], p["count"],
                       p.get("sweep_type","length"), p.get("sweep_value",0.0),
                       p.get("thickness",0.0))
        shape_info = {
            "type":    "fin",
            "corners": fi2["corners"],   # en coords locales de la caja (X=cuerda, Y=span)
            "bnd_w":   fi2["bnd_w"],     # span+2th
            "bnd_h":   fi2["bnd_h"],     # chord+2th
            "swapped": (pw > ph),        # True si se giró la caja
        }

    return cross, along, qty, ppb, shape_info



# ─────────────────────────────────────────────────────────────────
# SKYLINE PACKING  (mínimo avance en X, sin huecos)
# ─────────────────────────────────────────────────────────────────

def _skyline_run(fixed_w, items):
    """
    Skyline packing para una tira horizontal.

    Skyline = lista de segmentos (y1, y2, x) que cubre [0, fixed_w] en Y.
    Cada segmento indica que el borde derecho a esa altura es x.
    Inicialmente todo está en x=0.

    Para cada pieza, prueba todos los Y válidos (en los bordes de los
    segmentos del skyline) y elige el que produce el mínimo right_edge
    (= x_skyline_max + piece_along). Esto compacta el layout de izquierda
    a derecha sin dejar huecos en Y.
    """
    # Skyline inicial: todo a x=0
    sky = [(0.0, fixed_w, 0.0)]   # (y1, y2, x_level)
    placements = []

    def sky_x_max(y1, y2):
        """Máximo x_level que cubre el rango [y1, y2]."""
        return max(x for s_y1, s_y2, x in sky
                   if s_y1 < y2 - 1e-9 and s_y2 > y1 + 1e-9)

    def sky_update(py, ph, new_x):
        """Actualiza el skyline: pone new_x en [py, py+ph]."""
        new_sky = []
        for s_y1, s_y2, x in sky:
            ov1 = max(s_y1, py)
            ov2 = min(s_y2, py + ph)
            if ov2 > ov1 + 1e-9:
                if s_y1 < ov1 - 1e-9: new_sky.append((s_y1, ov1, x))
                new_sky.append((ov1, ov2, new_x))
                if s_y2 > ov2 + 1e-9: new_sky.append((ov2, s_y2, x))
            else:
                new_sky.append((s_y1, s_y2, x))
        return new_sky

    for item in items:
        pc, pa, comp, ppb = item[0], item[1], item[2], item[3]

        best_pos   = None
        best_score = (float('inf'), float('inf'))

        for pw, ph in ((pa, pc), (pc, pa)):
            if ph > fixed_w + 1e-9:
                continue

            # Y candidatos: todos los bordes de segmentos del skyline
            y_cands = set()
            for s_y1, s_y2, _ in sky:
                y_cands.add(s_y1)
                end = s_y2 - ph
                if end >= -1e-9:
                    y_cands.add(max(0.0, end))

            for y_start in sorted(y_cands):
                if y_start < -1e-9 or y_start + ph > fixed_w + 1e-9:
                    continue
                x_base = sky_x_max(y_start, y_start + ph)
                # Score: (right_edge, y_start) → mínimo right, luego arriba
                score = (round(x_base + pw, 9), round(y_start, 9))
                if score < best_score:
                    best_score = score
                    best_pos = (x_base, y_start, pw, ph)

        if best_pos is None:
            continue

        px, py, pw, ph = best_pos
        placements.append({
            "x": px, "y": py, "w": pw, "h": ph,
            "pc": item[0], "pa": item[1],
            "comp": item[2], "ppb": item[3],
        })
        sky = sky_update(py, ph, px + pw)

    if not placements:
        return 0, []
    n = math.ceil(max(p["x"] + p["w"] for p in placements))
    return n, placements


def maxrects_pack(fixed_w, pieces_with_names):
    """
    Skyline packing con 4 estrategias de ordenación. Elige la de menor n.
    """
    base = []
    for pc, pa, qty, comp, ppb in pieces_with_names:
        for _ in range(int(qty)):
            base.append([float(pc), float(pa), comp, int(ppb)])

    if not base:
        return 0, []

    for it in base:
        if it[0] > fixed_w + 1e-9 and it[1] > fixed_w + 1e-9:
            return None, []

    strategies = [
        sorted(base, key=lambda x: x[0]*x[1],         reverse=True),   # área desc
        sorted(base, key=lambda x: max(x[0], x[1]),    reverse=True),   # lado largo desc
        sorted(base, key=lambda x: min(x[0], x[1]),    reverse=True),   # lado corto desc
        sorted(base, key=lambda x: min(x[0], x[1]),    reverse=False),  # lado corto asc
    ]

    best_n, best_pl = None, None
    for order in strategies:
        result = _skyline_run(fixed_w, [list(it) for it in order])
        if result is None:
            continue
        n, pl = result
        if pl and (best_n is None or n < best_n):
            best_n, best_pl = n, pl

    return (best_n, best_pl) if best_n is not None else (None, [])


# ─────────────────────────────────────────────────────────────────
# CÁLCULO GLOBAL (todos los componentes juntos, por proveedor)
# ─────────────────────────────────────────────────────────────────

def calc_all(components, providers_by_id, settings):
    """
    Calcula materiales para todos los componentes con optimización global:
    los componentes que usan el mismo proveedor comparten el rollo.

    Retorna dict:
    {
      "components": [
        { name, comp_type, geo_area,
          layers_bulk, layers_aest,
          pieces_bulk: (cross, along, qty, ppb) | None,
          pieces_aest: (cross, along, qty, ppb) | None,
          mass_used_bulk, mass_used_aest,
          mass_used_total, resin, warnings }
      ],
      "by_provider": {
        pid: {
          provider_name, fiber_type, fixed_dim, density,
          n, area_purchased, mass_purchased,
          placements,   ← [{"x","y","w","h","pc","pa","comp","ppb"}]
          all_pieces,   ← [(cross, along, qty, ppb, comp_name)]
          too_narrow: bool
        }
      },
      "totals": { geo_area, mass_used, resin, area_purchased, mass_purchased },
      "warnings": [...]
    }
    """
    ov    = settings["overlap"]
    gores = settings["cone_gores"]
    ratio = settings["resin_ratio"]

    global_warnings = []
    comp_results    = []
    prov_pieces     = {}   # {pid: [(pc, pa, qty, comp_name)]}

    for comp in components:
        p  = comp["params"]
        ct = comp["comp_type"]
        warns = []

        # Área geométrica
        if ct == "Cilindro":
            geo_area = cylinder_info(p["diameter"], p["length"])["area"]
        elif ct == "Cono / Ogiva":
            ci       = cone_info(p["base_diam"], p["height"], p["cone_type"])
            geo_area = ci["area"]
            if ci["warning"]:
                warns.append(ci["warning"])
        else:
            geo_area = fin_info(p["root"], p["tip"], p["span"], p["count"],
                                p.get("sweep_type", "length"),
                                p.get("sweep_value", 0.0), p.get("thickness", 0.0))["total_area"]

        # Engorde
        pb_id = comp["prov_bulk_id"]
        pb    = providers_by_id.get(pb_id) if pb_id else None
        pieces_bulk    = None
        mass_used_bulk = 0.0

        if comp["layers_bulk"] > 0:
            if not pb:
                warns.append("Capas de engorde sin proveedor asignado.")
            else:
                res_bulk = get_pieces(comp, "bulk", ov, gores)
                if res_bulk:
                    pc, pa, qty, ppb, shape = res_bulk
                    pieces_bulk = (pc, pa, qty, ppb)
                    prov_pieces.setdefault(pb_id, []).append(
                        (pc, pa, qty, comp["name"], ppb, shape))
                mass_used_bulk = geo_area * comp["layers_bulk"] * pb["density"]

        # Estética
        pa_id = comp["prov_aest_id"]
        pa_p  = providers_by_id.get(pa_id) if pa_id else None
        pieces_aest    = None
        mass_used_aest = 0.0

        if comp["layers_aesthetic"] > 0:
            if not pa_p:
                warns.append("Capas estéticas sin proveedor asignado.")
            else:
                res_aest = get_pieces(comp, "aesthetic", ov, gores)
                if res_aest:
                    pc, pa, qty, ppb, shape = res_aest
                    pieces_aest = (pc, pa, qty, ppb)
                    prov_pieces.setdefault(pa_id, []).append(
                        (pc, pa, qty, comp["name"], ppb, shape))
                mass_used_aest = geo_area * comp["layers_aesthetic"] * pa_p["density"]

        mass_used_total = mass_used_bulk + mass_used_aest
        resin           = mass_used_total * ratio

        comp_results.append({
            "name":            comp["name"],
            "comp_type":       ct,
            "geo_area":        geo_area,
            "layers_bulk":     comp["layers_bulk"],
            "layers_aest":     comp["layers_aesthetic"],
            "pieces_bulk":     pieces_bulk,
            "pieces_aest":     pieces_aest,
            "mass_used_bulk":  mass_used_bulk,
            "mass_used_aest":  mass_used_aest,
            "mass_used_total": mass_used_total,
            "resin":           resin,
            "warnings":        warns,
        })
        global_warnings.extend(warns)

    # ── Paso 2: MaxRects packing global por proveedor ──────────
    by_provider = {}
    for pid, raw_pieces in prov_pieces.items():
        prov = providers_by_id[pid]
        W    = prov["fixed_dim"]

        # Agrupar piezas idénticas → acumular qty (ppb y shape_info del primero)
        grouped = {}
        for pc, pa, qty, cname, ppb, shape in raw_pieces:
            key = (round(pc, 8), round(pa, 8))
            if key not in grouped:
                grouped[key] = {"qty": 0, "comps": [], "ppb": ppb, "shape": shape}
            grouped[key]["qty"]   += qty
            grouped[key]["comps"].append(cname)

        # Lista para el packer: (pc, pa, qty, comp_label, ppb)
        pieces_for_pack = [
            (k[0], k[1], v["qty"],
             ", ".join(sorted(set(v["comps"]))),
             v["ppb"])
            for k, v in grouped.items()
        ]

        # Mapa de (pc,pa) → shape_info para enriquecer placements
        shape_map = {k: v["shape"] for k, v in grouped.items()}

        result = maxrects_pack(W, pieces_for_pack)

        if result is None:
            too_narrow = True
            n = 0; placements = []
            global_warnings.append(
                f"Proveedor «{prov['name']}»: alguna pieza excede el ancho "
                f"del rollo ({W} m). Revisa dimensiones o proveedor.")
        else:
            too_narrow = False
            n, placements = result
            # Enriquecer placements con shape_info
            for pl in placements:
                key = (round(pl["pc"], 8), round(pl["pa"], 8))
                pl["shape"] = shape_map.get(key) or shape_map.get(
                    (round(pl["pa"], 8), round(pl["pc"], 8)))

        area_purchased = W * n
        mass_purchased = area_purchased * prov["density"]

        by_provider[pid] = {
            "provider_name":  prov["name"],
            "fiber_type":     prov["fiber_type"],
            "fixed_dim":      W,
            "density":        prov["density"],
            "n":              n,
            "area_purchased": area_purchased,
            "mass_purchased": mass_purchased,
            "placements":     placements,
            "all_pieces":     pieces_for_pack,
            "too_narrow":     too_narrow,
        }

    # ── Paso 3: totales ────────────────────────────────────────
    totals = {
        "geo_area":       sum(r["geo_area"]        for r in comp_results),
        "mass_used":      sum(r["mass_used_total"] for r in comp_results),
        "resin":          sum(r["resin"]           for r in comp_results),
        "area_purchased": sum(v["area_purchased"]  for v in by_provider.values()),
        "mass_purchased": sum(v["mass_purchased"]  for v in by_provider.values()),
    }

    return {
        "components":  comp_results,
        "by_provider": by_provider,
        "totals":      totals,
        "warnings":    global_warnings,
    }


# ─────────────────────────────────────────────────────────────────
# CÁLCULO COMPLETO DE UN COMPONENTE (legacy, mantenido por compatibilidad)
# ─────────────────────────────────────────────────────────────────

def calc_component(comp, prov_bulk, prov_aest, settings):
    """
    Calcula para un componente:
        - n_bulk, n_aest (metros de rollo necesarios)
        - area_bulk, area_aest (m² de fibra real utilizada)
        - mass_bulk, mass_aest (gramos de fibra)
        - resin_total (gramos de resina)
        - warnings (lista de cadenas)

    Retorna dict con todos estos campos, o dict con 'error' si algo falla.
    """
    s     = settings
    ov    = s["overlap"]
    ratio = s["resin_ratio"]
    gores = s["cone_gores"]
    ctype = comp["comp_type"]
    p     = comp["params"]
    warnings = []

    # ── Capas y proveedores ─────────────────────────────────────
    lb = comp["layers_bulk"]
    la = comp["layers_aesthetic"]

    def _cut_info(fixed_w, layers, comp_type, p, gores, ov):
        if layers == 0:
            return None
        if comp_type == "Cilindro":
            gi = cylinder_info(p["diameter"], p["length"])
            return cut_cylinder(fixed_w, ov, gi["perimeter"], gi["length"], layers), gi
        elif comp_type == "Cono / Ogiva":
            ci = cone_info(p["base_diam"], p["height"], p["cone_type"])
            if ci["warning"]:
                warnings.append(ci["warning"])
            return cut_cone(fixed_w, ov, ci["arc"], ci["perimeter"], layers, gores), ci
        else:  # Aleta
            fi = fin_info(p["root"], p["tip"], p["span"], p["count"], p.get("sweep_type","length"), p.get("sweep_value",0.0), p.get("thickness",0.0))
            return cut_fin(fixed_w, ov, fi["bnd_w"], fi["bnd_h"], fi["count"], layers), fi

    # ── Engorde ────────────────────────────────────────────────
    n_bulk = 0; area_bulk = 0.0; mass_bulk = 0.0; cut_bulk = None
    if lb > 0 and prov_bulk:
        res = _cut_info(prov_bulk["fixed_dim"], lb, ctype, p, gores, ov)
        if res:
            cut_bulk, geo = res
            if cut_bulk is None:
                warnings.append(
                    f"Rollo engorde ({prov_bulk['name']}) muy angosto para este componente.")
            else:
                n_bulk    = cut_bulk["n"]
                area_bulk = prov_bulk["fixed_dim"] * n_bulk
                mass_bulk = area_bulk * prov_bulk["density"]

    # ── Estética ───────────────────────────────────────────────
    n_aest = 0; area_aest = 0.0; mass_aest = 0.0; cut_aest = None
    if la > 0 and prov_aest:
        res = _cut_info(prov_aest["fixed_dim"], la, ctype, p, gores, ov)
        if res:
            cut_aest, geo = res
            if cut_aest is None:
                warnings.append(
                    f"Rollo estética ({prov_aest['name']}) muy angosto para este componente.")
            else:
                n_aest    = cut_aest["n"]
                area_aest = prov_aest["fixed_dim"] * n_aest
                mass_aest = area_aest * prov_aest["density"]

    total_mass  = mass_bulk + mass_aest
    resin_total = total_mass * ratio

    # Área geométrica real del componente (sin overlap)
    if ctype == "Cilindro":
        geo_area = cylinder_info(p["diameter"], p["length"])["area"]
    elif ctype == "Cono / Ogiva":
        geo_area = cone_info(p["base_diam"], p["height"], p["cone_type"])["area"]
    else:
        geo_area = fin_info(p["root"], p["tip"], p["span"], p["count"],
                            p.get("sweep_type", "length"),
                            p.get("sweep_value", 0.0), p.get("thickness", 0.0))["total_area"]

    return {
        "name":        comp["name"],
        "comp_type":   ctype,
        "geo_area":    geo_area,
        "n_bulk":      n_bulk,
        "n_aest":      n_aest,
        "area_bulk":   area_bulk,
        "area_aest":   area_aest,
        "mass_bulk":   mass_bulk,
        "mass_aest":   mass_aest,
        "resin_total": resin_total,
        "cut_bulk":    cut_bulk,
        "cut_aest":    cut_aest,
        "warnings":    warnings,
    }
