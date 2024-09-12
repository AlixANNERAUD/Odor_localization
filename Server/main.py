# - Libraries


# - - Time
import time
import datetime
# - - Sensor
from sensor import SensorClass, MinimumMaximumScaler, get_sliding_shift
# - - Mathematical
import numpy
import scipy 
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
# - - Serialization
import json
# - - Logging
import logging
from logging_formatter import LoggingFormatterClass
import traceback

import localization

import configuration

import excitement

from plot import plot_sensors, plot_source_position

from calibration import CalibrationClass

from mqtt import MQTTClientClass

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from sklearn.preprocessing import StandardScaler, MinMaxScaler

from sensor import get_shifts

import localization 

# - - Sensors configuration
# Sensors dictionary
sensors = {}

# - - Configuration file
configuration_path = "configuration.json" # Path to the configuration file

# - - Logging configuration
logging.basicConfig(level=logging.INFO) # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
logging.getLogger().handlers[0].setFormatter(LoggingFormatterClass())   # Set the custom formatter

# - Global variables
first_timestamp = None    # First acquired timestamp
start = datetime.datetime.now() # Start time of the program

# - Functions

def update_sensors(sensor_identifier, sensor_data):
    """
    Update the sensors with the new data

    # Arguments

    - sensor_identifier (str): sensor identifier
    - sensor_data (dict): sensor data
    """

    global first_timestamp

    if sensor_identifier not in sensors:
        logging.warning(f"Sensor {sensor_identifier} not in `sensors` dictionary.")
        return    print(f"Sensor {sensor_identifier} : {sensor_data}")

    for key, sensor in sensor_data.items():
        # We get the timestamp and the value from the sensor
        timestamp = sensor["timestamp"]
        # We use the first timestamp as the reference
        if first_timestamp is None:
            logging.info(f"First timestamp : {timestamp}")
            first_timestamp = timestamp

        # We get the time since the first timestamp
        if timestamp >= first_timestamp:
            timestamp -= first_timestamp
        else:
            logging.warning(f"Ignoring {sensor_identifier} for {key} gaz sensor : timestamp is lower than the first timestamp")
            continue


        value : float = sensor["value"]        

        if value is None:
            continue

        if value == 0:
            logging.debug(f"Ignoring {sensor_identifier} for {key} gaz sensor : value is 0")
            continue
        
        # Try to update the sensor with the new data
        try:
            sensors[sensor_identifier].update(key, value, timestamp)
        except Exception as e:
            logging.error(f"An error occured while updating the sensor {sensor_identifier} : {e}")
            traceback.print_exc()


def get_sensors_position(sensors):
    """
    Get the sensors position

    # Arguments

    - sensors (Dict): sensors

    # Returns

    - numpy.ndarray: sensors position
    """

    positions = numpy.zeros((len(sensors), 2))

    for i, (_, sensor) in enumerate(sensors.items()):
        position = sensor.get_position()
        positions[i, :] = position

    return positions

def get_sensors_value(gaz_sensor_type):
    """
    Get the sensors values

    # Arguments

    - gaz_sensor_type (str): gaz sensor type

    # Returns

    - numpy.ndarray: sensors values for the gaz sensor type for all sensors
    """

    values = numpy.zeros(len(sensors))

    for i, (_, sensor) in enumerate(sensors.items()):
        sensor_values = sensor.get_latest_values(gaz_sensor_type)
        values[i] = sensor_values["value"]

    return values



def localize_source(axes, map_size, sensors_position):
    """
    Localize the source

    # Arguments

    - axes (matplotlib.axes.Axes): axes
    - map_size (Tuple): map size

    # Returns

    - numpy.ndarray: source position
    """

    try:
        sensors_value = get_sensors_value("MQ3")
    except ValueError:
        logging.debug("No values for MQ3")
        return

    if sensors_value.shape[0] < 3:
        print("Not enough sensors")
        return

    if sensors_value.sum() == 0:
        print("No gaz detected")
        return

    #delaunay_position = locate_delaunay(sensors_position, sensors_value)

    #print(f"Source coordinates : {delaunay_position}")

    optimize_position = locate_optimize(sensors_position, sensors_value)

    #print(f"Source coordinates : {optimize_position}")

    plot_source_position(axes, optimize_position, sensors_position, map_size)


def get_map_size(sensors_position):
    """
    Get the map size

    # Arguments

    - sensors_position (numpy.ndarray (N, 2)): sensors position

    # Returns

    - numpy.ndarray (2, 2): map size (min, max)
    """

    # Get the minimum and maximum values
    minimum_x = sensors_position[:, 0].min()
    maximum_x = sensors_position[:, 0].max()

    minimum_y = sensors_position[:, 1].min()
    maximum_y = sensors_position[:, 1].max()

    # Compute the range
    range_x = maximum_x - minimum_x
    range_y = maximum_y - minimum_y

    # Add a 10% margin
    minimum_x -= range_x * 0.1
    maximum_x += range_x * 0.1

    minimum_y -= range_y * 0.1
    maximum_y += range_y * 0.1

    return numpy.array([[minimum_x, minimum_y], [maximum_x, maximum_y]])


def plot_gradient(axes, gaz_sensor_type):
    """
    Plot the sensor growth

    # Argumentsmq3 alcohol sensor library

    - axes ([matplotlib.axes.Axes]): axes
    - gaz_sensor_type (str): gaz sensor type    
    """

    axes[0].clear()
    axes[0].set_title(f"Sensor gradient for {gaz_sensor_type}")
    axes[0].set_xlabel("Time (s)")
    axes[0].set_ylabel("Value")

    if len(axes) > 1:
        axes[1].clear()
        axes[1].set_title(f"Sensor double gradient for {gaz_sensor_type}")
        axes[1].set_xlabel("Time (s)")
        axes[1].set_ylabel("Value")

    butterworth = butter(4, 0.05, output="sos")

    def plot_function(name, sensor, axes):

        data = sensor.get_all_values(gaz_sensors_type=gaz_sensor_type, scale=False)
      

        #data = StandardScaler().fit_transform(data["value"].to_numpy().reshape(-1, 1)).flatten()

        # Ignore empty data
        if data.shape[0] < 16:
            return

        values = sosfiltfilt(butterworth, data["value"].to_numpy())

        #values = StandardScaler().fit_transform(values.reshape(-1, 1)).flatten()

        #scaled_values = MinMaxScaler().fit_transform(data["value"].to_numpy().reshape(-1, 1)).flatten()

        #scaled_values = data["value"].to_numpy()

        gradient = numpy.gradient(values, data["time"].to_numpy()/1000)

        gradient = StandardScaler().fit_transform(gradient.reshape(-1, 1)).flatten()

        #gradient = numpy.convolve(gradient, numpy.ones(10)/10, mode='valid')

        label = f"{name} {sensor.get_position()}"
        
        axes[0].plot(data["time"]/1000, gradient, label=label)
                
        if len(axes) > 1:
            double_gradient = numpy.gradient(gradient, data["time"].to_numpy()/1000)
            
            axes[1].plot(data["time"]/1000, double_gradient, label=label)
          
    iterate_sensors(axes, plot_function)

    if axes[0].get_legend() is not None:
        axes[0].legend()
    if len(axes) > 1 and axes[1].get_legend() is not None:
        axes[1].legend()

def plot_shift(axes, gaz_sensor_type, window_size=50):
    """
    Plot the sensor shift

    # Arguments

    - axes (matplotlib.axes.Axes): axes
    - gaz_sensor_type (str): gaz sensor type    
    """

    axes.clear()
    axes.set_title(f"Sensor shift for {gaz_sensor_type}")
    axes.set_xlabel("Time (s)")
    axes.set_ylabel("Value")

    axes.set_ylim(-500, 500)

    reference_sensor_data = None

    for name, sensor in sensors.items():
        sensor_data = sensor.get_all_values(gaz_sensors_type=gaz_sensor_type, scale=False)

        if sensor_data.shape[0] < window_size:
            continue

        if reference_sensor_data is None:
            reference_sensor_data = sensor.get_all_values(gaz_sensors_type=gaz_sensor_type, scale=False)

        shift_values, shift_time = get_sliding_shift(reference_sensor_data["value"].to_numpy(), reference_sensor_data["time"].to_numpy(), sensor_data["value"].to_numpy(), sensor_data["time"].to_numpy(), window_size=window_size)

        label = f"{name} {sensor.get_position()}"

        axes.plot(shift_time/1000, shift_values, label=label)


        time_difference = numpy.diff(sensor_data["time"].to_numpy())

        print(f"Average time difference for {name} : {(time_difference.mean() / 1000):.2f} s")


    if axes.get_legend() is not None:
        axes.legend()

    #plt.plot(block=False)

   

def main():
    global calibration_mode, sensors

    run = True

    try:
        mqtt_configuration, calibration_configuration, sensors_configuration = configuration.load(configuration_path)

        # - Create the sensors

        for sensor_identifier, sensor_configuration in sensors_configuration.items():
            sensors[sensor_identifier] = SensorClass(sensor_configuration)
        
        # - Create the calibration
        calibration = CalibrationClass(calibration_configuration)

        calibration_state = calibration.state()
        if calibration_state is not None:
            logging.info(f"Calibration enabled, wait for {calibration_state} to calibrate the sensors...")

        # - Create the interface
        window = tk.Tk()    
        window.title("Gaz analyzer")
        window.attributes('-zoomed', True)
        notebook = ttk.Notebook(window)
        notebook.pack(expand=1, fill='both')
    
        # - Create the figure and the canvas        
        # - - Signals
        signals_frame = ttk.Frame(notebook)
        notebook.add(signals_frame, text="Signals")
        signals_figure = matplotlib.figure.Figure(dpi=100)
        signals_subplots = signals_figure.subplots(1, 3)
        signals_canvas = FigureCanvasTkAgg(signals_figure, signals_frame)
    
        # - - Filtering
        filtering_frame = ttk.Frame(notebook)
        notebook.add(filtering_frame, text="Gradient")
        filtering_figure = matplotlib.figure.Figure(dpi=100)
        filtering_canvas = FigureCanvasTkAgg(filtering_figure, filtering_frame)
        filtering_axes = filtering_figure.subplots(1, 2)

        # - - Weight extraction
        weight_extraction_frame = ttk.Frame(notebook)
        notebook.add(weight_extraction_frame, text="Weight extraction")
        weight_extraction_figure = matplotlib.figure.Figure(dpi=100)
        weight_extraction_canvas = FigureCanvasTkAgg(weight_extraction_figure, weight_extraction_frame)
        weight_extraction_subplots = [weight_extraction_figure.subplots(1, 1)]

        # - - Localization
        localization_frame = ttk.Frame(notebook)
        notebook.add(localization_frame, text="Localization")
        localization_figure = matplotlib.figure.Figure(dpi=100)
        localization_canvas = FigureCanvasTkAgg(localization_figure, localization_frame)
        localization_subplots = localization_figure.subplots(1, 1)
        plot_source_position(localization_subplots, sensors, None)

        sensors_position = get_sensors_position(sensors)
        map_size = get_map_size(sensors_position)

        # - Create and start the MQTT client
        mqtt_client = MQTTClientClass(mqtt_configuration, update_sensors)

        mq3_excitement = excitement.ExcitementClass("MQ3")    

        source = None
       
        # - Main loop
        while run:
  
            #localize_source(location_axes, map_size, sensors_position)
            
            mq3_excitement.loop(sensors)
            
            mq3_excited_signals = mq3_excitement.get_excited_signals(sensors)

            if mq3_excitement.is_all_excited(sensors):

                logging.info("All sensors are excited")

                shifts = get_shifts(mq3_excited_signals)

                logging.info(f"Shifts : {shifts}")


                source = localization.trilateration(sensors, shifts)

                print(f"Position : {source}")


            try:
                selected_tab = notebook.select()

                if selected_tab == str(signals_frame):
                    plot_sensors(sensors, signals_subplots[0], "MQ3", "raw_value")
                    plot_sensors(sensors, signals_subplots[1], "MQ3", "resistance")
                    plot_sensors(sensors, signals_subplots[2], "MQ3", "concentration")
                    #plot_sensor_values(mq136_axes, "MQ136")
                    #plot_sensor_spectrum([mq3_spectrum_before_axes, mq3_spectrum_after_axes], "MQ3")
                    #plot_sensors(sensors, filtered_mq3_axes, "MQ3", "concentration", filter=True)
                    #plot_shift(shift_axes, "MQ3")

                    signals_figure.tight_layout()

                    signals_canvas.draw()
                    
                    signals_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

                elif selected_tab == str(filtering_frame):
                    
                    plot_sensors(sensors, filtering_axes[0], "MQ3", "raw_value_filtered")
                    plot_sensors(sensors, filtering_axes[1], "MQ3", "raw_value_filtered_gradient")

                    filtering_figure.tight_layout()
                    filtering_canvas.draw()

                    filtering_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

                elif selected_tab == str(weight_extraction_frame):

                 
                    weight_extraction_subplots[0].set_title("Excited sensors signals")

                    if bool(mq3_excited_signals):

                        weight_extraction_subplots[0].clear()

                        for name, signal in mq3_excited_signals.items():
                            

                            weight_extraction_subplots[0].plot(signal["time"]/1000, signal["value"], label=name)

                        weight_extraction_subplots[0].legend()                    
                    
                    weight_extraction_figure.tight_layout()

                    weight_extraction_canvas.draw()
                    weight_extraction_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

                elif selected_tab == str(localization_frame):

                    if bool(mq3_excited_signals) and source is not None:
                        plot_source_position(localization_subplots, sensors, (source[0], source[1]))

                    localization_figure.tight_layout()
                    localization_canvas.draw()
                    localization_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

                    

            except Exception as e:
                run = False
                
                logging.error(f"An unexpected error occured : {e}")
                traceback.print_exc()
                break  

            window.update()

            calibration_result = calibration.loop(sensors)

            if calibration_result is not None:
                logging.info(f"Calibration results : \n{calibration_result}")


            plt.pause(0.1)

    except Exception as e:
        logging.error(f"An unexpected error occured : {e}")
        traceback.print_exc()
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        run = False

    logging.info("Exiting...")
    mqtt_client.stop()

if __name__ == "__main__":
    main()
