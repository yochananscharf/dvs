import dv_processing as dv


cameras = dv.io.discoverDevices()

print(cameras)

capture = dv.io.CameraCapture(cameraName=cameras[0])

if capture.isEventStreamAvailable():
    # Get the event stream resolution
    resolution = capture.getEventResolution()

    # Print the event stream capability with resolution value
    print(f"* Events at ({resolution[0]}x{resolution[1]}) resolution")