# tab_cortes.py — Visualización gráfica del plan de cortes
import tkinter as tk
from tkinter import ttk
import math
from estilos import C, FONT_BOLD, FONT_SMALL, FONT_MONO

# Paleta de colores para componentes (cicla si hay más de 10)
PIECE_COLORS = [
    ("#89b4fa", "#1e1e2e"),  # blue
    ("#a6e3a1", "#1e1e2e"),  # green
    ("#fab387", "#1e1e2e"),  # peach
    ("#cba6f7", "#1e1e2e"),  # mauve
    ("#f38ba8", "#1e1e2e"),  # red
    ("#94e2d5", "#1e1e2e"),  # teal
    ("#f9e2af", "#1e1e2e"),  # yellow
    ("#89dceb", "#1e1e2e"),  # sky
    ("#b4befe", "#1e1e2e"),  # lavender
    ("#eba0ac", "#1e1e2e"),  # maroon
]

WASTE_COLOR   = ("#313244", "#585b70")   # superficie / borde desperdicio
SHELF_BORDER  = "#45475a"
ROLL_BG       = "#181825"
RULER_FG      = "#a6adc8"
TOOLTIP_BG    = "#313244"
TOOLTIP_FG    = "#cdd6f4"


# ─────────────────────────────────────────────────────────────────
# CANVAS DE ROLLO
# ─────────────────────────────────────────────────────────────────

class RollCanvas(tk.Canvas):
    """
    Dibuja el rollo de fibra con los estantes y piezas.
    Escala uniforme: se ajusta al ancho disponible y el rollo
    se desplaza verticalmente con scrollbar.
    Rueda del ratón: zoom.
    """

    MARGIN_LEFT  = 64
    MARGIN_TOP   = 44
    MARGIN_RIGHT = 24
    MARGIN_BOT   = 30
    MIN_SCALE    = 20    # px/m mínimo
    MAX_SCALE    = 2000  # px/m máximo

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["crust"],
                         highlightthickness=0, **kw)
        self._data        = None
        self._comp_colors = {}
        self._scale       = 100.0   # px por metro (uniforme X e Y)
        self._tooltip_win = None
        self._piece_rects = {}
        self._ox          = self.MARGIN_LEFT
        self._oy          = self.MARGIN_TOP

        self.bind("<Configure>",        self._on_resize)
        self.bind("<Motion>",           self._on_motion)
        self.bind("<Leave>",            self._hide_tooltip)
        self.bind("<MouseWheel>",       self._on_wheel)       # Windows
        self.bind("<Button-4>",         self._on_wheel)       # Linux scroll up
        self.bind("<Button-5>",         self._on_wheel)       # Linux scroll down

    # ── API pública ───────────────────────────────────────────

    def load(self, prov_data, comp_colors):
        self._data        = prov_data
        self._comp_colors = comp_colors
        self._piece_rects = {}
        self._fit_to_width()   # calcula escala óptima y dibuja

    def clear(self):
        self.delete("all")
        self._data = None

    # ── Escala y ajuste ───────────────────────────────────────

    def _fit_to_width(self):
        """Calcula la escala para que el ANCHO del rollo ocupe el alto del canvas."""
        self.update_idletasks()
        ch = self.winfo_height() or 500
        W_world = self._data["fixed_dim"] if self._data else 1.0
        usable  = ch - self.MARGIN_TOP - self.MARGIN_BOT
        self._scale = max(self.MIN_SCALE,
                          min(self.MAX_SCALE, usable / W_world))
        self._redraw()

    def _on_resize(self, _e):
        if self._data:
            self._fit_to_width()
        else:
            self._draw_empty()

    def _on_wheel(self, event):
        if not self._data:
            return
        if event.num == 4 or event.delta > 0:
            factor = 1.15
        else:
            factor = 1 / 1.15
        new_scale = max(self.MIN_SCALE,
                        min(self.MAX_SCALE, self._scale * factor))
        if abs(new_scale - self._scale) > 0.1:
            self._scale = new_scale
            self._redraw()

    def _redraw(self):
        self.delete("all")
        self._piece_rects = {}
        if not self._data:
            self._draw_empty()
            return

        W_world = self._data["fixed_dim"]   # alto del rollo (eje Y)
        N_world = self._data["n"]           # largo del rollo (eje X)
        if N_world <= 0:
            self._draw_empty()
            return

        s  = self._scale
        ox = self.MARGIN_LEFT   # origen X (izquierda)
        oy = self.MARGIN_TOP    # origen Y (arriba)

        self._ox = ox
        self._oy = oy

        # En modo horizontal:
        #   X  → largo del rollo (n)
        #   Y  → ancho del rollo (fixed_dim)
        # Cada placement tiene x,y,w,h en coordenadas de mundo.

        roll_h_px = W_world * s
        roll_w_px = N_world * s

        self.configure(scrollregion=(
            0, 0,
            ox + roll_w_px + self.MARGIN_RIGHT,
            oy + roll_h_px + self.MARGIN_BOT))

        # Fondo del rollo
        self.create_rectangle(ox, oy, ox + roll_w_px, oy + roll_h_px,
                              fill=ROLL_BG, outline=C["surface1"], width=2)

        # Cuadrícula de guía (cada metro)
        for v in range(1, N_world):
            gx = ox + v * s
            self.create_line(gx, oy, gx, oy + roll_h_px,
                             fill="#252535", width=1)

        # Dibujar placements
        placements = self._data.get("placements", [])
        for pl in placements:
            comp_name = pl["comp"]
            ppb       = pl.get("ppb", 1)
            shape     = pl.get("shape")
            fill, fg  = self._comp_colors.get(comp_name, (C["surface1"], C["text"]))

            px0 = ox + pl["x"] * s
            py0 = oy + pl["y"] * s
            px1 = ox + (pl["x"] + pl["w"]) * s
            py1 = oy + (pl["y"] + pl["h"]) * s

            # Fondo de la caja (siempre)
            rid = self.create_rectangle(px0, py0, px1, py1,
                                        fill=fill, outline=C["surface1"],
                                        width=1, dash=(4, 3))

            # Dibujar trapecio real si hay shape_info de aleta
            if shape and shape.get("type") == "fin":
                self._draw_fin_shape(px0, py0, pl["w"], pl["h"],
                                     shape, s, fill, fg, ppb)
            else:
                # Sin shape: relleno sólido con etiqueta
                self.create_rectangle(px0, py0, px1, py1,
                                      fill=fill, outline=C["crust"], width=1)

            # Línea diagonal para emparejamiento
            if ppb > 1 and not (shape and shape.get("type") == "fin"):
                self.create_line(px0, py0, px1, py1,
                                 fill=fg, dash=(3, 4), width=1)

            pw_px = px1 - px0
            ph_px = py1 - py0
            if pw_px > 36 and ph_px > 14:
                short  = comp_name[:16] + ("…" if len(comp_name) > 16 else "")
                label  = f"×{ppb} {short}" if ppb > 1 else short
                fsize  = max(7, min(10, int(min(pw_px, ph_px) / 8)))
                cx     = (px0 + px1) / 2
                cy     = py0 + ph_px * 0.15 if (shape and shape.get("type") == "fin") else (py0 + py1) / 2
                self.create_text(cx, cy, text=label, fill=fg,
                                 font=("Consolas", fsize), width=pw_px - 6)

            self._piece_rects[rid] = {
                "comp": comp_name,
                "pc": pl["pc"], "pa": pl["pa"],
                "w": pl["w"],   "h": pl["h"],
                "x0": pl["x"],  "y0": pl["y"],
                "ppb": ppb,
            }

        # Reglas
        self._draw_ruler_x(N_world, s, ox, oy, roll_h_px)
        self._draw_ruler_y(W_world, s, ox, oy)

        # Etiquetas totales
        self.create_text(
            ox + roll_w_px / 2, oy - 12,
            text=f"← largo a comprar:  n = {N_world} m →",
            fill=C["blue"], font=("Consolas", 9, "bold"))
        self.create_text(
            ox - 10, oy + roll_h_px / 2,
            text=f"{W_world:.3f} m", fill=C["blue"],
            font=("Consolas", 9, "bold"), angle=90, anchor="center")
        self.create_text(
            ox + roll_w_px, oy + roll_h_px + 18,
            text=f"zoom: {s:.0f} px/m  (rueda del ratón para ajustar)",
            fill=C["overlay0"], font=("Consolas", 8), anchor="e")

    def _draw_ruler_x(self, N_world, s, ox, oy, roll_h_px):
        tick_interval = self._nice_interval(N_world, max_ticks=20)
        v = 0.0
        while v <= N_world + 1e-9:
            x = ox + v * s
            self.create_line(x, oy + roll_h_px, x, oy + roll_h_px + 7,
                             fill=RULER_FG, width=1)
            self.create_text(x, oy + roll_h_px + 10, text=f"{v:.2f}",
                             fill=RULER_FG, font=("Consolas", 7), anchor="n")
            v = round(v + tick_interval, 6)
        self.create_line(ox, oy + roll_h_px + 1,
                         ox + N_world * s, oy + roll_h_px + 1,
                         fill=RULER_FG, width=1)

    def _draw_ruler_y(self, W_world, s, ox, oy):
        tick_interval = self._nice_interval(W_world, max_ticks=10)
        v = 0.0
        while v <= W_world + 1e-9:
            y = oy + v * s
            self.create_line(ox - 7, y, ox, y, fill=RULER_FG, width=1)
            self.create_text(ox - 10, y, text=f"{v:.2f}",
                             fill=RULER_FG, font=("Consolas", 7), anchor="e")
            v = round(v + tick_interval, 6)
        self.create_line(ox - 1, oy, ox - 1, oy + W_world * s,
                         fill=RULER_FG, width=1)

    @staticmethod
    def _nice_interval(span, max_ticks=10):
        raw = span / max_ticks
        mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 0.1
        for step in (1, 2, 2.5, 5, 10):
            if mag * step >= raw:
                return mag * step
        return mag * 10

    def _draw_fin_shape(self, box_x, box_y, box_w, box_h, shape, s, fill, fg, ppb):
        """
        Dibuja el trapecio real dentro de su caja de corte.
        Detecta la orientación real comparando las dimensiones del placement
        con bnd_h y bnd_w, en lugar de confiar en el flag 'swapped' precalculado
        (que puede discrepar si el packer decidió rotar la pieza).

        coords locales: lx = cuerda (0..bnd_h),  ly = span (0..bnd_w)
        Si X del canvas corresponde a cuerda: canvas_X=lx, canvas_Y=ly  (normal)
        Si X del canvas corresponde a span:   canvas_X=ly, canvas_Y=lx  (swapped)
        """
        bnd_h = shape["bnd_h"]   # cuerda + 2*th
        bnd_w = shape["bnd_w"]   # span   + 2*th
        if bnd_h < 1e-9 or bnd_w < 1e-9:
            return

        # Detectar orientación real: ¿qué dimensión local ocupa el eje X del canvas?
        # box_w es el extent X del placement, box_h es el extent Y.
        # Si box_w ≈ bnd_h (cuerda), entonces X=cuerda → normal (not swapped).
        # Si box_w ≈ bnd_w (span),   entonces X=span  → swapped.
        swapped = abs(box_w - bnd_w) < abs(box_w - bnd_h)

        bwpx = box_w * s
        bhpx = box_h * s

        if not swapped:
            def to_canvas(lx, ly):
                return (box_x + (lx / bnd_h) * bwpx,
                        box_y + (ly / bnd_w) * bhpx)
        else:
            def to_canvas(lx, ly):
                return (box_x + (ly / bnd_w) * bwpx,
                        box_y + (lx / bnd_h) * bhpx)

        pts = []
        for lx, ly in shape["corners"]:
            pts.extend(to_canvas(lx, ly))
        if len(pts) >= 6:
            self.create_polygon(pts, fill=fill, outline=fg, width=1)

    def _draw_empty(self):
        cw = self.winfo_width()  or 400
        ch = self.winfo_height() or 300
        self.create_text(cw / 2, ch / 2,
                         text="Calcula primero para ver el plan de cortes",
                         fill=C["sub0"], font=("Consolas", 11))

    # ── Tooltip ───────────────────────────────────────────────

    def _on_motion(self, event):
        hit = self._hit_piece(event.x, event.y)
        if hit:
            self._show_tooltip(event, hit)
        else:
            self._hide_tooltip()

    def _hit_piece(self, mx, my):
        ids = self.find_overlapping(mx - 1, my - 1, mx + 1, my + 1)
        for rid in reversed(ids):
            if rid in self._piece_rects:
                return self._piece_rects[rid]
        return None

    def _show_tooltip(self, event, info):
        self._hide_tooltip()
        tw = tk.Toplevel(self)
        tw.withdraw()                    # ocultar ANTES de que el WM lo muestre
        tw.wm_overrideredirect(True)
        tw.configure(bg=TOOLTIP_BG)
        ppb = info.get("ppb", 1)
        ppb_line = f"  (×{ppb} piezas por caja)\n" if ppb > 1 else ""
        txt = (
            f"Componente : {info['comp']}\n"
            f"Caja       : {info['w']:.4f} m (X) × {info['h']:.4f} m (Y)\n"
            f"Pieza real : {info['pc']:.4f} m × {info['pa']:.4f} m\n"
            f"{ppb_line}"
            f"Posición   : x={info['x0']:.4f} m, y={info['y0']:.4f} m"
        )
        tk.Label(tw, text=txt, bg=TOOLTIP_BG, fg=TOOLTIP_FG,
                 font=("Consolas", 9), justify=tk.LEFT,
                 padx=8, pady=6).pack()
        tw.update_idletasks()            # calcular tamaño real antes de posicionar
        x = event.x_root + 14
        y = event.y_root + 10
        tw.wm_geometry(f"+{x}+{y}")
        tw.deiconify()                   # mostrar ya en la posición correcta
        self._tooltip_win = tw

    def _hide_tooltip(self, _e=None):
        if self._tooltip_win:
            try:
                self._tooltip_win.destroy()
            except Exception:
                pass
            self._tooltip_win = None


# ─────────────────────────────────────────────────────────────────
# TAB PRINCIPAL
# ─────────────────────────────────────────────────────────────────

class CutsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app          = app
        self._data        = None   # resultado completo de calc_all
        self._prov_ids    = []     # orden de proveedores
        self._comp_colors = {}     # nombre → (fill, text)
        self._build()

    def _build(self):
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # ── Barra de controles ─────────────────────────────────
        bar = ttk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew", padx=12, pady=8)

        tk.Label(bar, text="Proveedor / rollo:",
                 bg=C["base"], fg=C["sub0"], font=FONT_SMALL
                 ).pack(side=tk.LEFT, padx=(0, 6))

        self._prov_var = tk.StringVar()
        self._prov_cb  = ttk.Combobox(bar, textvariable=self._prov_var,
                                      state="readonly", width=36)
        self._prov_cb.pack(side=tk.LEFT, padx=4)
        self._prov_cb.bind("<<ComboboxSelected>>", self._on_prov_change)

        ttk.Button(bar, text="⟳  Recargar desde cálculo",
                   command=self._reload, style="Secondary.TButton"
                   ).pack(side=tk.LEFT, padx=10)

        # ── Área central: canvas + leyenda ────────────────────
        center = ttk.Frame(self)
        center.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        center.rowconfigure(0, weight=1)
        center.columnconfigure(0, weight=1)
        center.columnconfigure(1, weight=0)

        # Canvas
        canvas_frame = tk.Frame(center, bg=C["crust"],
                                relief="flat", bd=1,
                                highlightbackground=C["surface1"],
                                highlightthickness=1)
        canvas_frame.grid(row=0, column=0, sticky="nsew")
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        self._canvas = RollCanvas(canvas_frame)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        # Scrollbars conectadas al canvas
        vsb = ttk.Scrollbar(canvas_frame, orient="vertical",
                            command=self._canvas.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(canvas_frame, orient="horizontal",
                            command=self._canvas.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self._canvas.configure(yscrollcommand=vsb.set,
                               xscrollcommand=hsb.set)

        # ── Panel de leyenda + stats ──────────────────────────
        right = ttk.Frame(center, width=210)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure(0, weight=1)

        lf_leg = ttk.LabelFrame(right, text="  Leyenda  ")
        lf_leg.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._legend_frame = lf_leg

        lf_stat = ttk.LabelFrame(right, text="  Estadísticas  ", padding=8)
        lf_stat.grid(row=1, column=0, sticky="ew")

        stat_fields = [
            ("Ancho rollo",       "_st_w",       "m"),
            ("Largo a comprar",   "_st_n",       "m"),
            ("Área comprada",     "_st_area",    "m²"),
            ("Piezas colocadas",  "_st_shelves", ""),
            ("Tipos de pieza",    "_st_pieces",  ""),
            ("Desperdicio",       "_st_waste",   "%"),
        ]
        for i, (lbl, attr, unit) in enumerate(stat_fields):
            tk.Label(lf_stat, text=lbl + ":",
                     bg=C["base"], fg=C["sub0"],
                     font=FONT_SMALL, anchor="w"
                     ).grid(row=i, column=0, sticky="w", pady=1)
            var = tk.StringVar(value="—")
            setattr(self, attr, var)
            tk.Label(lf_stat, textvariable=var,
                     bg=C["base"], fg=C["text"],
                     font=FONT_MONO, anchor="e"
                     ).grid(row=i, column=1, sticky="e", padx=(8, 2), pady=1)
            if unit:
                tk.Label(lf_stat, text=unit,
                         bg=C["base"], fg=C["overlay0"],
                         font=FONT_SMALL
                         ).grid(row=i, column=2, sticky="w", pady=1)

        lf_stat.columnconfigure(1, weight=1)

        # Nota inferior
        tk.Label(right,
                 text="Pasa el cursor sobre\nuna pieza para ver\nsu detalle.",
                 bg=C["base"], fg=C["overlay0"],
                 font=FONT_SMALL, justify=tk.LEFT
                 ).grid(row=2, column=0, sticky="w", pady=(12, 0))

    # ── API pública ───────────────────────────────────────────

    def load_results(self, calc_data):
        """Llamado desde ResultsTab después de calcular."""
        self._data     = calc_data
        self._assign_colors()
        self._populate_combo()

    # ── Internos ──────────────────────────────────────────────

    def _assign_colors(self):
        """Asigna un color a cada componente único."""
        if not self._data:
            return
        names = [c["name"] for c in self._data["components"]]
        seen  = {}
        idx   = 0
        for name in names:
            if name not in seen:
                seen[name] = PIECE_COLORS[idx % len(PIECE_COLORS)]
                idx += 1
        self._comp_colors = seen

    def _populate_combo(self):
        if not self._data:
            return
        entries     = []
        self._prov_ids = []
        for pid, pv in self._data["by_provider"].items():
            label = (f"{pv['provider_name']}  "
                     f"[{pv['fiber_type']}]  "
                     f"{pv['fixed_dim']:.3f} m × {pv['n']} m")
            entries.append(label)
            self._prov_ids.append(pid)

        self._prov_cb["values"] = entries
        if entries:
            self._prov_cb.current(0)
            self._show_provider(self._prov_ids[0])

    def _on_prov_change(self, _e):
        idx = self._prov_cb.current()
        if 0 <= idx < len(self._prov_ids):
            self._show_provider(self._prov_ids[idx])

    def _reload(self):
        """Recarga desde la pestaña de Resultados si ya existe cálculo."""
        # El app expone el último resultado a través de tab_res._data
        res_tab = getattr(self.app, "tab_res", None)
        if res_tab and res_tab._data:
            self.load_results(res_tab._data)
        else:
            from tkinter import messagebox
            messagebox.showinfo("Sin datos",
                "Primero ejecuta el cálculo en la pestaña Resultados.",
                parent=self)

    def _show_provider(self, pid):
        if not self._data:
            return
        pv = self._data["by_provider"].get(pid)
        if not pv:
            return

        self._canvas.load(pv, self._comp_colors)
        self._update_legend(pv)
        self._update_stats(pv)

    def _update_legend(self, pv):
        for w in self._legend_frame.winfo_children():
            w.destroy()

        seen_comps = set()
        for _, _, _, comp_name in pv["all_pieces"]:
            for cn in comp_name.split(", "):
                seen_comps.add(cn.strip())

        for i, cn in enumerate(sorted(seen_comps)):
            fill, _ = self._comp_colors.get(cn, (C["surface1"], C["text"]))
            row = tk.Frame(self._legend_frame, bg=C["base"])
            row.grid(row=i, column=0, sticky="w", padx=6, pady=2)
            # Swatch
            tk.Label(row, bg=fill, width=3, height=1,
                     relief="flat"
                     ).pack(side=tk.LEFT, padx=(0, 6))
            tk.Label(row, text=cn[:22] + ("…" if len(cn) > 22 else ""),
                     bg=C["base"], fg=C["text"],
                     font=FONT_SMALL
                     ).pack(side=tk.LEFT)

        # Desperdicio
        tk.Frame(self._legend_frame, bg=C["surface1"], height=1
                 ).grid(row=len(seen_comps), column=0,
                        sticky="ew", pady=4, padx=4)
        row = tk.Frame(self._legend_frame, bg=C["base"])
        row.grid(row=len(seen_comps) + 1, column=0,
                 sticky="w", padx=6, pady=2)
        tk.Label(row, bg=WASTE_COLOR[0], width=3, height=1,
                 relief="flat"
                 ).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(row, text="Desperdicio",
                 bg=C["base"], fg=C["sub0"],
                 font=FONT_SMALL
                 ).pack(side=tk.LEFT)

    def _update_stats(self, pv):
        W = pv["fixed_dim"]
        N = pv["n"]
        total_area   = W * N
        useful_area  = sum(p["w"] * p["h"] for p in pv.get("placements", []))
        waste_pct    = (1 - useful_area / total_area) * 100 if total_area > 0 else 0
        total_pieces = sum(qty for _, _, qty, _ in pv["all_pieces"])

        self._st_w.set      (f"{W:.3f}")
        self._st_n.set      (f"{N}")
        self._st_area.set   (f"{total_area:.4f}")
        self._st_shelves.set(f"{len(pv.get('placements', []))}")
        self._st_pieces.set (f"{total_pieces}")
        self._st_waste.set  (f"{waste_pct:.1f}")
