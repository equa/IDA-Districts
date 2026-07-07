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

            power.append(p)

            if dt is not None:
                # energy in kWh
                energy_increment = p * float(dt) / 3600000
                energy_cum += energy_increment

            energy.append(energy_cum)

            # optional: debug print
            #print(t, p, dt, energy_cum)

        # --- Plot AFTER the loop ---
        fig, ax = plt.subplots()
        ax2 = ax.twinx()

        # Plot Power
        ax.plot(time, power, label=f'Power ID={id}', color='blue')
        # Plot Energy
        ax2.plot(time, energy, label=f'Energy ID={id}', color='red', linestyle='--')

       # --- X-axis formatting ---
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %H:%M'))
        ax.xaxis.set_minor_locator(mdates.HourLocator(interval=1))

        fig.autofmt_xdate()  # auto rotate & format dates

        # Labels
        ax.set_xlabel("Time")
        ax.set_ylabel("Power (W)")
        ax2.set_ylabel("Energy (kWh)")

        # Legends
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
        
        # 3. Initialize the synchronized timeline bar
        if sync_temporalControler:
            # Note: passed time[0] as start position instead of the full array
            timeline_bar = ax.axvline(x=time[0], color='red', linestyle='-', linewidth=2, label="QGIS Zeit")
            ax.legend()
            
            # Extract the actual canvas directly from the figure
            canvas = fig.canvas
                    
            # 4. Connect the QGIS Temporal Controller Signal
            canvas_obj = iface.mapCanvas()
            temporal_controller = canvas_obj.temporalController()
            
            # Define the lambda function
            bound_update_func = lambda _range=None, c=temporal_controller, t=timeline_bar, cv=canvas: update_timeline(c, t, cv)
            temporal_controller.updateTemporalRange.connect(bound_update_func)
            
            # GARBAGE COLLECTION PROTECTION:
            # We attach the canvas and lambda reference directly to the fig object.
            # As long as the figure window is open, these variables stay alive in memory.
            fig.qgis_canvas_ref = canvas
            fig.bound_update_ref = bound_update_func
            
            # WHERE CLEANUP BELONGS:
            # Connect the cleanup function to the 'destroyed' signal of the Matplotlib Qt window.
            if hasattr(canvas, 'manager') and hasattr(canvas.manager, 'window'):
                plot_window = canvas.manager.window
                plot_window.destroyed.connect(lambda: cleanup_plot(temporal_controller, bound_update_func))

        plt.tight_layout()
        if show_plot:
            plt.show()
        
        if save_plot:
            filename=districtsModelerTempDir()+p_table_name
            fig.savefig(filename, format='svg')
            filenames.append(filename)
            
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
        print(f"Error during timeline update: {e}")

def cleanup_plot(controller, update_func_ref):
    """Disconnects the temporal signal safely when the dialog window is closed."""
    try:
        controller.updateTemporalRange.disconnect(update_func_ref)
    except Exception:
        pass