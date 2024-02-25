# based on code from https://dv-processing.inivation.com/rel_1_7/event_stream_slicing.html

import dv_processing as dv
from PIL import Image, ImageDraw 
from datetime import timedelta
import numpy as np
import streamlit as st

from skimage.transform import hough_circle
image_area = st.empty()
event_area_1 = st.empty()
event_area_2 = st.empty()
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

offset = int(resolution[0]/12)
crop_box = (int(resolution[0]/2), offset, resolution[0], int(resolution[1]/2)+offset)
#crop_box_resize = (crop_box[2], crop_box[3])
#filter = dv.EventRegionFilter(crop_box)
filter_true = dv.EventPolarityFilter(True)
filter_false = dv.EventPolarityFilter(False)

visualizer = dv.visualization.EventVisualizer(camera.getEventResolution(), dv.visualization.colors.white(),
                                              dv.visualization.colors.green(), dv.visualization.colors.red())

visualizer_true = dv.visualization.EventVisualizer(camera.getEventResolution(), dv.visualization.colors.black(),
                                              dv.visualization.colors.green(), dv.visualization.colors.red())
visualizer_false = dv.visualization.EventVisualizer(camera.getEventResolution(), dv.visualization.colors.black(),
                                              dv.visualization.colors.green(), dv.visualization.colors.red())
count = 0

class EyeTracking():
    def __init__(self) -> None:
        self.visualize_image_size = resolution
        self.pupil_width = 100 # in pixels
        self.pupil_start_x = 180
        self.pupil_start_y = 45
        self.draw_blank =  Image.new('RGBA', self.visualize_image_size, (255, 255, 255, 0))#for opacity 
        self.roi_pupil = (self.pupil_start_x, self.pupil_start_y,  self.pupil_start_x+int(1.25*self.pupil_width),self.pupil_start_y+int(1.25*self.pupil_width))
        self.roi = (crop_box[0]+self.pupil_start_x/2, 
                    crop_box[1]+self.pupil_start_y/2, 
                    crop_box[0]+self.pupil_start_x/2+self.roi_pupil[2]/2, 
                    crop_box[1]+self.pupil_start_y/2+self.roi_pupil[3]/2)
        pass

    def draw_image(self, image_raw, roi):
        draw = ImageDraw.Draw(self.draw_blank.copy())   
        draw.rectangle(roi, width=1, outline = (255, 0, 0, 128)) 
        out = Image.alpha_composite(image_raw.convert('RGBA'), self.draw_blank)
        return out
    

    #def filter_events()
    

eye_tracker = EyeTracking()
# Callback method for time based slicing
def display_preview(data):
    # Retrieve frame data using the named method and stream name
    frames = data.getFrames("frames")

    # Retrieve event data
    events = data.getEvents("events")
    #filter for positive polarity events
    filter_true.accept(events)
    filter_false.accept(events)
    filtered_true = filter_true.generateEvents()
    filtered_false = filter_false.generateEvents()
    #filter.accept(events)
    #filtered = filter.generateEvents()
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
    image_draw = eye_tracker.draw_image(preview_image_cropped, eye_tracker.roi_pupil)
    image_area.image(image_draw)

    image_pos = Image.fromarray(visualizer_true.generateImage(filtered_true))
    image_pos = eye_tracker.draw_image(image_pos, eye_tracker.roi)
    image_neg = Image.fromarray(visualizer_false.generateImage(filtered_false))
    # print(count)
    # if count >= 277:
    #     check = True
    event_area_1.image(image_pos)
    event_area_2.image(image_neg)
    #cv.imshow("Preview", visualizer.generateImage(events, latest_image))

    # If escape button is pressed (code 27 is escape key), exit the program cleanly
    #if cv.waitKey(2) == 27:
    #    exit(0)


# Register a job to be performed every 33 milliseconds
slicer.doEveryTimeInterval(timedelta(milliseconds=30), display_preview)

# Continue the loop while both cameras are connected
while camera.isRunning():
    count +=1
    events = camera.getNextEventBatch()
    if events is not None:
        slicer.accept("events", events)

    frame = camera.getNextFrame()
    if frame is not None:
        slicer.accept("frames", [frame])