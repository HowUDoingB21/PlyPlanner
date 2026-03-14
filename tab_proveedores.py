# tab_proveedores.py — Gestión de proveedores de fibra de carbono
import tkinter as tk
from tkinter import ttk, messagebox
from estilos import C, FONT_BOLD, FONT_SMALL, tree_with_scroll
from modelos import new_provider, FIBER_TYPES


# ─────────────────────────────────────────────────────────────────
# DIÁLOGO: Agregar / Editar proveedor
# ─────────────────────────────────────────────────────────────────
class ProviderDialog(tk.Toplevel):
    def __init__(self, parent, title, data=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(bg=C["base"])
        self.result = None
        self._build(data or {})
        self.grab_set()
        self.transient(parent)
        self.wait_window()

    def _build(self, d):
        pad = dict(padx=14, pady=6)

        tk.Label(self, text="Datos del proveedor",
                 bg=C["base"], fg=C["blue"], font=FONT_BOLD
                 ).grid(row=0, column=0, columnspan=2, pady=(14, 6))

        fields = [
            ("Nombre *",          "name",      "str",   d.get("name",      "")),
            ("Tipo de fibra *",   "fiber_type","combo", d.get("fiber_type", FIBER_TYPES[0])),
            ("Dimensión fija (m)*","fixed_dim", "float", d.get("fixed_dim", "")),
            ("Densidad (g/m²) *", "density",   "float", d.get("density",   "")),
            ("Precio por metro n","price",      "float", d.get("price",     "0")),
            ("Notas",             "notes",      "str",   d.get("notes",     "")),
        ]

        self._vars = {}
        for r, (label, key, ftype, val) in enumerate(fields, start=1):
            tk.Label(self, text=label, bg=C["base"], fg=C["text"],
                     anchor="e", width=22).grid(row=r, column=0, **pad)
            if ftype == "combo":
                var = tk.StringVar(value=val)
                w   = ttk.Combobox(self, textvariable=var,
                                   values=FIBER_TYPES, state="readonly", width=18)
            else:
                var = tk.StringVar(value=str(val))
                w   = ttk.Entry(self, textvariable=var, width=20)
            w.grid(row=r, column=1, **pad)
            self._vars[key] = var

        # Botones
        bf = tk.Frame(self, bg=C["base"])
        bf.grid(row=len(fields)+1, column=0, columnspan=2, pady=12)
        ttk.Button(bf, text="Guardar",  command=self._save ).pack(side=tk.LEFT, padx=6)
        ttk.Button(bf, text="Cancelar", command=self.destroy,
                   style="Secondary.TButton").pack(side=tk.LEFT, padx=6)

    def _save(self):
        v = {k: var.get().strip() for k, var in self._vars.items()}
        if not v["name"]:
            messagebox.showwarning("Campo requerido", "El nombre no puede estar vacío.", parent=self)
            return
        for key in ("fixed_dim", "density", "price"):
            try:
                val = float(v[key])
                if key != "price" and val <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Valor inválido",
                    f"'{key}' debe ser un número positivo.", parent=self)
                return
        self.result = v
        self.destroy()


# ─────────────────────────────────────────────────────────────────
# TAB
# ─────────────────────────────────────────────────────────────────
class ProvidersTab(ttk.Frame):
    COLS = ("name", "fiber_type", "fixed_dim", "density", "price", "notes")
    HDRS = ("Proveedor", "Tipo fibra", "Dim. fija (m)", "Densidad g/m²", "Precio / m_n", "Notas")
    WDTS = (170,          100,           120,             120,             110,             250)

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        # ── Barra de acciones ──────────────────────────────────
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

        # ── Treeview ───────────────────────────────────────────
        f, self.tree = tree_with_scroll(
            self, self.COLS, self.HDRS, self.WDTS, height=18)
        f.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
        self.tree.bind("<Double-1>", lambda _e: self._edit())

        # ── Info de leyenda ────────────────────────────────────
        tk.Label(self,
                 text="  * Dim. fija: el ancho constante del rollo (p.ej. 2 m).  "
                      "n se calcula automáticamente según las piezas necesarias.",
                 bg=C["base"], fg=C["sub0"], font=FONT_SMALL
                 ).pack(anchor="w", padx=12, pady=(0, 8))

        self._refresh()

    # ── CRUD ──────────────────────────────────────────────────

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for p in self.app.db["providers"]:
            self.tree.insert("", "end", iid=p["id"], values=(
                p["name"],
                p["fiber_type"],
                f"{p['fixed_dim']:.3f}",
                f"{p['density']:.1f}",
                f"{p['price']:.2f}",
                p["notes"],
            ))

    def _selected_id(self):
        sel = self.tree.selection()
        return sel[0] if sel else None

    def _add(self):
        dlg = ProviderDialog(self, "Nuevo proveedor")
        if dlg.result:
            v = dlg.result
            prov = new_provider(v["name"], v["fiber_type"],
                                v["fixed_dim"], v["density"],
                                v["price"],    v["notes"])
            self.app.db["providers"].append(prov)
            self.app.save()
            self._refresh()

    def _edit(self):
        pid = self._selected_id()
        if not pid:
            messagebox.showinfo("Sin selección", "Selecciona un proveedor primero.", parent=self)
            return
        prov = next(p for p in self.app.db["providers"] if p["id"] == pid)
        dlg  = ProviderDialog(self, "Editar proveedor", prov)
        if dlg.result:
            v = dlg.result
            prov.update({
                "name":       v["name"],
                "fiber_type": v["fiber_type"],
                "fixed_dim":  float(v["fixed_dim"]),
                "density":    float(v["density"]),
                "price":      float(v["price"]),
                "notes":      v["notes"],
            })
            self.app.save()
            self._refresh()

    def _delete(self):
        pid = self._selected_id()
        if not pid:
            messagebox.showinfo("Sin selección", "Selecciona un proveedor primero.", parent=self)
            return
        prov = next(p for p in self.app.db["providers"] if p["id"] == pid)
        # Verificar si está en uso
        en_uso = [c["name"] for c in self.app.db["components"]
                  if c["prov_bulk_id"] == pid or c["prov_aest_id"] == pid]
        if en_uso:
            messagebox.showwarning("Proveedor en uso",
                f"Este proveedor está asignado a:\n  {', '.join(en_uso)}\n"
                "Reasigna esos componentes antes de eliminar.", parent=self)
            return
        if messagebox.askyesno("Confirmar",
                f"¿Eliminar proveedor «{prov['name']}»?", parent=self):
            self.app.db["providers"] = [p for p in self.app.db["providers"] if p["id"] != pid]
            self.app.save()
            self._refresh()
