# tab_configuracion.py — Ajustes globales del cálculo
import tkinter as tk
from tkinter import ttk, messagebox
from estilos import C, FONT_BOLD, FONT_SMALL


class SettingsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        # ── Título de sección ──────────────────────────────────
        tk.Label(self, text="Parámetros Globales del Cálculo",
                 bg=C["base"], fg=C["blue"], font=FONT_BOLD
                 ).pack(anchor="w", padx=20, pady=(18, 4))
        tk.Label(self,
                 text="Estos valores se aplican a todos los componentes al calcular.",
                 bg=C["base"], fg=C["sub0"], font=FONT_SMALL
                 ).pack(anchor="w", padx=20, pady=(0, 16))

        s = self.app.db["settings"]

        # ── Frame central ──────────────────────────────────────
        cf = ttk.LabelFrame(self, text="  Ajustes de corte y resina  ", padding=20)
        cf.pack(fill=tk.X, padx=24, pady=8)

        # Overlap
        self._add_row(cf, 0,
            label   = "Overlap (solapamiento) de corte",
            unit    = "metros",
            tooltip = ("Margen adicional que se suma a cada pieza en ambas dimensiones "
                       "para asegurar continuidad estructural en las juntas."),
            var_name = "_v_overlap",
            default  = str(s.get("overlap", 0.03)),
        )

        # Relación resina
        self._add_row(cf, 1,
            label   = "Relación resina / fibra",
            unit    = "g resina por g de fibra",
            tooltip = ("La cantidad de gramos de resina que se usa por cada gramo "
                       "de fibra de carbono. Valor típico: 1.0"),
            var_name = "_v_resin",
            default  = str(s.get("resin_ratio", 1.0)),
        )

        # Gajos por capa en conos
        self._add_row(cf, 2,
            label   = "Gajos por capa (conos/ogivas)",
            unit    = "piezas",
            tooltip = ("Número de gajos en que se divide cada capa al recubrir un cono. "
                       "Más gajos = piezas más pequeñas, menor desperdicio en curvas."),
            var_name = "_v_gores",
            default  = str(s.get("cone_gores", 6)),
        )

        # ── Botón Guardar ──────────────────────────────────────
        ttk.Button(self, text="💾  Guardar configuración",
                   style="Action.TButton",
                   command=self._save
                   ).pack(pady=20)

        # ── Sección de información ─────────────────────────────
        if_frame = ttk.LabelFrame(self, text="  Notas sobre el cálculo  ", padding=16)
        if_frame.pack(fill=tk.X, padx=24, pady=(0, 16))

        notes = (
            "• El rollo de fibra tiene una dimensión fija (configurada por proveedor) "
            "y una longitud n entera (metros) a calcular.\n\n"
            "• El algoritmo prueba ambas orientaciones de la pieza y elige la que "
            "minimiza n (menor desperdicio).\n\n"
            "• Para cilindros: 1 pieza por capa = (perímetro + overlap) × (largo + overlap).\n\n"
            "• Para conos/ogivas: cada capa se divide en gajos.  "
            "El gajo mide (perímetro/gajos + overlap) × (arco + overlap).\n\n"
            "• Para aletas: caja contenedora por aleta = (envergadura + overlap) × (raíz + overlap).\n\n"
            "• Masa de fibra = área_rollo_comprada × densidad_proveedor (g/m²).\n\n"
            "• Resina = masa_fibra × relación."
        )
        tk.Label(if_frame, text=notes,
                 bg=C["base"], fg=C["sub1"],
                 font=FONT_SMALL, justify=tk.LEFT, wraplength=640
                 ).pack(anchor="w")

    # ── Helper para filas de ajuste ────────────────────────────

    def _add_row(self, parent, row, label, unit, tooltip, var_name, default):
        # Etiqueta principal
        tk.Label(parent, text=label, bg=C["base"], fg=C["text"],
                 font=FONT_BOLD, anchor="w", width=36
                 ).grid(row=row, column=0, padx=(0, 12), pady=10, sticky="w")

        # Campo de entrada
        var = tk.StringVar(value=default)
        setattr(self, var_name, var)
        ttk.Entry(parent, textvariable=var, width=12
                  ).grid(row=row, column=1, padx=6, pady=10)

        # Unidad
        tk.Label(parent, text=unit, bg=C["base"], fg=C["sub0"],
                 font=FONT_SMALL
                 ).grid(row=row, column=2, padx=6, pady=10, sticky="w")

        # Tooltip
        tk.Label(parent, text=f"ℹ  {tooltip}",
                 bg=C["base"], fg=C["overlay0"],
                 font=FONT_SMALL, wraplength=380, justify=tk.LEFT
                 ).grid(row=row, column=3, padx=(16, 0), pady=10, sticky="w")

    # ── Guardar ───────────────────────────────────────────────

    def _save(self):
        try:
            ov = float(self._v_overlap.get())
            rr = float(self._v_resin.get())
            gc = int(self._v_gores.get())
        except ValueError:
            messagebox.showwarning("Valor inválido",
                "Overlap y relación deben ser números decimales; "
                "gajos debe ser un entero.", parent=self)
            return

        if ov < 0:
            messagebox.showwarning("Valor inválido",
                "El overlap no puede ser negativo.", parent=self)
            return
        if rr <= 0:
            messagebox.showwarning("Valor inválido",
                "La relación resina/fibra debe ser > 0.", parent=self)
            return
        if gc < 1:
            messagebox.showwarning("Valor inválido",
                "El número de gajos debe ser ≥ 1.", parent=self)
            return

        self.app.db["settings"]["overlap"]     = ov
        self.app.db["settings"]["resin_ratio"] = rr
        self.app.db["settings"]["cone_gores"]  = gc
        self.app.save()
        messagebox.showinfo("Guardado", "Configuración guardada correctamente.", parent=self)

    def refresh(self):
        """Recarga los valores desde la DB (llamar tras cargar proyecto)."""
        s = self.app.db["settings"]
        self._v_overlap.set(str(s.get("overlap",     0.03)))
        self._v_resin.set  (str(s.get("resin_ratio", 1.0 )))
        self._v_gores.set  (str(s.get("cone_gores",  6   )))
