import dv_processing as dv
from PIL import Image
from datetime import timedelta
import numpy as np
import streamlit as st

from skimage.transform import hough_circle
image_area = st.empty()
# Open the camera, just use first detected DAVIS camera
#camera = dv.io.CameraCapture("", dv.io.CameraCapture.CameraType.DAVIS)
# Open a file
file_path_a  = 'data/dvSave-2024_01_09_18_02_30.aedat4'
file_path_b  = 'data/dvSave-2024_01_09_18_02_32.aedat4'



camera = dv.io.MonoCameraRecording(file_path_a)

# Initialize a multi-stream slicer
slicer = dv.EventMultiStreamSlicer("events")

# Add a frame stream to the slicer
slicer.addFrameStream("frames")

# Initialize a visualizer for the overlay
resolution = camera.getEventResolution()

crop_box = (int(resolution[0]/2), 0, resolution[0], int(resolution[1]/2))

visualizer = dv.visualization.EventVisualizer(camera.getEventResolution(), dv.visualization.colors.white(),
                                              dv.visualization.colors.green(), dv.visualization.colors.red())



# Callback method for time based slicing
def display_preview(data):
    # Retrieve frame data using the named method and stream name
    frames = data.getFrames("frames")

    # Retrieve event data
    events = data.getEvents("events")

    # Retrieve and color convert the latest frame of retrieved frames
    latest_image = None
    if len(frames) > 0:
        if len(frames[-1].image.shape) == 3:
            # We already have colored image, no conversion
            latest_image = frames[-1].image
        else:
            # Image is grayscale, convert to color (BGR image)
            #latest_image_pil = Image.fromarray(frames[-1].image).convert('RGB')
            latest_image = np.tile(frames[-1].image[:, :, None], [1, 1, 3])
    else:
        return

    # Generate a preview and show the final image
    preview_image = Image.fromarray(visualizer.generateImage(events, latest_image))
    preview_image_cropped = preview_image.crop(crop_box)
    preview_image_cropped = preview_image_cropped.resize(resolution) # back to size of original image
    image_area.image(preview_image_cropped)
    #cv.imshow("Preview", visualizer.generateImage(events, latest_image))

    # If escape button is pressed (code 27 is escape key), exit the program cleanly
    #if cv.waitKey(2) == 27:
    #    exit(0)


# Register a job to be performed every 33 milliseconds
slicer.doEveryTimeInterval(timedelta(milliseconds=30), display_preview)

# Continue the loop while both cameras are connected
while camera.isRunning():
    events = camera.getNextEventBatch()
    if events is not None:
        slicer.accept("events", events)

    frame = camera.getNextFrame()
    if frame is not None:
        slicer.accept("frames", [frame])