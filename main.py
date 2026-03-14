#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — Punto de entrada de la Calculadora de Materiales para Cohetes
Ejecutar: python main.py
"""

import tkinter as tk
from tkinter import ttk

from modelos           import load_db, save_db
from estilos           import apply_style, C, FONT_TITLE, FONT_SMALL
from tab_proveedores   import ProvidersTab
from tab_componentes   import ComponentsTab
from tab_configuracion import SettingsTab
from tab_resultados    import ResultsTab
from tab_cortes        import CutsTab


class RocketApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Calculadora de Materiales  v1.0")
        self.geometry("1200x760")
        self.minsize(960, 620)
        self.configure(bg=C["crust"])

        # Icono desde PNG usando ruta relativa al script
        import os
        _here = os.path.dirname(os.path.abspath(__file__))
        _logo_path = os.path.join(_here, "Logo_Orbital.png")
        try:
            from PIL import Image, ImageTk
            img = Image.open(_logo_path).resize((32, 32), Image.LANCZOS)
            self._icon = ImageTk.PhotoImage(img)
            self.iconphoto(True, self._icon)
        except Exception:
            pass

        # Cargar datos
        self.db = load_db()

        # Aplicar estilos globales
        apply_style(self)

        # Construir interfaz
        self._build_header()
        self._build_notebook()
        self._build_statusbar()

    # ─────────────────────────────────────────────────────────
    # CONSTRUCCIÓN UI
    # ─────────────────────────────────────────────────────────

    def _build_header(self):
        hf = tk.Frame(self, bg=C["crust"], height=56)
        hf.pack(fill=tk.X)
        hf.pack_propagate(False)

        tk.Frame(hf, bg=C["blue"], height=2).place(
            relx=0, rely=1.0, anchor="sw", relwidth=1.0)

        # Logo en el header
        import os
        _here = os.path.dirname(os.path.abspath(__file__))
        _logo_path = os.path.join(_here, "Logo_Orbital.png")
        try:
            from PIL import Image, ImageTk
            img = Image.open(_logo_path).resize((36, 36), Image.LANCZOS)
            self._header_logo = ImageTk.PhotoImage(img)
            tk.Label(hf, image=self._header_logo,
                     bg=C["crust"]).pack(side=tk.LEFT, padx=(10, 4), pady=8)
            title_text = "  CALCULADORA DE MATERIALES"
        except Exception:
            title_text = "  CALCULADORA DE MATERIALES"

        tk.Label(hf, text=title_text,
                 bg=C["crust"], fg=C["blue"],
                 font=FONT_TITLE
                 ).pack(side=tk.LEFT, pady=10)

        tk.Label(hf,
                 text="Fibra de Carbono · Resina · Corte Óptimo   ",
                 bg=C["crust"], fg=C["sub0"],
                 font=FONT_SMALL
                 ).pack(side=tk.RIGHT, padx=8, pady=10)

    def _build_notebook(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=(6, 0))

        self.tab_prov = ProvidersTab (self.nb, self)
        self.tab_comp = ComponentsTab(self.nb, self)
        self.tab_conf = SettingsTab  (self.nb, self)
        self.tab_res  = ResultsTab   (self.nb, self)
        self.tab_cuts = CutsTab      (self.nb, self)

        self.nb.add(self.tab_prov, text="  Proveedores  ")
        self.nb.add(self.tab_comp, text="  Componentes  ")
        self.nb.add(self.tab_conf, text="  Configuración  ")
        self.nb.add(self.tab_res,  text="  Resultados  ")
        self.nb.add(self.tab_cuts, text="  Plan de Cortes  ")

    def _build_statusbar(self):
        sb = tk.Frame(self, bg=C["crust"], height=24)
        sb.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Frame(sb, bg=C["surface1"], height=1).pack(fill=tk.X)

        self._status_var = tk.StringVar(value="Listo.")
        tk.Label(sb, textvariable=self._status_var,
                 bg=C["crust"], fg=C["sub0"],
                 font=FONT_SMALL, anchor="w"
                 ).pack(side=tk.LEFT, padx=10)

        # Indicador de archivo de datos
        from modelos import DATA_FILE
        import os
        path = os.path.abspath(DATA_FILE)
        tk.Label(sb, text=f"Datos: {path}  ",
                 bg=C["crust"], fg=C["overlay0"],
                 font=FONT_SMALL, anchor="e"
                 ).pack(side=tk.RIGHT, padx=10)

    # ─────────────────────────────────────────────────────────
    # HELPERS PÚBLICOS 
    # ─────────────────────────────────────────────────────────

    def save(self):
        """Guarda la base de datos y actualiza la barra de estado."""
        save_db(self.db)
        self._status_var.set("✔  Guardado correctamente.")
        self.after(3000, lambda: self._status_var.set("Listo."))

    def get_provider(self, pid):
        """Devuelve el dict del proveedor por id, o None."""
        return next((p for p in self.db["providers"] if p["id"] == pid), None)

    def set_status(self, msg):
        self._status_var.set(msg)


# ─────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = RocketApp()
    app.mainloop()
