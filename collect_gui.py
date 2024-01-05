import cv2
from hik_camera import HikCamera
import threading
import time
import os
import serial
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

# Flag to indicate when to stop the video capture
exit_flag = False
screen_fol = '5Jan24_test'
i = 1

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera GUI")

        # Create a label to display the camera feed
        self.label = ttk.Label(root)
        self.label.pack(padx=10, pady=10)

        # Create an exit button
        self.exit_button = ttk.Button(root, text="Exit", command=self.exit_app)
        self.exit_button.pack(pady=10)

        # Save a reference to the camera and serial objects
        self.cam = None
        self.ser = None

        # Initialize class instance variables
        self.prev_state = None
        self.state = None

        # Start a thread for displaying frames
        self.display_thread = threading.Thread(target=self.show_frame)
        self.display_thread.start()

        # Start a thread for reading from the serial port
        self.serial_thread = threading.Thread(target=self.serial_read)
        self.serial_thread.start()

    def set_camera_and_serial(self, cam, ser):
        self.cam = cam
        self.ser = ser

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
        self.root.destroy()

if __name__ == "__main__":
    ips = HikCamera.get_all_ips()
    # Replace 'COM5' with the actual name of your serial port
    ser = serial.Serial('COM5', baudrate=115200, timeout=1)

    if not os.path.exists(screen_fol):
        os.makedirs(screen_fol)
        print(f'Folder created: {screen_fol}')

    if not ips:
        print("No cameras found on the network.")
    else:
        ip = ips[0]
        cam = HikCamera(ip)

        with cam:
            cam["ExposureAuto"] = "Off"
            cam["ExposureTime"] = 50000

            root = tk.Tk()
            app = App(root)
            app.set_camera_and_serial(cam, ser)  # Set camera and serial in the App instance
            root.mainloop()
