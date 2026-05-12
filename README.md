# PlyPlanner v1.0 — Rocketry Material Calculator

PlyPlanner is a specialized engineering tool designed to calculate the necessary carbon fiber and resin for experimental rocket components. It integrates geometric modeling with advanced cutting algorithms to minimize material waste and provide professional documentation for aerospace manufacturing.

## Key Features

* **Multi-Component Geometry Support:** Precise calculation of surface areas and profiles for:
    * **Cylinders:** Standard body tubes and couplers.
    * **Cones & Ogives:** Support for Conical, Tangent Ogive, and Parabolic profiles with numeric arc length calculation.
    * **Trapezoidal Fins:** Advanced fin geometry including sweep angle/distance and thickness offsets.
* **Cutting Optimization:** Implements a **Skyline Packing** (Guillotine BSSF) algorithm to organize pieces on a fixed-width fiber roll, minimizing the length of material required.
* **Global Nesting:** Components sharing the same provider are automatically nested together on the same roll to reduce waste.
* **Interactive Visualizations:** High-fidelity canvas representing the fiber roll with interactive tooltips for each cut piece.
* **Professional Theming:** Built with a custom "Catppuccin Mocha" palette for a modern, high-contrast engineering interface.
* **Data Export:** Generates detailed text reports summarizing geometric areas, resin requirements, and purchase lists.

## Project Structure

* `main.py`: Application entry point and UI architecture.
* `geometria.py`: Mathematical core for geometric areas and cutting algorithms.
* `modelos.py`: Data persistence (JSON) and object definitions.
* `estilos.py`: UI Theming and layout helper functions.
* `tab_*.py`: Modular interface components:
    * `tab_proveedores.py`: Fiber supplier and density management.
    * `tab_componentes.py`: Individual rocket component definitions.
    * `tab_configuracion.py`: Global parameters (overlap, resin ratio).
    * `tab_resultados.py`: Material summaries and report generation.
    * `tab_cortes.py`: Graphical layout of the cutting plan.

## 🛠️ Requirements

* Python 3.x
* `tkinter` (standard library)
* `Pillow` (for logo rendering)

## Usage

1.  **Define Providers:** Add your fiber rolls (width, density, and cost).
2.  **Configure Globals:** Set your preferred overlap margin and resin/fiber mass ratio.
3.  **Add Components:** Input the dimensions and layer requirements for your rocket's body, nose cone, and fins.
4.  **Calculate & Visualize:** Run the optimization to see the total mass required and view the interactive cutting map.
5.  **Export:** Save a text report for the workshop.

---
*Developed for Orbital Dynamics.*
