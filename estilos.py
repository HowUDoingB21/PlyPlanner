# estilos.py — Paleta Catppuccin Mocha + configuración de ttk.Style
import tkinter as tk
from tkinter import ttk

# ─────────────────────────────────────────────────────────────────
# PALETA
# ─────────────────────────────────────────────────────────────────
C = dict(
    base     = "#1e1e2e",
    crust    = "#11111b",
    mantle   = "#181825",
    surface0 = "#313244",
    surface1 = "#45475a",
    surface2 = "#585b70",
    overlay0 = "#6c7086",
    text     = "#cdd6f4",
    sub1     = "#bac2de",
    sub0     = "#a6adc8",
    blue     = "#89b4fa",
    lavender = "#b4befe",
    mauve    = "#cba6f7",
    green    = "#a6e3a1",
    yellow   = "#f9e2af",
    peach    = "#fab387",
    red      = "#f38ba8",
    teal     = "#94e2d5",
    sky      = "#89dceb",
    sapphire = "#74c7ec",
    maroon   = "#eba0ac",
    flamingo = "#f2cdcd",
)

FONT_BODY   = ("Segoe UI",    10)
FONT_BOLD   = ("Segoe UI",    10, "bold")
FONT_SMALL  = ("Segoe UI",     9)
FONT_TITLE  = ("Consolas",    13, "bold")
FONT_MONO   = ("Consolas",    10)


def apply_style(root):
    s = ttk.Style(root)
    s.theme_use("clam")

    # Base global
    s.configure(".",
        background    = C["base"],
        foreground    = C["text"],
        fieldbackground = C["surface0"],
        borderwidth   = 0,
        font          = FONT_BODY,
        troughcolor   = C["crust"],
        relief        = "flat",
    )

    # Notebook
    s.configure("TNotebook",
        background  = C["crust"],
        borderwidth = 0,
        tabmargins  = [2, 2, 0, 0],
    )
    s.configure("TNotebook.Tab",
        background  = C["surface0"],
        foreground  = C["sub0"],
        padding     = [20, 8],
        font        = FONT_BOLD,
    )
    s.map("TNotebook.Tab",
        background  = [("selected", C["blue"]),  ("active", C["surface1"])],
        foreground  = [("selected", C["crust"]), ("active", C["text"])],
    )

    # Frames y Labels
    s.configure("TFrame",     background = C["base"])
    s.configure("TLabel",     background = C["base"], foreground = C["text"])
    s.configure("TSeparator", background = C["surface1"])

    # LabelFrame
    s.configure("TLabelframe",
        background   = C["base"],
        foreground   = C["blue"],
        bordercolor  = C["surface1"],
        relief       = "groove",
        padding      = 8,
    )
    s.configure("TLabelframe.Label",
        background = C["base"],
        foreground = C["blue"],
        font       = FONT_BOLD,
    )

    # Botones normales
    s.configure("TButton",
        background = C["blue"],
        foreground = C["crust"],
        font       = FONT_BOLD,
        padding    = [12, 5],
        relief     = "flat",
    )
    s.map("TButton",
        background = [("active", C["lavender"]), ("pressed", C["mauve"]),
                      ("disabled", C["surface1"])],
        foreground = [("disabled", C["overlay0"])],
    )

    # Botón peligro (eliminar)
    s.configure("Danger.TButton",
        background = C["red"],
        foreground = C["crust"],
        font       = FONT_BOLD,
        padding    = [12, 5],
    )
    s.map("Danger.TButton",
        background = [("active", C["maroon"]), ("pressed", C["flamingo"])],
    )

    # Botón secundario (neutral)
    s.configure("Secondary.TButton",
        background = C["surface1"],
        foreground = C["text"],
        font       = FONT_BOLD,
        padding    = [12, 5],
    )
    s.map("Secondary.TButton",
        background = [("active", C["surface2"])],
    )

    # Botón acción positiva (calcular / guardar)
    s.configure("Action.TButton",
        background = C["green"],
        foreground = C["crust"],
        font       = FONT_BOLD,
        padding    = [16, 6],
    )
    s.map("Action.TButton",
        background = [("active", C["teal"])],
    )

    # Entry
    s.configure("TEntry",
        fieldbackground = C["surface0"],
        foreground      = C["text"],
        insertcolor     = C["text"],
        padding         = 5,
        relief          = "flat",
    )

    # Combobox
    s.configure("TCombobox",
        fieldbackground  = C["surface0"],
        foreground       = C["text"],
        selectbackground = C["surface1"],
        selectforeground = C["text"],
        padding          = 5,
    )
    s.map("TCombobox",
        fieldbackground  = [("readonly", C["surface0"])],
        selectbackground = [("readonly", C["surface1"])],
        foreground       = [("readonly", C["text"])],
    )

    # Spinbox
    s.configure("TSpinbox",
        fieldbackground = C["surface0"],
        foreground      = C["text"],
        insertcolor     = C["text"],
        arrowcolor      = C["blue"],
        padding         = 5,
    )

    # Treeview
    s.configure("Treeview",
        background       = C["surface0"],
        foreground       = C["text"],
        fieldbackground  = C["surface0"],
        rowheight        = 30,
        borderwidth      = 0,
        relief           = "flat",
    )
    s.configure("Treeview.Heading",
        background  = C["surface1"],
        foreground  = C["blue"],
        font        = FONT_BOLD,
        relief      = "flat",
        padding     = [8, 6],
    )
    s.map("Treeview",
        background  = [("selected", C["blue"])],
        foreground  = [("selected", C["crust"])],
    )

    # Scrollbar
    s.configure("TScrollbar",
        background   = C["surface1"],
        troughcolor  = C["surface0"],
        arrowcolor   = C["sub0"],
        relief       = "flat",
        borderwidth  = 0,
    )

    # Checkbutton
    s.configure("TCheckbutton",
        background   = C["base"],
        foreground   = C["text"],
        indicatorcolor = C["surface0"],
    )
    s.map("TCheckbutton",
        indicatorcolor = [("selected", C["blue"])],
        foreground     = [("active", C["lavender"])],
    )

    # PanedWindow
    s.configure("TPanedwindow", background = C["crust"])

    # Scale
    s.configure("TScale",
        troughcolor = C["surface0"],
        background  = C["blue"],
    )


# ─────────────────────────────────────────────────────────────────
# HELPERS DE LAYOUT
# ─────────────────────────────────────────────────────────────────

def header_bar(parent, title, subtitle=""):
    """Banda superior con título y subtítulo opcionales."""
    bar = tk.Frame(parent, bg=C["crust"], height=52)
    bar.pack(fill=tk.X)
    bar.pack_propagate(False)
    tk.Label(bar, text=f"  {title}",
             bg=C["crust"], fg=C["blue"], font=FONT_TITLE
             ).pack(side=tk.LEFT, pady=8)
    if subtitle:
        tk.Label(bar, text=f"{subtitle}  ",
                 bg=C["crust"], fg=C["sub0"], font=FONT_SMALL
                 ).pack(side=tk.RIGHT, pady=8)
    return bar


def lbl(parent, text, fg=None, bold=False, small=False):
    font = FONT_SMALL if small else (FONT_BOLD if bold else FONT_BODY)
    return ttk.Label(parent, text=text,
                     foreground=fg or C["text"],
                     font=font)


def entry(parent, textvariable, width=14, validate=None):
    kw = dict(textvariable=textvariable, width=width)
    if validate:
        kw["validate"]     = "key"
        kw["validatecommand"] = validate
    return ttk.Entry(parent, **kw)


def tree_with_scroll(parent, columns, headings, widths, height=12):
    """Crea un Treeview con scrollbars horizontal y vertical."""
    frame = ttk.Frame(parent)
    tv    = ttk.Treeview(frame, columns=columns,
                         show="headings", height=height)
    vsb = ttk.Scrollbar(frame, orient="vertical",   command=tv.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tv.xview)
    tv.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    for col, hdr, w in zip(columns, headings, widths):
        tv.heading(col, text=hdr)
        tv.column(col, width=w, minwidth=60, stretch=True)

    tv.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return frame, tv
