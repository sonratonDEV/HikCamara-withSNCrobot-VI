import cv2
from hik_camera import HikCamera
import threading
import time
import os
import serial
import time

# Flag to indicate when to stop the video capture
exit_flag = False
screen_fol = '5Jan24_test'
i = 1
prev_state = None
state = None

def serail_read(ser):
    global state
    try:
        while not exit_flag:
            line = ser.readline().decode('utf-8').strip()
            if line:
                state = int(line)
                print(f"Received data: {line}")
            # time.sleep(0.1)  # Adjust the sleep time based on your requirements
    except KeyboardInterrupt:
        print("Serial reading stopped by the user.")

    finally:
        ser.close()

    return state

def show_frame(cam):
    global exit_flag,i,state,prev_state
    while not exit_flag:
        try:
            rgb = cam.robust_get_frame()
            if rgb is not None:
                height, width, _ = rgb.shape
                new_width = 640
                new_height = int((new_width / width) * height)
                resized_rgb = cv2.resize(rgb, (new_width, new_height))
                cv2.imshow('Hikvision Camera', cv2.cvtColor(resized_rgb, cv2.COLOR_RGB2BGR))
                # cv2.imshow('Hikvision Camera', resized_rgb)

                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    exit_flag = True
                    break
                if prev_state is not None and prev_state == 0 and state == 1:
                    # Save the image with the IP address as the filename
                    # screen_path = os.path.join(screen_fol, f'{screen_fol}_{i}.png')
                    screen_path = os.path.join(screen_fol, f'{screen_fol}_{i}.png')
                    # filename = f"{cam.ip}.png"
                    # cv2.imwrite(screen_path, cv2.cvtColor(resized_rgb, cv2.COLOR_RGB2BGR))
                    cv2.imwrite(screen_path, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
                    print(f"Image saved as {screen_path}")
                    i+=1
                prev_state = state

        except Exception as e:
            print(f"Error during frame retrieval: {str(e)}")
            # Add logging to a file or another output here

    cv2.destroyAllWindows()
    cv2.waitKey(1)


if __name__ == "__main__":
    ips = HikCamera.get_all_ips()
    # Replace 'COM3' with the actual name of your serial port
    ser = serial.Serial('COM5', baudrate=115200, timeout=1)

    if not os.path.exists(screen_fol):
        os.makedirs(screen_fol)
        print(f'Folder created: {screen_fol}')

    if not ips:
        print("No cameras found on the network.")
    else:
        ip = ips[0]
        cam = HikCamera(ip)

        with cam:  # Using a 'with' statement for OpenDevice
            cam["ExposureAuto"] = "Off"  # Configure parameters similar to Hikvision official API
            cam["ExposureTime"] = 50000  # Exposure time in nanoseconds

            # Start a thread for displaying frames
            display_thread = threading.Thread(target=show_frame, args=(cam,))
            display_thread.start()
            serail_thread = threading.Thread(target=serail_read, args=(ser,))
            serail_thread.start()

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
 