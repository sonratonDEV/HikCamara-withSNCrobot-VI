from hik_camera import HikCamera

ips = HikCamera.get_all_ips()
print("All camera IP adresses:", ips)
ip = ips[0]
cam = HikCamera(ip)
with cam:  # 用 with 的上下文的方式来 OpenDevice
   cam["ExposureAuto"] = "Off"  # 配置参数和海康官方 API 一致
   cam["ExposureTime"] = 50000  # 单位 ns
   rgb = cam.robust_get_frame()  # rgb's shape is np.uint8(h, w, 3)
   print("Saveing image to:", cam.save(rgb, ip + ".jpg"))