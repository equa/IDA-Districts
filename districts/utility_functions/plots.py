import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import datetime

import tempfile
from qgis.utils import iface

from .topology import *
from .files import *

import xml.etree.ElementTree as ET

def get_svg_size(svg_file):
    tree = ET.parse(svg_file) # nosec B314
    root = tree.getroot()
    width = root.get('width')
    height = root.get('height')

    # Convert units if necessary (assuming px → mm, 1px = 0.264583 mm)
    def parse_size(value):
        if value is None:
            return None
        if value.endswith('px'):
            return float(value[:-2]) * 0.264583
        elif value.endswith('mm'):
            return float(value[:-2])
        elif value.endswith('pt'):
            return float(value[:-2]) * 0.352778  # points to mm
        else:  # assume px
            return float(value) * 0.264583

    return parse_size(width), parse_size(height)
    
def matplotlibPowerPlots(plugin_dir,config,cur,id,feature_type='customer',show_plot=True,save_plot=False,sync_temporalControler=False):
    #print(feature_type)
    power_connections=getFeatureConnbundletypeSequences(id,config,cur,feature_type=feature_type)
    #print(power_connections)
    p_table_names=[feature_type+ '_s_power$'+str(i['conn_bundle_type_id'])+'_'+str(i['sequence']) for i in power_connections]
    filenames=[]
    scaling=0.001
    for p_table_name in p_table_names:
        #try:
        #print(p_table_name)
        sql = """
SELECT
    time,
    "$power" AS power,
    EXTRACT(EPOCH FROM (time - LAG(time) OVER (ORDER BY time))) AS dt
FROM "{}"."{}"
WHERE fid={}
ORDER BY time;
        """.format(config['versionName'], p_table_name, id) # nosec B608               
        #print(sql)
        cur.execute(sql)
        data=cur.fetchall()
        
        time = []
        power = []
        energy = []

        energy_cum = 0

        for entry in data:
            t = entry['time']
            p = float(entry['power'])
            dt = entry['dt']  # seconds (None for first row)

            # Keep datetime objects directly
            if isinstance(t, str):
                t = datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
            time.append(t)

            if dt is not None:
                # energy in kWh
                energy_increment = p * float(dt) / 3600000
                energy_cum += energy_increment
                
            power.append(p*scaling)

            energy.append(energy_cum)

            # optional: debug print
            #print(t, p, dt, energy_cum)

        # --- Plot AFTER the loop ---
        fig, ax = plt.subplots()
        ax2 = ax.twinx()

        import numpy as np
        time_arr = np.array(time)

        # Plot Power auf der primären Achse (zorder=2)
        ax.plot(time_arr, power, label=f"{tr('@default','power')} ID={id}", color='blue', zorder=2)
        
        # Plot Energy auf der sekundären Achse (zorder=2)
        ax2.plot(time_arr, energy, label=f"{tr('@default','energy')} ID={id}", color='red', linestyle='--', zorder=2)

        #--- X-axis formatting ---
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %H:%M'))
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))

        # Grenzen explizit einfrieren, um Verzerren beim Zeitregler-Update zu verhindern
        ax.set_xlim(time_arr[0], time_arr[-1])
        fig.autofmt_xdate()  # auto rotate & format dates

        # Labels
        ax.set_ylabel(tr('@default','power')+', kW')
        ax2.set_ylabel(tr('@default','energy')+', kWh')

        # WICHTIG: Die Steuerung der Hintergrund-Reihenfolge (Layer-Schnittstelle)
        # Macht den Hintergrund von ax2 transparent, damit man ax (und die rote Linie) darunter sieht
        ax.set_zorder(1)
        ax2.set_zorder(2)
        ax.patch.set_visible(False)  # Verhindert, dass ax die Achse ax2 komplett überdeckt

        # 3. Initialize the synchronized timeline bar
        if sync_temporalControler:
            # WICHTIG: Wir zeichnen die Linie auf ax2 (die oberste Achse) mit zorder=5, 
            # damit sie absolut unblockiert ganz oben liegt.
            timeline_bar = ax2.axvline(x=time_arr[0], color='red', linestyle='-', linewidth=2, label="QGIS "+tr('@default','time'), zorder=5)
            
            # Extract the actual canvas directly from the figure
            canvas = fig.canvas
                    
            # 4. Connect the QGIS Temporal Controller Signal
            canvas_obj = iface.mapCanvas()
            temporal_controller = canvas_obj.temporalController()
            
            # Define the lambda function
            bound_update_func = lambda _range=None, c=temporal_controller, t=timeline_bar, cv=canvas: update_timeline(c, t, cv)
            temporal_controller.updateTemporalRange.connect(bound_update_func)
            
            # GARBAGE COLLECTION PROTECTION:
            fig.qgis_canvas_ref = canvas
            fig.bound_update_ref = bound_update_func
            
            # WHERE CLEANUP BELONGS:
            try:
                if hasattr(canvas, 'manager') and hasattr(canvas.manager, 'window'):
                    plot_window = canvas.manager.window
                    plot_window.destroyed.connect(lambda: cleanup_plot(temporal_controller, bound_update_func))
            except:
                pass

        # JETZT ERST: Die Legenden werden exakt einmal am Ende aufgerufen.
        # ax-Legende (Power) oben links
        ax.legend(loc='upper left')
        
        # ax2-Legende (Energy + ggf. QGIS Zeit-Linie) oben rechts
        ax2.legend(loc='upper right')


        plt.tight_layout()
        if show_plot:
            plt.show()
        
        if save_plot:
            filename=districtsModelerTempDir()+p_table_name
            fig.savefig(filename, format='svg')
            filenames.append(filename)
            
    return filenames

def matplotlibBalancePlots(plugin_dir,config,cur,networks,balance_type='heatbalance',show_plot=True,save_plot=False,sync_temporalControler=False):
    scaling=0.001 if balance_type=='heatbalance' else 1
    for network in networks:
        print(network)
        table_name=balance_type+'_{}_s'.format(network)
        columns=getDBColumnInfo(cur,config['versionName'],table_name).keys()
        var_colmns=list(columns)[2:]
        
        sql = """SELECT {}
FROM "{}"."{}"
ORDER BY time;
        """.format(','.join(['"'+col+'"' for col in columns]),config['versionName'], table_name, ) # nosec B608               
        print(sql)
        cur.execute(sql)
        data=cur.fetchall()
        
        time = []
        var_data={col: [] for col in var_colmns}

        for entry in data:
            print(entry)
            t = entry['time']

            # Keep datetime objects directly
            if isinstance(t, str):
                t = datetime.strptime(t, "%Y-%m-%dT%H:%M:%S")
            time.append(t)
            
            for col in var_colmns:
                # Direkt zu float konvertieren, um Decimal-Probleme bei Matplotlib zu vermeiden
                val = entry[col]
                var_data[col].append(float(val)*scaling if val is not None else 0.0)

        # --- Plot AFTER the loop ---
        fig, ax = plt.subplots()

        import numpy as np
        time_arr = np.array(time)
        
        # Baselines für die positive und negative Stapelung initialisieren
        pos_cum = np.zeros(len(time_arr))
        neg_cum = np.zeros(len(time_arr))
        
        # Jede Variable separat als Bilanz-Fläche plotten
        for label, values in var_data.items():
            vals_arr = np.array(values)
            
            # Splitten in positive und negative Anteile
            pos_part = np.where(vals_arr > 0, vals_arr, 0.0)
            neg_part = np.where(vals_arr < 0, vals_arr, 0.0)
            
            has_pos = np.any(pos_part)
            
            # Farb-Zuweisung sichern, damit Positiv/Negativ dieselbe Farbe haben (zorder=2)
            poly = None
            if has_pos:
                next_pos = pos_cum + pos_part
                poly = ax.fill_between(time_arr, pos_cum, next_pos, label=label, zorder=2)
                pos_cum = next_pos
                
            if np.any(neg_part):
                next_neg = neg_cum + neg_part
                plot_label = None if has_pos else label
                # Falls bereits eine Positiv-Fläche existiert, nutzen wir deren Farbe
                color = poly.get_facecolor()[0] if poly else None
                ax.fill_between(time_arr, neg_cum, next_neg, label=plot_label, color=color, zorder=2)
                neg_cum = next_neg

        # Eine schwarze Nulllinie als visueller Anker (zorder=2.5)
        ax.axhline(0, color='black', linestyle='--', linewidth=1, zorder=2.5)

       # --- X-axis formatting ---
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %H:%M'))
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))

        fig.autofmt_xdate()  # auto rotate & format dates

        # Labels
        ax.set_ylabel(tr('@default','power')+', kW' if balance_type=='heatbalance' else tr('@default','massflow')+', kg/s')

        # Initialisiert die Standard-Legende ohne die rote Linie
        ax.legend(loc='upper left')
        
        # 3. Initialize the synchronized timeline bar
        if sync_temporalControler:
            # WICHTIG: x=time[0] statt dem ganzen Array, zorder=5 setzt die Linie ganz nach oben über die Flächen!
            timeline_bar = ax.axvline(x=time[0], color='red', linestyle='-', linewidth=2, label="QGIS "+tr('@default','time'), zorder=5)
            
            # Legende aktualisieren, um die rote Linie einzuschließen
            ax.legend(loc='upper left')
            
            # Extract the actual canvas directly from the figure
            canvas = fig.canvas
                    
            # 4. Connect the QGIS Temporal Controller Signal
            canvas_obj = iface.mapCanvas()
            temporal_controller = canvas_obj.temporalController()
            
            # Define the lambda function
            bound_update_func = lambda _range=None, c=temporal_controller, t=timeline_bar, cv=canvas: update_timeline_balance(c, t, cv)
            temporal_controller.updateTemporalRange.connect(bound_update_func)
            
            # GARBAGE COLLECTION PROTECTION:
            fig.qgis_canvas_ref = canvas
            fig.bound_update_ref = bound_update_func
            
            # WHERE CLEANUP BELONGS:
            try:
                if hasattr(canvas, 'manager') and hasattr(canvas.manager, 'window'):
                    plot_window = canvas.manager.window
                    plot_window.destroyed.connect(lambda: cleanup_plot(temporal_controller, bound_update_func))
            except:
                pass

        plt.tight_layout()
        if show_plot:
            plt.show()
        
        if save_plot:
            filename=districtsModelerTempDir()+table_name
            fig.savefig(filename, format='svg')
            filenames.append(filename)
        else:
            filenames=[]
            
    return filenames
    
def update_timeline(controller, timeline_bar, canvas):
    """Triggered whenever the time changes in the QGIS Temporal Controller."""
    try:
        # Calculate the datetime range using the current frame number
        frame_number = controller.currentFrameNumber()
        time_range = controller.dateTimeRangeForFrameNumber(frame_number)
        qgs_datetime = time_range.begin()
        
        # Convert to a standard Python datetime object (removing timezone data)
        current_time = qgs_datetime.toPyDateTime().replace(tzinfo=None)
        
        # Update the X-position of the vertical line
        timeline_bar.set_xdata([current_time, current_time])
        
        # Redraw the plot canvas efficiently
        canvas.draw_idle()
    except Exception as e:
        #print(f"Error during timeline update: {e}")
        pass

def update_timeline_balance(controller, timeline_bar, canvas):
    """Triggered whenever the time changes in the QGIS Temporal Controller."""
    try:
        # Calculate the datetime range using the current frame number
        frame_number = controller.currentFrameNumber()
        time_range = controller.dateTimeRangeForFrameNumber(frame_number)
        qgs_datetime = time_range.begin()
        
        # Convert to a standard Python datetime object (removing timezone data)
        current_time = qgs_datetime.toPyDateTime().replace(tzinfo=None)
        
        # WICHTIG: Konvertierung in das numerische Datumsformat von Matplotlib
        import matplotlib.dates as mdates
        mpl_time = mdates.date2num(current_time)
        
        # Grenzen der X-Achse sichern, um automatisches Rescaling zu verhindern
        ax = timeline_bar.axes
        xlim = ax.get_xlim()
        
        # Update mit dem numerischen Wert durchführen
        timeline_bar.set_xdata([mpl_time, mpl_time])
        
        # Grenzen starr beibehalten
        ax.set_xlim(xlim)
        
        # Redraw the plot canvas efficiently
        canvas.draw_idle()
    except Exception as e:
        # print(f"Error during timeline update: {e}")
        pass

def cleanup_plot(controller, update_func_ref):
    """Disconnects the temporal signal safely when the dialog window is closed."""
    try:
        controller.updateTemporalRange.disconnect(update_func_ref)
    except Exception:
        pass