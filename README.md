# Districts QGIS Plugin

A QGIS plugin for managing, analyzing, and working with district-based spatial data.  
This plugin provides tools to organize, visualize, and interact with administrative or custom district layers directly inside QGIS.

In addition, when configured with **IDA Districts**, the plugin enables advanced dynamic simulation capabilities for energy and district systems.

---

## 🚀 Features

- Manage districts datasets
- Integration with PostgreSQL/PostGIS (if configured)
- Projects Version handling (parent-child relationship)
- Resource handling of pipes, templates for energy plants and customers, etc.
- Pipe laying algorithmn
- Pipe sizing
- Result visualization: Show temporal measurement data or simulation results on map, network reports, path reports, diagrams, etc.

---

## ⚡ Advanced Simulation (IDA Districts Integration)

When connected to **IDA Districts**, the plugin supports advanced dynamic simulation of district energy systems.

IDA Districts https://equa.cloud.xwiki.com/xwiki/bin/view/IDA_Districts/ is a simulation environment for engineers, utilities and research institutions for the planning and analysis of thermal networks and district energy systems. The software enables dynamic, physics-based simulation of buildings, energy sources, networks and their control strategies within one integrated system, creating reliable decision support for planning, dimensioning and operation.

### With IDA Districts integration, this plugin enables:

- Dynamic simulation of district energy systems
- Coupling of spatial district data with physical models
- Analysis of thermal networks and energy flows
- Scenario-based planning and optimization
- Support for engineering decision-making in district development

> Note: IDA Districts must be installed and properly configured for simulation features to be available.

---

## 📦 Installation

### From QGIS Plugin Manager (recommended)

1. Open QGIS
2. Go to **Plugins → Manage and Install Plugins**
3. Search for **Districts Modeler**
4. Click **Install**

> If the plugin is marked as experimental, enable:
> **Settings → Show also experimental plugins**

---

### Manual installation (development)

1. Download or clone this repository
2. Copy the folder into your QGIS plugins directory:

**Windows:**
C:\Users<User>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins


3. Restart QGIS
4. Enable the plugin in the plugin manager

---


## ⚙️ Requirements

- QGIS >= 3.28
- Python 3.x (bundled with QGIS)
- Optional: PostgreSQL/PostGIS (for database features)
- Optional: IDA Districts https://equa.cloud.xwiki.com/xwiki/bin/view/IDA_Districts/ for simulation features

---

## 📦 Releases

- `0.1.10.2` → Experimental preview release
- `1.0.0.0` → Stable release

Each release is tagged and uploaded to the QGIS Plugin Repository separately.
