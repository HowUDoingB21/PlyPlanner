# tab_resultados.py — Cálculo y visualización de resultados (optimización global)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from estilos import C, FONT_BOLD, FONT_SMALL, FONT_MONO, tree_with_scroll
from geometria import calc_all


class ResultsTab(ttk.Frame):

    COLS_COMP = ("name", "type", "geo_area",
                 "lb", "pieces_b", "la", "pieces_a",
                 "mass_used", "resin")
    HDRS_COMP = ("Componente", "Tipo", "Área geom. m²",
                 "Cap.eng.", "Piezas eng.",
                 "Cap.est.", "Piezas est.",
                 "Masa usada g", "Resina g")
    WDTS_COMP = (150, 100, 110, 70, 160, 70, 160, 110, 100)

    COLS_PROV = ("pname", "ftype", "fixed", "n", "area", "mass_purch")
    HDRS_PROV = ("Proveedor", "Fibra", "Dim. fija (m)",
                 "n a comprar (m)", "Área comprada m²", "Masa comprada g")
    WDTS_PROV = (180, 90, 110, 140, 150, 140)

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app   = app
        self._data = None
        self._build()

    def _build(self):
        self.rowconfigure(1, weight=2)
        self.rowconfigure(2, weight=2)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=0)
        self.columnconfigure(0, weight=1)

        # Botones
        bar = ttk.Frame(self)
        bar.grid(row=0, column=0, sticky="ew", padx=12, pady=8)
        ttk.Button(bar, text="▶  Calcular",
                   style="Action.TButton", command=self._run).pack(side=tk.LEFT, padx=4)
        ttk.Button(bar, text="💾  Exportar TXT",
                   command=self._export_txt).pack(side=tk.LEFT, padx=4)
        tk.Label(bar,
                 text="  Los componentes que comparten proveedor se empaquetan juntos en el mismo rollo.",
                 bg=C["base"], fg=C["sub0"], font=FONT_SMALL
                 ).pack(side=tk.LEFT, padx=12)

        # Tabla componentes
        lf_c = ttk.LabelFrame(self, text="  Geometría y masa por componente  ")
        lf_c.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 4))
        lf_c.rowconfigure(0, weight=1); lf_c.columnconfigure(0, weight=1)
        f, self.tree_comp = tree_with_scroll(
            lf_c, self.COLS_COMP, self.HDRS_COMP, self.WDTS_COMP, height=6)
        f.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.tree_comp.bind("<<TreeviewSelect>>", self._on_comp_select)

        # Tabla proveedores
        lf_p = ttk.LabelFrame(
            self,
            text="  Metros a comprar por proveedor  "
                 "(optimizado: todos los componentes comparten el mismo rollo)  ")
        lf_p.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 4))
        lf_p.rowconfigure(0, weight=1); lf_p.columnconfigure(0, weight=1)
        f2, self.tree_prov = tree_with_scroll(
            lf_p, self.COLS_PROV, self.HDRS_PROV, self.WDTS_PROV, height=5)
        f2.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self.tree_prov.bind("<<TreeviewSelect>>", self._on_prov_select)

        # Detalle
        dp = ttk.LabelFrame(self, text="  Detalle  (clic en componente o proveedor)  ")
        dp.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 4))
        dp.rowconfigure(0, weight=1); dp.columnconfigure(0, weight=1)
        self.detail_text = tk.Text(
            dp, height=7, bg=C["surface0"], fg=C["text"], font=FONT_MONO,
            relief="flat", insertbackground=C["text"], state="disabled", wrap="word")
        sb = ttk.Scrollbar(dp, orient="vertical", command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=sb.set)
        self.detail_text.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=6)
        sb.grid(row=0, column=1, sticky="ns", pady=6, padx=(0, 4))

        # Totales
        tf = ttk.LabelFrame(self, text="  Totales del cohete  ", padding=10)
        tf.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))
        total_fields = [
            ("Área geométrica total",  "_tot_geo",    "m²"),
            ("Masa fibra usada",       "_tot_used",   "g"),
            ("Resina necesaria",       "_tot_resin",  "g"),
            ("Área de rollo comprada", "_tot_area_p", "m²"),
            ("Masa de rollo comprada", "_tot_mass_p", "g"),
        ]
        for i, (lbl, attr, unit) in enumerate(total_fields):
            tk.Label(tf, text=lbl + ":", bg=C["base"], fg=C["sub0"],
                     font=FONT_SMALL, anchor="e", width=24
                     ).grid(row=0, column=i, padx=(10, 2), pady=(4, 0), sticky="e")
            var = tk.StringVar(value="—")
            setattr(self, attr, var)
            frm = tk.Frame(tf, bg=C["base"])
            frm.grid(row=1, column=i, padx=(10, 2), pady=(0, 6), sticky="w")
            tk.Label(frm, textvariable=var, bg=C["base"], fg=C["green"],
                     font=FONT_BOLD).pack(side=tk.LEFT)
            tk.Label(frm, text=" " + unit, bg=C["base"], fg=C["overlay0"],
                     font=FONT_SMALL).pack(side=tk.LEFT)

    # ── Cálculo ───────────────────────────────────────────────

    def _run(self):
        db = self.app.db
        if not db["components"]:
            messagebox.showinfo("Sin componentes",
                "Agrega al menos un componente.", parent=self)
            return
        prov_by_id = {p["id"]: p for p in db["providers"]}
        self._data = calc_all(db["components"], prov_by_id, db["settings"])
        self._populate_comp_tree()
        self._populate_prov_tree()
        self._populate_totals()

        # Actualizar pestaña de cortes automáticamente
        cuts_tab = getattr(self.app, "tab_cuts", None)
        if cuts_tab:
            cuts_tab.load_results(self._data)

        warns = self._data["warnings"]
        if warns:
            messagebox.showwarning("Advertencias",
                "\n\n".join(f"⚠  {w}" for w in warns), parent=self)

    # ── Poblar tablas ─────────────────────────────────────────

    def _pieces_str(self, pieces):
        if not pieces:
            return "—"
        pc, pa, qty, ppb = pieces
        ppb_str = f"  ×{ppb}/caja" if ppb > 1 else ""
        return f"{qty} cajas  [{pc:.3f}×{pa:.3f}m]{ppb_str}"

    def _populate_comp_tree(self):
        self.tree_comp.delete(*self.tree_comp.get_children())
        for i, r in enumerate(self._data["components"]):
            tag = "warn" if r["warnings"] else ""
            self.tree_comp.insert("", "end", iid=f"c{i}", tags=(tag,), values=(
                r["name"], r["comp_type"],
                f"{r['geo_area']:.4f}",
                r["layers_bulk"],  self._pieces_str(r["pieces_bulk"]),
                r["layers_aest"],  self._pieces_str(r["pieces_aest"]),
                f"{r['mass_used_total']:.2f}",
                f"{r['resin']:.2f}",
            ))
        self.tree_comp.tag_configure("warn", foreground=C["yellow"])

    def _populate_prov_tree(self):
        self.tree_prov.delete(*self.tree_prov.get_children())
        for pid, pv in self._data["by_provider"].items():
            tag = "narrow" if pv["too_narrow"] else ""
            self.tree_prov.insert("", "end", iid=f"p{pid}", tags=(tag,), values=(
                pv["provider_name"], pv["fiber_type"],
                f"{pv['fixed_dim']:.3f}",
                f"{pv['n']}",
                f"{pv['area_purchased']:.4f}",
                f"{pv['mass_purchased']:.2f}",
            ))
        self.tree_prov.tag_configure("narrow", foreground=C["red"])

    def _populate_totals(self):
        t = self._data["totals"]
        self._tot_geo.set   (f"{t['geo_area']:.4f}")
        self._tot_used.set  (f"{t['mass_used']:.2f}")
        self._tot_resin.set (f"{t['resin']:.2f}")
        self._tot_area_p.set(f"{t['area_purchased']:.4f}")
        self._tot_mass_p.set(f"{t['mass_purchased']:.2f}")

    # ── Detalle al seleccionar ────────────────────────────────

    def _on_comp_select(self, _e):
        sel = self.tree_comp.selection()
        if not sel or not self._data:
            return
        idx = int(sel[0][1:])
        r   = self._data["components"][idx]
        lines = [
            f"╔══  {r['name']}  ({r['comp_type']})  ══",
            f"  Área geométrica           : {r['geo_area']:.6f} m²",
            "",
            "  ── FIBRA DE ENGORDE ─────────────────────────────────",
        ]
        if r["pieces_bulk"]:
            pc, pa, qty, ppb = r["pieces_bulk"]
            lines += [
                f"  Cajas a cortar            : {qty}  (×{ppb} piezas/caja)" if ppb > 1
                    else f"  Cajas a cortar            : {qty}",
                f"  Tamaño de caja            : {pc:.4f} m × {pa:.4f} m",
                f"  Masa fibra usada          : {r['mass_used_bulk']:.2f} g",
                f"  (el n del rollo se calcula en la tabla de proveedores)",
            ]
        else:
            lines.append("  (sin capas de engorde)")
        lines += ["", "  ── FIBRA ESTÉTICA ───────────────────────────────────"]
        if r["pieces_aest"]:
            pc, pa, qty, ppb = r["pieces_aest"]
            lines += [
                f"  Cajas a cortar            : {qty}  (×{ppb} piezas/caja)" if ppb > 1
                    else f"  Cajas a cortar            : {qty}",
                f"  Tamaño de caja            : {pc:.4f} m × {pa:.4f} m",
                f"  Masa fibra usada          : {r['mass_used_aest']:.2f} g",
                f"  (el n del rollo se calcula en la tabla de proveedores)",
            ]
        else:
            lines.append("  (sin capas estéticas)")
        lines += [
            "",
            "  ── RESUMEN ──────────────────────────────────────────",
            f"  Masa total fibra usada    : {r['mass_used_total']:.2f} g",
            f"  Resina necesaria          : {r['resin']:.2f} g",
        ]
        if r["warnings"]:
            lines += ["", "  ── ADVERTENCIAS ─────────────────────────────────────"]
            for w in r["warnings"]:
                lines.append(f"  ⚠  {w}")
        self._set_detail("\n".join(lines))

    def _on_prov_select(self, _e):
        sel = self.tree_prov.selection()
        if not sel or not self._data:
            return
        pid = sel[0][1:]
        pv  = self._data["by_provider"].get(pid)
        if not pv:
            return
        lines = [
            f"╔══  {pv['provider_name']}  ({pv['fiber_type']})  ══",
            f"  Dimensión fija            : {pv['fixed_dim']:.3f} m",
            f"  n a comprar               : {pv['n']} m",
            f"  Área total comprada       : {pv['area_purchased']:.4f} m²",
            f"  Masa total comprada       : {pv['mass_purchased']:.2f} g",
            "",
            "  ── TODAS LAS PIEZAS EMPAQUETADAS EN ESTE ROLLO ──────",
        ]
        for pc, pa, qty, comps, ppb in pv["all_pieces"]:
            ppb_str = f"  ×{ppb}/caja" if ppb > 1 else ""
            lines.append(f"  {qty:>3} cajas  [{pc:.4f} × {pa:.4f} m]{ppb_str}  ← {comps}")

        if pv.get("placements"):
            lines += ["", "  ── DISTRIBUCIÓN EN EL ROLLO (Guillotine BSSF) ──────"]
            # Agrupar placements por componente para resumen
            from collections import Counter
            comp_count = Counter(p["comp"] for p in pv["placements"])
            for cname, cnt in sorted(comp_count.items()):
                lines.append(f"    {cnt:>3} pieza(s)  ← {cname}")
        self._set_detail("\n".join(lines))

    def _set_detail(self, txt):
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", txt)
        self.detail_text.configure(state="disabled")

    # ── Exportar ──────────────────────────────────────────────

    def _export_txt(self):
        if not self._data:
            messagebox.showinfo("Sin resultados",
                "Ejecuta el cálculo primero.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".txt",
            filetypes=[("Texto", "*.txt"), ("Todos", "*.*")],
            title="Exportar resultados",
        )
        if not path:
            return
        s = self.app.db["settings"]
        lines = [
            "═" * 68,
            "  CALCULADORA DE MATERIALES — COHETE",
            "═" * 68,
            f"  Overlap        : {s['overlap']} m",
            f"  Relación resina: {s['resin_ratio']} g/g",
            f"  Gajos/capa     : {s['cone_gores']}",
            "",
            "  NOTA: n por proveedor ya incluye optimización global.",
            "  Los sobrantes de un componente cubren otros del mismo rollo.",
            "",
        ]
        lines += ["═"*68, "  COMPONENTES", "═"*68]
        for r in self._data["components"]:
            lines += ["", f"  [{r['comp_type']}]  {r['name']}",
                      f"    Área geom.  : {r['geo_area']:.6f} m²"]
            if r["pieces_bulk"]:
                pc, pa, qty, ppb = r["pieces_bulk"]
                ppb_str = f" ×{ppb}/caja" if ppb > 1 else ""
                lines.append(f"    Engorde     : {qty} cajas{ppb_str} de {pc:.4f}×{pa:.4f} m  "
                              f"→  masa usada {r['mass_used_bulk']:.2f} g")
            if r["pieces_aest"]:
                pc, pa, qty, ppb = r["pieces_aest"]
                ppb_str = f" ×{ppb}/caja" if ppb > 1 else ""
                lines.append(f"    Estética    : {qty} cajas{ppb_str} de {pc:.4f}×{pa:.4f} m  "
                              f"→  masa usada {r['mass_used_aest']:.2f} g")
            lines += [f"    Masa total  : {r['mass_used_total']:.2f} g",
                      f"    Resina      : {r['resin']:.2f} g"]
        lines += ["", "═"*68, "  COMPRA POR PROVEEDOR", "═"*68]
        for pv in self._data["by_provider"].values():
            lines += [
                "",
                f"  {pv['provider_name']}  ({pv['fiber_type']})",
                f"  Rollo  : {pv['fixed_dim']:.3f} m × {pv['n']} m",
                f"  Área   : {pv['area_purchased']:.4f} m²",
                f"  Masa   : {pv['mass_purchased']:.2f} g",
                "  Piezas :",
            ]
            for pc, pa, qty, comps, ppb in pv["all_pieces"]:
                ppb_str = f" ×{ppb}/caja" if ppb > 1 else ""
                lines.append(f"    {qty:>3} cajas{ppb_str}  [{pc:.4f}×{pa:.4f} m]  ← {comps}")
        t = self._data["totals"]
        lines += [
            "", "═"*68, "  TOTALES", "═"*68,
            f"  Área geométrica total  : {t['geo_area']:.4f} m²",
            f"  Masa fibra usada       : {t['mass_used']:.2f} g",
            f"  Resina total           : {t['resin']:.2f} g",
            f"  Área rollo comprada    : {t['area_purchased']:.4f} m²",
            f"  Masa rollo comprada    : {t['mass_purchased']:.2f} g",
        ]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        messagebox.showinfo("Exportado", f"Guardado en:\n{path}", parent=self)
