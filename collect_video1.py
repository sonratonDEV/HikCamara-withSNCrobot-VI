import cv2
from hik_camera import HikCamera

ips = HikCamera.get_all_ips()

if not ips:
    print("No cameras found on the network.")
else:
    ip = ips[0]
    cam = HikCamera(ip)

    with cam:  # Using a 'with' statement for OpenDevice
        cam["ExposureAuto"] = "Off"  # Configure parameters similar to Hikvision official API
        cam["ExposureTime"] = 10000  # Exposure time in nanoseconds

        while True:
            try:
                rgb = cam.robust_get_frame()  # RGB frame shape: np.uint8(h, w, 3)

                if rgb is not None:
                    # Display the frame using OpenCV
                    cv2.imshow('Hikvision Camera', rgb)

                    # Check for the 'q' key to exit the loop
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

            except KeyboardInterrupt:
                print("Video capture stopped by the user.")
                break

    # Release the camera and close the OpenCV window after a short delay
    cv2.destroyAllWindows()
    cv2.waitKey(1)
