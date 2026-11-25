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
- Economic evaluation of a simulated version in the network report: investment of pipes, trench and pumps, pump energy, heat and cold losses, maintenance, net present value and annuity, with cost data in the pipe catalog and named economic scenarios (prices per year, hourly electricity profile, price curves of the supply temperature, trench costs per surface; example values from public sources)
- Cost optimization: pipe sizes with the least net present value over the amortization period (investment, trench, pumps, maintenance, pump energy, heat and cold losses, comfort penalties), one pipe size per line and iteration, each iteration checked by simulation; the needed outputs are switched on at the start, every iteration is shown on the map (diameters, changed lines, customers with a deficit)
- Network built in stages: the cost optimization sizes the pipes for several stage versions (child versions with more customers, plants and lines, each from its start year); a line is sized for all stages it exists in, the operating costs of a stage count in its years and an investment from the start of the stage it first appears in
- Pipe catalogue of the templates: isoplus rigid single and twin pipes (DRE/DRD) and flexible pipes (isoflex, isocu, isopex heating and sanitary including twins, isoclima), with product data per pipe series (system type, temperature limits, allowed axial stress, pressure ratings over operating time and temperature) and the minimum bend radius per pipe
- Statics model (first step of the pipe statics): built from the lines, junctions and pipe bundles of a version with bends found from the vertices (small-angle kinks, prefabricated and elastic bends, runs of small kinks merged into one elastic bend), dimensions and cover per pipe or twin pipe, and point and section overrides drawn on the map that survive a regeneration of the topology; shown as a layer group with a report
- Sensitivity analysis of the cost optimization: interest, period, prices and escalation per cost group, cost factors of pipes, trench and pumps, penalty prices and limits varied by − / + values (one at a time, all combinations or a Latin-hypercube sample); per variant an estimate from the best iteration of the last run (re-evaluation and one cost-model step, no simulation) or a full optimization into its own child versions; parallel coordinates, tornado chart or rank correlations, the lines whose pipe changes and their robustness on the map, in the dialog and the report; an estimate can be validated: "Validate…" simulates the step of the chosen variants once each in kept child versions `<version>_v<k>` and compares the simulated NPV, comfort penalties and limits with the forecast (table and plot of forecast against simulation)
- Ground collectors (first step; not yet usable in the plugin): the model of horizontal ground heat exchangers (ring trench collectors lying or standing, flat meanders, bare pipes) for a Modelica component of IDA Districts: a generic geometry per trench meter with presets, a 2D reference of the ground with freezing and a surface energy balance (air, sun, sky as IDA's climate model computes them), an RC network of six nodes fitted automatically to it in the frequency domain, the start state of the ground after years of operation, and validation cases on a real climate year (`districts/test/data/ground_collector_cases/`, regenerated with `python -m districts.test.make_ground_collector_cases`)
- Representative periods: three weeks chosen from the climate file (the coldest or warmest week and two weeks for the best coverage of the year) are simulated in parallel and weighted to the year, as a faster alternative to an annual simulation in the cost optimization
- Electric power of the network pumps (found automatically in the plant and customer templates, editable per project in `networkPumps.json`) and room setpoints as simulation results
- Scenario-based planning and optimization
- Energy use of the plants and customers (boilers, heat pumps; found automatically, carrier electricity, fuel or purchased heat, editable per project in `energyUse.json`) as simulation results; with them the net present value contains the energy costs per carrier of the plants and, for the whole system, of the customers, and a pipe loss is priced with the most expensive plant running in that hour
- Support for engineering decision-making in district development

> Note: IDA Districts must be installed and properly configured for simulation features to be available.

---

## 🤖 AI connection (MCP)

An AI assistant such as Claude Desktop or Claude Code can work with the open Districts Modeler through the Model Context
Protocol (MCP). Its tools only read: they show the state of the project and version, layers, features and a map image,
run model checks (topology, heights, pipe data, template detection, IDA run errors, substations ΔT and Δp, line
velocity and pressure loss, plants that never run, and the data a cost optimization needs: mapping expressions
evaluated for every customer and plant, pipe costs, economic scenario, supply/return pairs, required loads, climate
file, pump and energy-use lists), give the key figures of a version as in the network report
(heat, losses, pump energy, energy and costs per carrier, NPV) and compare two versions, report the workflow state
and read the IDA Districts wiki. No tool changes data or starts a simulation.

1. In QGIS, menu **Plugins → Districts Modeler → MCP configuration ...**: the dialog shows, with the paths of this
   computer, the command for Claude Code (`claude mcp add districts --scope user -- ...`, run once in a terminal; the
   dialog says whether the `claude` command is installed), the entry for the Chat tab of Claude Desktop (Settings →
   Developer → Edit Config, under `mcpServers`), each with a copy button, and "Write .mcp.json ..." for the Code tab of
   Claude Desktop and the VS Code extension (they have no `claude` command and read `.mcp.json` in the folder they
   open; the file holds paths of one computer and is not committed). The server is started with the Python of QGIS
   (`python.exe`), not with `python-qgis.bat`.
2. Switch on **Plugins → Districts Modeler → AI connection (MCP)** (off at every QGIS start). The connection listens on
   127.0.0.1 only, with a token renewed at every start (`districts_mcp.json` in the QGIS profile folder).
3. Ask the assistant, e.g. "check the loaded version" or "compare base1 with base1_sizing".

**AI assistant tab.** The same tools are available in the Districts Modeler itself: tab **AI assistant** (seventh tab,
detachable). It calls the Claude API through the `anthropic` Python package, which the tab installs on request
("Install AI support", `pip install --user` with the QGIS Python). The Anthropic API key goes into the Districts
Modeler settings (stored encrypted in the QGIS authentication database; without it `ANTHROPIC_API_KEY` is used); the
Claude API is billed per use, separately from a Claude subscription. The tab works only in projects where the AI
assistant is allowed (button "Permission ...", stored in the project database for everyone, with tools that can be
switched off, e.g. the map image); the MCP connection follows the same permission. Model (Claude Opus 5.5 by default,
Sonnet 5.5, Haiku 5.5) and effort can be chosen; the tab shows the estimated cost per answer and session and asks before
continuing above a limit per session (2 USD). "Export" writes a conversation as HTML; otherwise it ends with QGIS.

The server (`districts/mcp/server.py`) runs with the Python of QGIS and needs no further installation; the wiki needs
internet access, the other tools do not.

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
