import cv2
from hik_camera import HikCamera
import os
import threading
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import serial
import serial.tools.list_ports
import time

screen_fol = 'screen'
i = 1
prev_state = None
frame = None
cam = None
ser = None
state = None
line = '0'
image_matrix = [[1, 10, 11, 20, 21, 30, 31, 40],
                [2, 9, 12, 19, 22, 29, 32, 39],
                [3, 8, 13, 18, 23, 28, 33, 38],
                [4, 7, 14, 17, 24, 27, 34, 37],
                [5, 6, 15, 16, 25, 26, 35, 36]]

# Create a GUI window
root = tk.Tk()
root.geometry('1200x550')
root.title("Camera and Serial Monitor")

# Create a frame to contain the components
frame1 = ttk.Frame(root)
frame1.grid(row=0, column=0, rowspan=6)

frame2 = ttk.Frame(root)
frame2.grid(row=0, column=1)

# Function to get a list of available COM ports
def get_available_camera_ports():
    try:
        ports = [HikCamera.get_all_ips()]
        return ports
    except Exception as e:
        print(f'Error getting available camera ports: {e}')
        return []
    
# Function to update the COM port dropdown menu
def update_camera_ports():
    camera_ports = get_available_camera_ports()
    camera_dropdown['values'] = camera_ports
    if camera_ports:
        camera_dropdown.current(0)  # Set the default selection to the first available port
    else:
        camera_dropdown.set('')  # Clear the selection if no ports are available
        print("No COM ports available.")

# Function to get a list of available COM ports
def get_available_com_ports():
    try:
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports
    except Exception as e:
        print(f'Error getting available COM ports: {e}')
        return []

# Function to update the COM port dropdown menu
def update_com_ports():
    com_ports = get_available_com_ports()
    com_dropdown['values'] = com_ports
    if com_ports:
        com_dropdown.current(0)  # Set the default selection to the first available port
    else:
        com_dropdown.set('')  # Clear the selection if no ports are available
        print("No COM ports available.")

# Function to set the folder path
def set_folder_path():
    folder_path = folder_name_var.get()
    if folder_path:
        global screen_fol, i
        screen_fol = folder_path
        i = 1
        print(f"Folder path set to: {screen_fol}")

        # Clear the existing labels
        for widget in frame2.winfo_children():
            widget.destroy()

        # Create the folder if it doesn't exist
        if not os.path.exists(screen_fol):
            os.makedirs(screen_fol)
            print(f"Folder created: {screen_fol}")

# Create a frame for comport connection within frame1
camera_frame = ttk.Frame(frame1)
camera_frame.grid(row=0, column=0, columnspan=3)

# Dropdown menu for selecting camera port
camera_label = ttk.Label(camera_frame, text="Select camera Port:")
camera_label.grid(row=1, column=0)

camera_ports = get_available_camera_ports()  # Get available camera ports initially
selected_camara_port = tk.StringVar()
camera_dropdown = ttk.Combobox(camera_frame, textvariable=selected_camara_port, values=camera_ports)
camera_dropdown.grid(row=1, column=1)
camera_refresh = ttk.Button(camera_frame, text='Refresh camera port', command=update_camera_ports)
camera_refresh.grid(row=1, column=2)

# Create a frame for comport connection within frame1
comport_frame = ttk.Frame(frame1)
comport_frame.grid(row=5, column=0, columnspan=3)

# Create a frame for folder input and refresh button within frame1
folder_frame = ttk.Frame(frame1)
folder_frame.grid(row=6, column=0, columnspan=2)

# Entry widget to input the folder name
folder_entry_label = ttk.Label(folder_frame, text="Enter Folder Name:")
folder_entry_label.grid(row=0, column=0)
folder_name_var = tk.StringVar()
folder_entry = ttk.Entry(folder_frame, textvariable=folder_name_var)
folder_entry.grid(row=0, column=1)

# Button to set the folder path
set_folder_button = ttk.Button(folder_frame, text="Set Folder Path", command=set_folder_path)
set_folder_button.grid(row=0, column=2)

# Function to display the captured screenshots in the grid
def display_screenshots():
    # global image_matrix
    for row, image_row in enumerate(image_matrix):
        for col, image_num in enumerate(image_row):
            image_path = os.path.join(screen_fol, f'{screen_fol}_{image_num}.png')
            if os.path.exists(image_path):
                img = Image.open(image_path)
                img = img.resize((100, 100), Image.LANCZOS)  # Resize the image with anti-aliasing
                img = ImageTk.PhotoImage(img)  # Convert to a format that tkinter can display

                # Create a label to display the image
                label = ttk.Label(frame2, image=img)
                label.grid(row=row, column=col)
                label.image = img  # Keep a reference to the image to prevent it from being garbage collectedee

# Function to update serial connection state
def update_serial_state():
    if ser.is_open:
        serial_label.config(text="Serial: Connected", foreground="green")
    else:
        serial_label.config(text="Serial: Not Connected", foreground="red")

# Function to update camera connection state
def update_camera_state():
    if cam.is_open:
        camera_label.config(text="Camera: Connected", foreground="green")
    else:
        camera_label.config(text="Camera: Not Connected", foreground="red")

# Function to start the camera connection
def start_camera():
    ip = selected_camara_port.get()
    global cam

    cam = HikCamera()
    if cam.OpenDevice(ip):
        update_camera_state()
    else:
        print(f'Fail to connect camera at {ip}')
        pass

    # Use the entered folder name or default to 'screen' if not provided
    folder_name = folder_name_var.get() or 'screen'
    folder_path = os.path.join(os.getcwd(), folder_name)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    with cam:  # Using a 'with' statement for OpenDevice
        cam["ExposureAuto"] = "Off"  # Configure parameters similar to Hikvision official API
        cam["ExposureTime"] = 100000  # Exposure time in nanoseconds

        # Start a thread for camera_thread frames
        camera_thread = threading.Thread(target=lambda: camera_thread_function(folder_path, cam))  # Pass 'cam' as an argument
        camera_thread.start()

# Function to stop the camera connection
def stop_camera():
    global cam
    if cam.is_open():
        cam.release_device()
        update_camera_state()

# Function to start the serial connection
def start_serial():
    global ser
    selected_port = selected_com_port.get()
    ser = serial.Serial(selected_port, 115200)  # Open the selected serial port
    if ser.is_open:
        update_serial_state()
    serial_thread = threading.Thread(target=serial_thread_function)
    serial_thread.start()

# Function to stop the serial connection
def stop_serial():
    global ser
    if ser.is_open:
        ser.close()
        update_serial_state()

# Button to start the camera connection within frame1
start_camera_button = ttk.Button(camera_frame, text="Start Camera", command=start_camera)
start_camera_button.grid(row=2, column=0)

# Button to stop the camera connection within frame1
stop_camera_button = ttk.Button(camera_frame, text="Stop Camera", command=stop_camera)
stop_camera_button.grid(row=2, column=1)

# Label to display camera connection state within frame1
camera_label = ttk.Label(camera_frame, text="Camera: Not Connected", foreground="red")
camera_label.grid(row=2, column=2)

# Dropdown menu for selecting COM port
com_label = ttk.Label(comport_frame, text="Select COM Port:")
com_label.grid(row=0, column=0)

com_ports = get_available_com_ports()  # Get available COM ports initially
selected_com_port = tk.StringVar()
com_dropdown = ttk.Combobox(comport_frame, textvariable=selected_com_port, values=com_ports)
com_dropdown.grid(row=0, column=1)
com_refresh = ttk.Button(comport_frame, text='Refresh port', command=update_com_ports)
com_refresh.grid(row=0, column=2)

# Button to start the serial connection within frame1
start_serial_button = ttk.Button(comport_frame, text="Start Serial", command=start_serial)
start_serial_button.grid(row=2, column=0)

# Button to stop the serial connection within frame1
stop_serial_button = ttk.Button(comport_frame, text="Stop Serial", command=stop_serial)
stop_serial_button.grid(row=2, column=1)

# Label to display serial connection state within frame1
serial_label = ttk.Label(comport_frame, text="Serial: Not Connected", foreground="red")
serial_label.grid(row=2, column=2)

# Your camera and serial thread functions go here
def camera_thread_function(folder_path, cam):
    # global exit_flag
    while not camera_stopped.is_set():
        # Use try-except to catch exceptions during frame retrieval
        try:
            # Use robust_get_frame without a timeout
            rgb = cam.robust_get_frame()
            if rgb is not None:
                # Resize the image to fit the window
                height, width, _ = rgb.shape
                new_width = 640  # Adjust the width as needed
                new_height = int((new_width / width) * height)
                resized_rgb = cv2.resize(rgb, (new_width, new_height))
                cv2.imshow('Hikvision Camera', resized_rgb)
        except Exception as e:
            print(f"Error during frame retrieval: {str(e)}")
            # Add logging to a file or another output here

        if cv2.waitKey(30) & 0xFF == ord('q'):
            stop_camera()
            stop_serial()
            break

def serial_thread_function():
    global prev_state, i, frame
    while not serial_stopped.is_set():
        line = ser.readline().decode('utf-8').strip()
        if not line:
            # Handle empty string gracefully
            continue

        try:
            state = int(line)
        except ValueError:
            # Handle invalid data received from the serial port
            print(f"Invalid data received from the serial port: {line}")
            continue

        print(f"Received state: {state}")

        if prev_state is not None and prev_state == 0 and state == 1:
            screen_path = os.path.join(screen_fol, f'{screen_fol}_{i}.png')
            if frame is not None:
                cv2.imwrite(screen_path, frame)
                print(f'Screenshot taken: {screen_path}')
                i += 1
                root.after(500, display_screenshots)

        prev_state = state

camera_stopped = threading.Event()  # Event to signal camera thread to stop
serial_stopped = threading.Event()  # Event to signal serial thread to stop

# After the Tkinter main loop, release resources and close threads
# root.protocol("WM_DELETE_WINDOW", stop_program)
root.mainloop()  # Start the GUI main loop
