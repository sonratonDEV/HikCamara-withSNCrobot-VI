import cv2
from hik_camera import HikCamera
import threading
import time
import os
import serial
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk

# Flag to indicate when to stop the video capture
exit_flag = False
screen_fol = '5Jan24_test'
i = 1

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera GUI")

        # Frame 1: IP and Serial Port selection
        frame1 = ttk.Frame(root, padding="10")
        frame1.grid(row=0, column=0)

        ttk.Label(frame1, text="Camera IP: ").grid(row=0, column=0, padx=5, pady=5)
        self.ip_combobox = ttk.Combobox(frame1, state="readonly")
        self.ip_combobox.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame1, text="Serial Port: ").grid(row=1, column=0, padx=5, pady=5)
        self.serial_combobox = ttk.Combobox(frame1, state="readonly")
        self.serial_combobox.grid(row=1, column=1, padx=5, pady=5)

        connect_button = ttk.Button(frame1, text="Connect", command=self.connect_devices)
        connect_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Frame 2: Camera frame display
        frame2 = ttk.Frame(root, padding="10")
        frame2.grid(row=0, column=1)

        # Create a label to display the camera feed
        self.label = ttk.Label(frame2)
        self.label.pack(padx=10, pady=10)

        # Create an exit button
        self.exit_button = ttk.Button(frame2, text="Exit", command=self.exit_app)
        self.exit_button.pack(pady=10)

        # Save a reference to the camera and serial objects
        self.cam = None
        self.ser = None

        # Initialize class instance variables
        self.prev_state = None
        self.state = None

        # Initialize IP and Serial Comboboxes
        self.update_ip_combobox()
        self.update_serial_combobox()

    def update_ip_combobox(self):
        ips = HikCamera.get_all_ips()
        self.ip_combobox["values"] = ips
        if ips:
            self.ip_combobox.set(ips[0])

    def update_serial_combobox(self):
        # Update serial port combobox with available ports
        available_ports = [f"COM{i + 1}" for i in range(16)]
        self.serial_combobox["values"] = available_ports
        if available_ports:
            self.serial_combobox.set(available_ports[0])

    def connect_devices(self):
        try:
            selected_ip = self.ip_combobox.get()
            selected_serial_port = self.serial_combobox.get()

            if not selected_ip or not selected_serial_port:
                messagebox.showerror("Error", "Please select both Camera IP and Serial Port.")
                return

            # Disconnect existing devices
            if self.cam:
                self.cam.__exit__(None, None, None)
            if self.ser:
                self.ser.close()

            # Connect to the selected camera
            self.cam = HikCamera(selected_ip)
            self.cam.__enter__()

            # Connect to the selected serial port
            self.ser = serial.Serial(selected_serial_port, baudrate=115200, timeout=1)

        except Exception as e:
            messagebox.showerror("Error", f"Error connecting devices: {str(e)}")

    def show_frame(self):
        while not exit_flag:
            try:
                rgb = self.cam.robust_get_frame()
                if rgb is not None:
                    height, width, _ = rgb.shape
                    new_width = 640
                    new_height = int((new_width / width) * height)
                    resized_rgb = cv2.resize(rgb, (new_width, new_height))
                    image = Image.fromarray(cv2.cvtColor(resized_rgb, cv2.COLOR_BGR2RGB))
                    photo = ImageTk.PhotoImage(image=image)
                    self.label.config(image=photo)
                    self.label.image = photo

                    if self.prev_state is not None and self.prev_state == 0 and self.state == 1:
                        screen_path = os.path.join(screen_fol, f'{screen_fol}_{i}.png')
                        cv2.imwrite(screen_path, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
                        print(f"Image saved as {screen_path}")
                        i += 1
                    self.prev_state = self.state

            except Exception as e:
                print(f"Error during frame retrieval: {str(e)}")

            time.sleep(0.1)  # Adjust the sleep time based on your requirements

    def serial_read(self):
        while not exit_flag:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    self.state = int(line)
            except serial.SerialException as se:
                print(f"Serial reading error: {str(se)}")
            except KeyboardInterrupt:
                print("Serial reading stopped by the user.")
            finally:
                self.ser.close()

    def exit_app(self):
        global exit_flag
        exit_flag = True
        if self.cam:
            self.cam.__exit__(None, None, None)
        if self.ser:
            self.ser.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
