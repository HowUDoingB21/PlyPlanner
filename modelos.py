# modelos.py — Carga, guardado y estructura de datos
import json, os

DATA_FILE = "cohete_materiales.json"

FIBER_TYPES = ["engorde", "estetica"]
COMP_TYPES  = ["Cilindro", "Cono / Ogiva", "Aleta"]
CONE_TYPES  = ["Cónico", "Ojiva (tangente)", "Parabólico"]


def _empty_db():
    return {
        "providers": [],
        "components": [],
        "settings": {
            "overlap":     0.03,   # metros
            "resin_ratio": 1.0,    # g resina / g fibra
            "cone_gores":  6,      # gajos por capa en conos
        },
    }


def load_db():
    path = os.path.join(os.path.dirname(__file__), DATA_FILE)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            db = json.load(f)
        # Migración segura: asegura que existan todas las claves
        defaults = _empty_db()
        db.setdefault("providers",  defaults["providers"])
        db.setdefault("components", defaults["components"])
        for k, v in defaults["settings"].items():
            db.setdefault("settings", {})
            db["settings"].setdefault(k, v)
        return db
    return _empty_db()


def save_db(db):
    path = os.path.join(os.path.dirname(__file__), DATA_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


def new_provider(name, fiber_type, fixed_dim, density, price, notes=""):
    """
    fixed_dim : float  — la dimensión fija del rollo (metros), e.g. 2.0
    density   : float  — g/m²
    price     : float  — precio por metro de 'n'
    """
    import uuid
    return {
        "id":         str(uuid.uuid4()),
        "name":       name.strip(),
        "fiber_type": fiber_type,          # "engorde" | "estetica"
        "fixed_dim":  float(fixed_dim),
        "density":    float(density),
        "price":      float(price),
        "notes":      notes.strip(),
    }


def new_component(name, comp_type, layers_bulk, layers_aesthetic,
                  prov_bulk_id, prov_aest_id, params):
    """
    comp_type          : "Cilindro" | "Cono / Ogiva" | "Aleta"
    layers_bulk        : int  — capas de fibra de engorde
    layers_aesthetic   : int  — capas de fibra estética
    prov_bulk_id       : str  — id del proveedor de engorde
    prov_aest_id       : str  — id del proveedor estético
    params             : dict con claves según tipo:
        Cilindro : diameter (m), length (m)
        Cono     : base_diam (m), height (m), cone_type (str)
        Aleta    : root (m), tip (m), span (m), count (int)
    """
    import uuid
    return {
        "id":                str(uuid.uuid4()),
        "name":              name.strip(),
        "comp_type":         comp_type,
        "layers_bulk":       int(layers_bulk),
        "layers_aesthetic":  int(layers_aesthetic),
        "prov_bulk_id":      prov_bulk_id,
        "prov_aest_id":      prov_aest_id,
        "params":            params,
    }
