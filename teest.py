import cv2
from hik_camera import HikCamera
import threading
import time
import serial.tools.list_ports
import serial
import time
import os

screen_fol = 'test'

def serial_read(ser):
    global exit_flag, i

    while not exit_flag:
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
        time.sleep(0.1)

        if prev_state is not None and prev_state == 0 and state == 1:
            screen_path = os.path.join(screen_fol, f'{screen_fol}_{i}.png')
            if resized_rgb is not None:
                cv2.imwrite(screen_path, resized_rgb)
                print(f'Screenshot taken: {screen_path}')
                i += 1

        prev_state = state

def show_frame(cam):
    global exit_flag, resized_rgb
    while not exit_flag:
        try:
            rgb = cam.robust_get_frame()
            if rgb is not None:
                height, width, _ = rgb.shape
                new_width = 640
                new_height = int((new_width / width) * height)
                resized_rgb = cv2.resize(rgb, (new_width, new_height))
                cv2.imshow('Hikvision Camera', resized_rgb)

                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    exit_flag = True
                    break
                # elif key == ord('s'):
                #     # Save the image with the IP address as the filename
                #     filename = f"{cam.ip}.png"
                #     cv2.imwrite(filename, resized_rgb)
                #     print(f"Image saved as {filename}")
        except Exception as e:
            print(f"Error during frame retrieval: {str(e)}")
            # Add logging to a file or another output here

    cv2.destroyAllWindows()
    cv2.waitKey(1)


if __name__ == "__main__":
    # Flag to indicate when to stop the video capture
    exit_flag = False
    i=0

    ips = HikCamera.get_all_ips()
    ports = [port.device for port in serial.tools.list_ports.comports()]

    if not ips:
        print("No cameras found on the network.")
    else:
        ip = ips[0]
        cam = HikCamera(ip)

        with cam:  # Using a 'with' statement for OpenDevice
            cam["ExposureAuto"] = "Off"  # Configure parameters similar to Hikvision official API
            cam["ExposureTime"] = 100000  # Exposure time in nanoseconds

            # Start a thread for displaying frames
            display_thread = threading.Thread(target=show_frame, args=(cam,))
            display_thread.start()

            # Keep the main thread for camera setup and handling interruptions
            try:
                while not exit_flag:
                    time.sleep(1)  # Sleep briefly to reduce CPU usage
            except KeyboardInterrupt:
                print("Video capture stopped by the user.")
                exit_flag = True  # Set the exit flag to stop the display thread
            finally:
                # Release the camera and close the OpenCV window
                cv2.destroyAllWindows()
                cv2.waitKey(1)
                # Wait for the display thread to finish before exiting
                display_thread.join()

    if not ports:
        print("No port found on the network.")
        
    else:
        ser = serial.Serial(ports, 115200)
        serial_read(ser)