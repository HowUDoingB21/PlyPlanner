# tab_componentes.py — Gestión de componentes del cohete
import tkinter as tk
from tkinter import ttk, messagebox
from estilos import C, FONT_BOLD, FONT_SMALL, tree_with_scroll
from modelos import new_component, COMP_TYPES, CONE_TYPES, FIBER_TYPES


# ─────────────────────────────────────────────────────────────────
# DIÁLOGO: Agregar / Editar componente
# ─────────────────────────────────────────────────────────────────
class ComponentDialog(tk.Toplevel):
    def __init__(self, parent, app, data=None):
        super().__init__(parent)
        self.app    = app
        self.result = None
        self.configure(bg=C["base"])
        self.resizable(False, False)
        self.title("Componente" if not data else f"Editar — {data.get('name','')}")
        self._build(data or {})
        self.grab_set()
        self.transient(parent)
        self.wait_window()

    # ── Construcción del diálogo ──────────────────────────────

    def _build(self, d):
        pad = dict(padx=12, pady=5)

        # Título interno
        tk.Label(self, text="Definir componente",
                 bg=C["base"], fg=C["blue"], font=FONT_BOLD
                 ).grid(row=0, column=0, columnspan=4, pady=(14, 4))

        # Nombre
        tk.Label(self, text="Nombre *", bg=C["base"], fg=C["text"],
                 anchor="e", width=24).grid(row=1, column=0, **pad)
        self.v_name = tk.StringVar(value=d.get("name", ""))
        ttk.Entry(self, textvariable=self.v_name, width=28
                  ).grid(row=1, column=1, columnspan=3, **pad)

        # Tipo de componente
        tk.Label(self, text="Tipo *", bg=C["base"], fg=C["text"],
                 anchor="e", width=24).grid(row=2, column=0, **pad)
        self.v_type = tk.StringVar(value=d.get("comp_type", COMP_TYPES[0]))
        cb = ttk.Combobox(self, textvariable=self.v_type,
                          values=COMP_TYPES, state="readonly", width=18)
        cb.grid(row=2, column=1, **pad)
        cb.bind("<<ComboboxSelected>>", lambda _e: self._update_params())

        # Capas
        tk.Label(self, text="Capas engorde *", bg=C["base"], fg=C["text"],
                 anchor="e", width=24).grid(row=3, column=0, **pad)
        self.v_lb = tk.StringVar(value=str(d.get("layers_bulk", 2)))
        ttk.Spinbox(self, from_=0, to=20, textvariable=self.v_lb,
                    width=6).grid(row=3, column=1, sticky="w", **pad)

        tk.Label(self, text="Capas estética *", bg=C["base"], fg=C["text"],
                 anchor="e", width=24).grid(row=4, column=0, **pad)
        self.v_la = tk.StringVar(value=str(d.get("layers_aesthetic", 1)))
        ttk.Spinbox(self, from_=0, to=20, textvariable=self.v_la,
                    width=6).grid(row=4, column=1, sticky="w", **pad)

        # Proveedores
        self._prov_bulk = self._prov_list("engorde")
        self._prov_aest = self._prov_list("estetica")

        tk.Label(self, text="Proveedor engorde", bg=C["base"], fg=C["text"],
                 anchor="e", width=24).grid(row=5, column=0, **pad)
        self.v_pb = tk.StringVar(value=self._id_to_display(
            d.get("prov_bulk_id"), "engorde"))
        self.cb_pb = ttk.Combobox(self, textvariable=self.v_pb,
                                  values=self._prov_bulk, state="readonly", width=26)
        self.cb_pb.grid(row=5, column=1, columnspan=3, **pad)

        tk.Label(self, text="Proveedor estética", bg=C["base"], fg=C["text"],
                 anchor="e", width=24).grid(row=6, column=0, **pad)
        self.v_pa = tk.StringVar(value=self._id_to_display(
            d.get("prov_aest_id"), "estetica"))
        self.cb_pa = ttk.Combobox(self, textvariable=self.v_pa,
                                  values=self._prov_aest, state="readonly", width=26)
        self.cb_pa.grid(row=6, column=1, columnspan=3, **pad)

        # ── Frame de parámetros (se rellena dinámicamente) ─────
        sep = ttk.Separator(self, orient="horizontal")
        sep.grid(row=7, column=0, columnspan=4, sticky="ew", pady=6, padx=12)

        self.params_frame = tk.Frame(self, bg=C["base"])
        self.params_frame.grid(row=8, column=0, columnspan=4, sticky="ew")
        self._param_vars = {}
        self._update_params(initial=d.get("params", {}))

        # Botones
        bf = tk.Frame(self, bg=C["base"])
        bf.grid(row=9, column=0, columnspan=4, pady=14)
        ttk.Button(bf, text="Guardar",  command=self._save ).pack(side=tk.LEFT, padx=8)
        ttk.Button(bf, text="Cancelar", command=self.destroy,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=8)

    # ── Proveedores helpers ───────────────────────────────────

    def _prov_list(self, ftype):
        return ["(ninguno)"] + [
            f"{p['name']}  [{p['fixed_dim']:.2f}m × n]"
            for p in self.app.db["providers"]
            if p["fiber_type"] == ftype
        ]

    def _id_to_display(self, pid, ftype):
        if not pid:
            return "(ninguno)"
        p = next((x for x in self.app.db["providers"]
                  if x["id"] == pid and x["fiber_type"] == ftype), None)
        if not p:
            return "(ninguno)"
        return f"{p['name']}  [{p['fixed_dim']:.2f}m × n]"

    def _display_to_id(self, display, ftype):
        if display == "(ninguno)":
            return None
        for p in self.app.db["providers"]:
            if p["fiber_type"] == ftype and display.startswith(p["name"] + " "):
                return p["id"]
        return None

    # ── Parámetros dinámicos ──────────────────────────────────

    def _update_params(self, initial=None):
        for w in self.params_frame.winfo_children():
            w.destroy()
        self._param_vars = {}
        ct = self.v_type.get()
        ini = initial or {}

        def row_entry(r, label, key, default, fg=None):
            tk.Label(self.params_frame, text=label,
                     bg=C["base"], fg=fg or C["text"],
                     anchor="e", width=26
                     ).grid(row=r, column=0, padx=12, pady=4)
            var = tk.StringVar(value=str(ini.get(key, default)))
            ttk.Entry(self.params_frame, textvariable=var, width=14
                      ).grid(row=r, column=1, padx=12, pady=4, sticky="w")
            self._param_vars[key] = var

        if ct == "Cilindro":
            tk.Label(self.params_frame, text="— Parámetros del Cilindro —",
                     bg=C["base"], fg=C["blue"], font=FONT_BOLD
                     ).grid(row=0, column=0, columnspan=2, pady=(4, 2))
            row_entry(1, "Diámetro exterior (m) *", "diameter", "")
            row_entry(2, "Longitud (m) *",           "length",   "")

        elif ct == "Cono / Ogiva":
            tk.Label(self.params_frame, text="— Parámetros del Cono / Ogiva —",
                     bg=C["base"], fg=C["blue"], font=FONT_BOLD
                     ).grid(row=0, column=0, columnspan=2, pady=(4, 2))
            row_entry(1, "Diámetro de base (m) *", "base_diam", "")
            row_entry(2, "Altura (m) *",            "height",   "")
            # Tipo de ogiva
            tk.Label(self.params_frame, text="Tipo de ogiva *",
                     bg=C["base"], fg=C["text"],
                     anchor="e", width=26
                     ).grid(row=3, column=0, padx=12, pady=4)
            ct_var = tk.StringVar(value=ini.get("cone_type", CONE_TYPES[0]))
            ttk.Combobox(self.params_frame, textvariable=ct_var,
                         values=CONE_TYPES, state="readonly", width=20
                         ).grid(row=3, column=1, padx=12, pady=4, sticky="w")
            self._param_vars["cone_type"] = ct_var

        else:  # Aleta
            tk.Label(self.params_frame, text="— Parámetros de la Aleta —",
                     bg=C["base"], fg=C["blue"], font=FONT_BOLD
                     ).grid(row=0, column=0, columnspan=3, pady=(4, 2))
            row_entry(1, "Cuerda raíz (m) *",   "root",  "")
            row_entry(2, "Cuerda punta (m) *",   "tip",   "")
            row_entry(3, "Envergadura (m) *",     "span",  "")
            row_entry(4, "Número de aletas *",    "count", "4")
            row_entry(5, "Espesor de aleta (m) *", "thickness", str(ini.get("thickness", "0.003")))

            # Separador flechado
            ttk.Separator(self.params_frame, orient="horizontal").grid(
                row=5, column=0, columnspan=3, sticky="ew", padx=8, pady=6)
            tk.Label(self.params_frame, text="— Flechado (Sweep) —",
                     bg=C["base"], fg=C["blue"], font=FONT_BOLD
                     ).grid(row=6, column=0, columnspan=3, pady=(0, 2))

            # Tipo de flechado: radio buttons
            sweep_type_var = tk.StringVar(value=ini.get("sweep_type", "length"))
            self._param_vars["sweep_type"] = sweep_type_var

            rb_frame = tk.Frame(self.params_frame, bg=C["base"])
            rb_frame.grid(row=7, column=0, columnspan=3, sticky="w", padx=12, pady=2)

            def _update_sweep_label(*_):
                lbl = "Distancia de flechado (m)" if sweep_type_var.get() == "length" \
                      else "Ángulo de flechado (°)"
                sweep_lbl_var.set(lbl + " *")

            tk.Radiobutton(rb_frame, text="Distancia (m)",
                           variable=sweep_type_var, value="length",
                           bg=C["base"], fg=C["text"],
                           selectcolor=C["surface0"], activebackground=C["base"],
                           command=_update_sweep_label
                           ).pack(side=tk.LEFT, padx=(0, 16))
            tk.Radiobutton(rb_frame, text="Ángulo (°)",
                           variable=sweep_type_var, value="angle",
                           bg=C["base"], fg=C["text"],
                           selectcolor=C["surface0"], activebackground=C["base"],
                           command=_update_sweep_label
                           ).pack(side=tk.LEFT)

            # Campo de valor de flechado con etiqueta dinámica
            sweep_lbl_var = tk.StringVar()
            _update_sweep_label()
            tk.Label(self.params_frame, textvariable=sweep_lbl_var,
                     bg=C["base"], fg=C["text"],
                     anchor="e", width=26
                     ).grid(row=8, column=0, padx=12, pady=4)
            sv = tk.StringVar(value=str(ini.get("sweep_value", "0")))
            self._param_vars["sweep_value"] = sv
            ttk.Entry(self.params_frame, textvariable=sv, width=14
                      ).grid(row=8, column=1, padx=12, pady=4, sticky="w")

            # Nota informativa
            tk.Label(self.params_frame,
                     text="ℹ  El flechado no cambia el área, sí cambia la caja de corte.",
                     bg=C["base"], fg=C["overlay0"], font=("Segoe UI", 8),
                     ).grid(row=9, column=0, columnspan=3, padx=12, pady=(0, 4), sticky="w")

    # ── Guardar ───────────────────────────────────────────────

    def _save(self):
        name = self.v_name.get().strip()
        if not name:
            messagebox.showwarning("Campo requerido", "El nombre no puede estar vacío.", parent=self)
            return
        ct = self.v_type.get()
        try:
            lb = int(self.v_lb.get())
            la = int(self.v_la.get())
            if lb < 0 or la < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Valor inválido", "Las capas deben ser enteros ≥ 0.", parent=self)
            return

        # Validar parámetros según tipo
        params = {}
        try:
            if ct == "Cilindro":
                params["diameter"] = float(self._param_vars["diameter"].get())
                params["length"]   = float(self._param_vars["length"].get())
                if params["diameter"] <= 0 or params["length"] <= 0:
                    raise ValueError("Dimensiones deben ser > 0")
            elif ct == "Cono / Ogiva":
                params["base_diam"]  = float(self._param_vars["base_diam"].get())
                params["height"]     = float(self._param_vars["height"].get())
                params["cone_type"]  = self._param_vars["cone_type"].get()
                if params["base_diam"] <= 0 or params["height"] <= 0:
                    raise ValueError("Dimensiones deben ser > 0")
            else:
                params["root"]        = float(self._param_vars["root"].get())
                params["tip"]         = float(self._param_vars["tip"].get())
                params["span"]        = float(self._param_vars["span"].get())
                params["count"]       = int(self._param_vars["count"].get())
                params["thickness"]   = float(self._param_vars["thickness"].get())
                params["sweep_type"]  = self._param_vars["sweep_type"].get()
                params["sweep_value"] = float(self._param_vars["sweep_value"].get())
                if params["root"] <= 0 or params["span"] <= 0 or params["count"] < 1:
                    raise ValueError("Dimensiones deben ser > 0 y count ≥ 1")
                if params["thickness"] < 0:
                    raise ValueError("El espesor no puede ser negativo")
                if params["sweep_value"] < 0:
                    raise ValueError("El flechado no puede ser negativo")
                if params["sweep_type"] == "angle" and params["sweep_value"] >= 90:
                    raise ValueError("El ángulo de flechado debe ser < 90°")
        except (ValueError, KeyError) as e:
            messagebox.showwarning("Valor inválido",
                f"Revisa los parámetros: {e}", parent=self)
            return

        pb_id = self._display_to_id(self.v_pb.get(), "engorde")
        pa_id = self._display_to_id(self.v_pa.get(), "estetica")

        self.result = dict(
            name              = name,
            comp_type         = ct,
            layers_bulk       = lb,
            layers_aesthetic  = la,
            prov_bulk_id      = pb_id,
            prov_aest_id      = pa_id,
            params            = params,
        )
        self.destroy()


# ─────────────────────────────────────────────────────────────────
# TAB
# ─────────────────────────────────────────────────────────────────
class ComponentsTab(ttk.Frame):
    COLS = ("name", "comp_type", "layers_bulk", "layers_aesthetic",
            "prov_bulk", "prov_aest", "info")
    HDRS = ("Componente", "Tipo", "Cap. engorde", "Cap. estética",
            "Proveedor engorde", "Proveedor estética", "Dimensiones")
    WDTS = (160, 100, 100, 110, 160, 160, 280)

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, padx=12, pady=8)
        ttk.Button(bar, text="＋  Agregar",
                   command=self._add).pack(side=tk.LEFT, padx=3)
        ttk.Button(bar, text="✎  Editar",
                   command=self._edit).pack(side=tk.LEFT, padx=3)
        ttk.Button(bar, text="✕  Eliminar",
                   command=self._delete, style="Danger.TButton").pack(side=tk.LEFT, padx=3)
        tk.Label(bar, text="  Doble clic para editar",
                 bg=C["base"], fg=C["sub0"], font=FONT_SMALL
                 ).pack(side=tk.LEFT, padx=10)

        f, self.tree = tree_with_scroll(
            self, self.COLS, self.HDRS, self.WDTS, height=18)
        f.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        self.tree.bind("<Double-1>", lambda _e: self._edit())
        self._refresh()

    # ── Helpers ───────────────────────────────────────────────

    def _prov_name(self, pid):
        if not pid:
            return "—"
        p = next((x for x in self.app.db["providers"] if x["id"] == pid), None)
        return p["name"] if p else "?"

    def _dim_summary(self, comp):
        p = comp["params"]
        ct = comp["comp_type"]
        if ct == "Cilindro":
            return f"Ø{p['diameter']}m  L={p['length']}m"
        elif ct == "Cono / Ogiva":
            return f"Ø{p['base_diam']}m  H={p['height']}m  [{p['cone_type']}]"
        else:
            sweep = ""
            if p.get("sweep_value", 0) != 0:
                unit = "°" if p.get("sweep_type") == "angle" else "m"
                sweep = f"  flechado={p['sweep_value']}{unit}"
            return (f"raíz={p['root']}m  punta={p['tip']}m  "
                    f"enverg={p['span']}m  ×{p['count']}{sweep}")

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for c in self.app.db["components"]:
            self.tree.insert("", "end", iid=c["id"], values=(
                c["name"],
                c["comp_type"],
                c["layers_bulk"],
                c["layers_aesthetic"],
                self._prov_name(c["prov_bulk_id"]),
                self._prov_name(c["prov_aest_id"]),
                self._dim_summary(c),
            ))

    def _selected_id(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    # ── CRUD ──────────────────────────────────────────────────

    def _add(self):
        dlg = ComponentDialog(self, self.app)
        if dlg.result:
            r = dlg.result
            c = new_component(
                r["name"], r["comp_type"],
                r["layers_bulk"], r["layers_aesthetic"],
                r["prov_bulk_id"], r["prov_aest_id"], r["params"])
            self.app.db["components"].append(c)
            self.app.save()
            self._refresh()

    def _edit(self):
        cid = self._selected_id()
        if not cid:
            messagebox.showinfo("Sin selección", "Selecciona un componente primero.", parent=self)
            return
        comp = next(c for c in self.app.db["components"] if c["id"] == cid)
        dlg  = ComponentDialog(self, self.app, comp)
        if dlg.result:
            r = dlg.result
            comp.update({
                "name":             r["name"],
                "comp_type":        r["comp_type"],
                "layers_bulk":      r["layers_bulk"],
                "layers_aesthetic": r["layers_aesthetic"],
                "prov_bulk_id":     r["prov_bulk_id"],
                "prov_aest_id":     r["prov_aest_id"],
                "params":           r["params"],
            })
            self.app.save()
            self._refresh()

    def _delete(self):
        cid = self._selected_id()
        if not cid:
            messagebox.showinfo("Sin selección", "Selecciona un componente primero.", parent=self)
            return
        comp = next(c for c in self.app.db["components"] if c["id"] == cid)
        if messagebox.askyesno("Confirmar",
                f"¿Eliminar componente «{comp['name']}»?", parent=self):
            self.app.db["components"] = [
                c for c in self.app.db["components"] if c["id"] != cid]
            self.app.save()
            self._refresh()
