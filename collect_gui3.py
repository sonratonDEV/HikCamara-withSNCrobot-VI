import cv2
from hik_camera import HikCamera
import threading
import time
import os
import serial
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import serial.tools.list_ports

# Flag to indicate when to stop the video capture
exit_flag = False
i = 1

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera GUI")

        # Frame 1: IP and Serial Port selection
        frame1 = ttk.Frame(root, padding="10")
        frame1.grid(row=0, column=0)

        ttk.Label(frame1, text="Camera IP: ").grid(row=1, column=0, padx=5, pady=5)
        self.ip_combobox = ttk.Combobox(frame1, state="readonly")
        self.ip_combobox.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame1, text="Serial Port: ").grid(row=2, column=0, padx=5, pady=5)
        self.serial_combobox = ttk.Combobox(frame1, state="readonly")
        self.serial_combobox.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame1, text="File Name: ").grid(row=0, column=0, padx=5, pady=5)
        self.file_name_entry = ttk.Entry(frame1)
        self.file_name_entry.grid(row=0, column=1, padx=5, pady=5)

        # Button to create a folder
        create_folder_button = ttk.Button(frame1, text="Set Folder", command=self.create_folder)
        create_folder_button.grid(row=0, column=2, columnspan=1, pady=10)

        refresh_button = ttk.Button(frame1, text="Refresh port", command=self.refresh_devices)
        refresh_button.grid(row=1, column=2, columnspan=1, pady=10)

        connect_button = ttk.Button(frame1, text="Connect", command=self.connect_devices)
        connect_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Frame 2: Camera frame display
        frame2 = ttk.Frame(root, padding="10")
        frame2.grid(row=1, column=0)

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
        self.refresh_devices()

        # Create thread variables
        self.show_frame_thread = None
        self.serial_read_thread = None


    def refresh_devices(self):
        self.update_ip_combobox()
        self.update_serial_combobox()

    def update_ip_combobox(self):
        ips = HikCamera.get_all_ips()
        self.ip_combobox["values"] = ips
        if ips:
            self.ip_combobox.set(ips[0])

    def update_serial_combobox(self):
        available_ports = [port.device for port in serial.tools.list_ports.comports()]
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

            if self.cam:
                self.cam.__exit__(None, None, None)
            if self.ser:
                self.ser.close()

            self.cam = HikCamera(selected_ip)
            self.cam.__enter__()

            self.ser = serial.Serial(selected_serial_port, baudrate=115200, timeout=None)

            folder_name = self.file_name_entry.get()
            if folder_name:
                self.show_frame_thread = threading.Thread(target=self.show_frame, args=(folder_name,), daemon=True)
                self.show_frame_thread.start()

                # Show saved images on frame3
                self.show_saved_images(folder_name)

            self.serial_read_thread = threading.Thread(target=self.serial_read, daemon=True)
            self.serial_read_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Error connecting devices: {str(e)}")

    def show_saved_images(self, folder_path):
        frame3 = ttk.Frame(self.root, padding="10")
        frame3.grid(row=0, column=1, rowspan=2)

        image_matrix = [[30, 21, 20, 11, 10, 1],
                        [29, 22, 19, 12, 9, 2],
                        [28, 23, 18, 13, 8, 3],
                        [27, 24, 17, 14, 7, 4],
                        [26, 25, 16, 15, 6, 5]]

        for i in range(len(image_matrix)):
            for j in range(len(image_matrix[0])):
                image_index = image_matrix[i][j]
                image_path = os.path.join(folder_path, f'{folder_path}_{image_index}.png')

                if os.path.isfile(image_path):
                    img = cv2.imread(image_path)
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(img)
                    img = img.resize((100, 100), Image.LANCZOS)
                    img = ImageTk.PhotoImage(img)

                    label = ttk.Label(frame3, image=img)
                    label.grid(row=i, column=j, padx=5, pady=5)

                    label.image = img
                else:
                    print(f"Image not found: {image_path}")

    def create_folder(self):
        try:
            folder_name = self.file_name_entry.get()
            if not folder_name:
                messagebox.showerror("Error", "Please enter a folder name.")
                return

            folder_path = os.path.join(os.getcwd(), folder_name)
            os.makedirs(folder_path, exist_ok=True)
            messagebox.showinfo("Success", f"Folder '{folder_name}' created successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Error creating folder: {str(e)}")

    def show_frame(self, folder_name):
        global i
        while not exit_flag:
            try:
                rgb = self.cam.robust_get_frame()
                if rgb is not None:
                    height, width, _ = rgb.shape
                    new_width = 320
                    new_height = int((new_width / width) * height)
                    resized_rgb = cv2.resize(rgb, (new_width, new_height))
                    image = Image.fromarray(cv2.cvtColor(resized_rgb, cv2.COLOR_BGR2RGB))
                    photo = ImageTk.PhotoImage(image=image)
                    self.label.config(image=photo)
                    self.label.image = photo

                    if self.prev_state is not None and self.prev_state == 0 and self.state == 1:
                        screen_path = os.path.join(folder_name, f'{folder_name}_{i}.png')
                        cv2.imwrite(screen_path, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
                        print(f"Image saved as {screen_path}")
                        i += 1
                    self.prev_state = self.state

            except Exception as e:
                print(f"Error during frame retrieval: {str(e)}")

            time.sleep(0.1)

    def serial_read(self):
        try:
            while not exit_flag:
                try:
                    if self.ser.is_open:
                        line = self.ser.readline().decode('utf-8').strip()
                        if line:
                            self.state = int(line)
                except serial.SerialException as se:
                    print(f"Serial reading error: {str(se)}")
                except Exception as e:
                    print(f"Unexpected error during serial reading: {str(e)}")
                except KeyboardInterrupt:
                    print("Serial reading stopped by the user.")
                finally:
                    pass
        except Exception as e:
            print(f"Error in serial_read: {str(e)}")

    def exit_app(self):
        global exit_flag
        exit_flag = True
        if self.cam:
            self.cam.__exit__(None, None, None)
        if self.ser:
            self.ser.close()

        if self.show_frame_thread:
            self.show_frame_thread.join()
        if self.serial_read_thread:
            self.serial_read_thread.join()

        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry('1200x550')
    app = App(root)
    root.mainloop()
