
from scipy.signal import savgol_filter, butter, sosfiltfilt

def plot_sensors(sensors, axes, gaz_sensor_type, y, scale=False, filter=False):
    """
    Plot the sensor values

    # Arguments

    - axes (matplotlib.axes.Axes): axes
    - gaz_sensor_type (str): gaz sensor type
    - scale (bool): center the values    
    """

    title = f"Sensors {y} for {gaz_sensor_type}"

    if scale:
        title += " scaled"

    if filter:
        title += " filtered"

    axes.clear()
    axes.set_title(title)
    axes.set_xlabel("Time (s)")
    axes.set_ylabel("Value")

    if filter:
        butterworth = butter(4, 0.05, output="sos")

    def plot_function(name, sensor, axes):
        label = f"{name} {sensor.get_position()}"

        data = sensor.get_all_values(gaz_sensors_type=gaz_sensor_type)
  
        # Ignore empty data
        if data.shape[0] < 2:
            return

        if filter and data.shape[0] < 16:
            return
        
        values = data[y].to_numpy()

        if filter:
            values = sosfiltfilt(butterworth, values)

        if scale:
            values = StandardScaler().fit_transform(values.reshape(-1, 1)).flatten()

        axes.plot(data["time"]/1000, values, label=label)


    iterate_sensors(sensors, axes, plot_function)

    # - Add the legend if there is one (avoid warning)
    if axes.get_legend() is None:
        axes.legend()

def iterate_sensors(sensors, axes, function):
    for name, sensor in sensors.items():
        function(name, sensor, axes)

def plot_spectrum(sensors, axes, gaz_sensor_type):

    axes[0].clear()
    axes[0].set_title(f"Spectrum for {gaz_sensor_type} before filtering")
    axes[0].set_xlabel("Frequency (Hz)")
    axes[0].set_ylabel("Amplitude")

    # axes[1].clear()
    # axes[1].set_title(f"Spectrum for {gaz_sensor_type} after filtering")
    # axes[1].set_xlabel("Frequency (Hz)")
    # axes[1].set_ylabel("Amplitude")
    
    def plot_function(name, sensor, axes):
        data = sensor.get_all_values(gaz_sensors_type=gaz_sensor_type)

        # Ignore empty data
        if data.shape[0] < 16:
            return None
        
        values = data["value"].to_numpy()

        label = f"{name} {sensor.get_position()}"

        fft_values = numpy.fft.fft(values)
        fft_freq = numpy.fft.fftfreq(len(values), d=(data["time"].to_numpy()[1] - data["time"].to_numpy()[0])/1000)

        fft_values = numpy.fft.fftshift(fft_values)
        fft_freq = numpy.fft.fftshift(fft_freq)

        axes[0].plot(fft_freq, numpy.abs(fft_values), label=label)
    
        butterworth = butter(4, 0.05, output="sos")

        filtered_values = sosfiltfilt(butterworth, values)

        fft_values = numpy.fft.fft(filtered_values)
        fft_freq = numpy.fft.fftfreq(len(filtered_values), d=(data["time"].to_numpy()[1] - data["time"].to_numpy()[0])/1000)

        fft_values = numpy.fft.fftshift(fft_values)
        fft_freq = numpy.fft.fftshift(fft_freq)

        axes[1].plot(fft_freq, numpy.abs(fft_values), label=label)

    iterate_sensors(axes, plot_function)

    if axes[0].get_legend() is not None:
        axes[0].legend()

    if axes[1].get_legend() is not None:
        axes[1].legend()


def plot_source_position(axes, sensors, source_position):
    """
    Plot the source position

    # Arguments

    - axes (matplotlib.axes.Axes): axes
    - map_size (Tuple): map size
    - source_position (numpy.ndarray of shape (2,)): source position
    """

    # - Reset the axes
    axes.clear()
    title = f"Source position "
    if source_position is not None:
        title += f"{source_position}"
    else:
        title += "unknown"

    axes.set_title(title)
    axes.set_xlabel("X")
    axes.set_ylabel("Y")
    axes.set_aspect("equal", adjustable="box")
    axes.grid(True)

    # - Plot the source and the sensors positions   
    if source_position is not None:
        axes.scatter(source_position[0], source_position[1], label="Source", marker="x")

    for name, sensor in sensors.items():
        x, y = sensor.get_position()
        label = f"{name} {sensor.get_position()}"
        axes.scatter(x, y, label=label)

    axes.legend()