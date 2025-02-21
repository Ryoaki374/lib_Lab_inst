import time
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx.errors import DaqError
import datetime as dt
import numpy as np


def create_csv(save_path, column_names):
    """
    Creates a CSV file with a filename that includes the current timestamp.
    Writes a header line to the CSV file.
    Parameters:
        save_path (str): The directory where the file will be saved.
    Returns:
        str: The full path of the created CSV file.
    """
    # Generate a filename using the current date and time
    filename = (
        save_path + dt.datetime.now().strftime("%Y%m%d%H%M%S") + "_NIDAQ_NI9215.csv"
    )
    print("Generated filename:", filename)
    # Write the header to the CSV file
    try:
        with open(filename, mode="a") as f:
            print(*column_names, sep=", ", file=f)
    except Exception as e:
        print("An error occurred while creating the file:", e)
    return filename


def DataAcquisition(save_path, filename, columnname, sampling_rate=512):
    """
    Continuously reads voltage data from NI-DAQ channels and appends the data to a CSV file.
    The function performs the following tasks:
      1. Sets up the NI-DAQ task to read voltage data from four channels:
         - "cDAQ1Mod2/ai0": Current Phase A
         - "cDAQ1Mod2/ai1": Current Phase B
         - "cDAQ1Mod1/ai0": Voltage Phase A
         - "cDAQ1Mod1/ai2": Voltage Phase B
      2. Configures the sampling clock for continuous acquisition.
      3. Reads a block of data (number of samples per channel equals sampling_rate).
      4. Creates a time vector for the current block, offset by a counter.
      5. Writes the data (with time information) to a CSV file.
         If the file is not found, it creates a new CSV file with a header.
    Parameters:
        save_path (str): Directory where the CSV file will be saved.
        filename (str): The initial file path for saving data.
        columnname (list): List of column names for the CSV header.
        sampling_rate (int): Number of samples to acquire per second.
    """
    # Record the start time (not used in the current version but can be useful for future extensions)
    start_time = time.perf_counter()
    # Counter for time offset for each block (assumes each block represents 1 second)
    CTime = 0
    while True:
        # Try to read data from NI-DAQ channels
        try:
            # Create a new NI-DAQ task for each block of acquisition
            with nidaqmx.Task() as task:
                # Add analog input channels for current and voltage measurements
                task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai0")  # Current Phase A
                task.ai_channels.add_ai_voltage_chan("cDAQ1Mod2/ai1")  # Current Phase B
                task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai0")  # Voltage Phase A
                task.ai_channels.add_ai_voltage_chan("cDAQ1Mod1/ai2")  # Voltage Phase B
                # Configure the sampling clock for continuous acquisition at the specified sampling_rate
                task.timing.cfg_samp_clk_timing(
                    rate=sampling_rate,
                    sample_mode=AcquisitionType.CONTINUOUS,
                    samps_per_chan=int(sampling_rate),
                )
                # Read data from each channel (number_of_samples_per_channel equals sampling_rate)
                data = np.array(task.read(number_of_samples_per_channel=sampling_rate))
        except DaqError as e:
            print(f"Reading Error: {e}")
            continue  # Skip the rest of the loop iteration if a reading error occurs
        # Generate a time vector for the current block of data, offset by CTime
        timedata = np.linspace(0.001 + CTime, 1 + CTime, sampling_rate)
        # Stack the time data and the acquired data vertically to create an array for CSV output
        arr = np.vstack([timedata, data])
        # Debug prints: output the first and last time values of the current block
        # print("First time value:", arr.T[0])
        # print("Last time value:", arr.T[-1])
        # Try to append the data block to the CSV file
        try:
            with open(filename, mode="a") as f:
                np.savetxt(f, arr.T, delimiter=",")
        except FileNotFoundError:
            # If file is not found, create a new file with a header
            print("FileNotFoundError occurred... Creating a new file.")
            # Generate a new filename with the current timestamp
            filename = save_path + dt.datetime.now().strftime("%Y%m%d%H%M%S") + ".csv"
            with open(filename, mode="a") as f:
                # Write the header line and then the data block
                print(*columnname, sep=", ", file=f)
                print(*arr, sep=", ", file=f)
        # Increment the time offset counter by 1 second for the next block
        CTime += 1
