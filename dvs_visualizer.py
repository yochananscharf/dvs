# based on code from https://dv-processing.inivation.com/rel_1_7/event_stream_slicing.html

import dv_processing as dv
from PIL import Image, ImageDraw 
from datetime import timedelta
import numpy as np
import streamlit as st

from skimage.transform import hough_circle
col1, col2 = st.columns(2)
image_area = col1.empty()
img_plot_area =[]
for i in range(4):
    img_plot_area.append(col2.empty())
# event_area_1 = col2.empty()
# event_area_2 = col2.empty()
# event_area_3 = col2.empty()
# event_area_2 = col2.empty()
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



#crop_box_resize = (crop_box[2], crop_box[3])
#filter = dv.EventRegionFilter(crop_box)


visualizer = dv.visualization.EventVisualizer(camera.getEventResolution(), dv.visualization.colors.white(),
                                              dv.visualization.colors.green(), dv.visualization.colors.red())

visualizer_true = dv.visualization.EventVisualizer(camera.getEventResolution(), dv.visualization.colors.black(),
                                              dv.visualization.colors.green(), dv.visualization.colors.red())
visualizer_false = dv.visualization.EventVisualizer(camera.getEventResolution(), dv.visualization.colors.black(),
                                              dv.visualization.colors.green(), dv.visualization.colors.red())


class EyeTracking():
    def __init__(self) -> None:
        self.visualize_image_size = resolution
        offset = int(resolution[0]/12)
        self.crop_box = (int(resolution[0]/2), offset, resolution[0], int(resolution[1]/2)+offset)
        self.pupil_width = 100 # in pixels
        self.pupil_start_x = 180
        self.pupil_start_y = 45
        self.draw_blank =  Image.new('RGBA', self.visualize_image_size, (255, 255, 255, 0))#for opacity 
        self.roi_pupil = (self.pupil_start_x, self.pupil_start_y,  self.pupil_start_x+int(1.25*self.pupil_width),self.pupil_start_y+int(1.25*self.pupil_width))
        x = int(self.crop_box[0]+self.pupil_start_x/3)
        y = int(self.crop_box[1]+self.pupil_start_y/4)
        w = int(self.pupil_width)
        h = int(self.pupil_width)
        self.roi = (x, 
                    y, 
                    x+w, 
                    y+h)
        self.roi_left = (x, y, x+w//2, y+h)
        self.roi_right = (x+w//2, y, x+w, y+h)
        self.filter_pos = None
        self.filter_neg = None
        self.filter_region_left =    None
        self.filter_region_right =   None
        self.filter_chain_left_pos = None
        self.filter_chain_right_pos =None
        self.filter_chain_left_neg = None
        self.filter_chain_right_neg =None
        self.filtered_counts = []
        self.create_filters()
        # self.filters_dict = {
        #     'left-pos':self.filter_region_left_pos, 
        #     'right-pos':self.filter_region_right_pos,
        #     'left-neg':self.filter_region_left_neg ,
        #     'right-neg':self.filter_region_right_neg,
        # }
        self.count = 0
        pass

    def create_filters(self):
        self.filter_pos = dv.EventPolarityFilter(True)
        self.filter_neg = dv.EventPolarityFilter(False)
        filter_region_left = dv.EventRegionFilter(self.roi_left)
        filter_region_right = dv.EventRegionFilter(self.roi_right)
        filter_chain_left_pos = dv.EventFilterChain()
        filter_chain_left_pos.addFilter(self.filter_pos)
        filter_chain_left_pos.addFilter(filter_region_left)
        filter_chain_right_pos = dv.EventFilterChain()
        filter_chain_right_pos.addFilter(self.filter_pos)
        filter_chain_right_pos.addFilter(filter_region_right)
        filter_chain_left_neg = dv.EventFilterChain()
        filter_chain_left_neg.addFilter(self.filter_neg)
        filter_chain_left_neg.addFilter(filter_region_left)
        filter_chain_right_neg = dv.EventFilterChain()
        filter_chain_right_neg.addFilter(self.filter_neg)
        filter_chain_right_neg.addFilter(filter_region_right)
        self.filters_list = [filter_chain_left_pos, 
                             filter_chain_right_pos,
                             filter_chain_left_neg,
                             filter_chain_right_neg]

    def draw_image(self, image_raw, roi):
        blank = self.draw_blank.copy()
        draw = ImageDraw.Draw(blank)   
        draw.rectangle(roi, width=3, outline = (255, 0, 0, 80)) 
        out = Image.alpha_composite(image_raw.convert('RGBA'), blank)
        return out
    

    def events_stats(self, events):
        num_events = events.size()
        return num_events

    def filter_events_regions(self, events):
        filtered_events_list = []
        for filter_chain in self.filters_list:
            filter_chain.accept(events) 
            filtered_events = filter_chain.generateEvents()
            filtered_events_list.append(filtered_events)
        #filtered_events_list = [left_pos, right_pos, left_neg, right_neg]
        #filtered_list = [pos_left, pos_right, neg_left, neg_right]
        self.filtered_counts = [self.events_stats(evnt) for evnt in filtered_events_list]
        print(self.filtered_counts)
        return filtered_events_list

eye_tracker = EyeTracking()
# Callback method for time based slicing
def display_preview(data):

    # Retrieve frame data using the named method and stream name
    frames = data.getFrames("frames")

    # Retrieve event data
    events = data.getEvents("events")
    #filter for positive polarity events
    eye_tracker.filter_pos.accept(events)
    filtered_pos = eye_tracker.filter_pos.generateEvents()
    eye_tracker.filter_neg.accept(events)
    filtered_neg = eye_tracker.filter_neg.generateEvents()
    filtered_list= eye_tracker.filter_events_regions(events)
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
    preview_image_cropped = preview_image.crop(eye_tracker.crop_box)
    preview_image_cropped = preview_image_cropped.resize(resolution) # back to size of original image
    image_draw = eye_tracker.draw_image(preview_image_cropped, eye_tracker.roi_pupil)
    image_area.image(image_draw)

    image_pos = Image.fromarray(visualizer_true.generateImage(filtered_pos))
    image_pos_cropped = image_pos.crop(eye_tracker.roi_right)
    #image_pos = eye_tracker.draw_image(image_pos)
    image_neg = Image.fromarray(visualizer_false.generateImage(filtered_neg))
    image_neg_cropped = image_neg.crop(eye_tracker.roi_left)
    for j, fltrd in enumerate(filtered_list):
        events_image = Image.fromarray(visualizer_false.generateImage(fltrd))
        if (j%2)==0:
            image_draw = eye_tracker.draw_image(events_image, eye_tracker.roi_left)
        else:
            image_draw = eye_tracker.draw_image(events_image, eye_tracker.roi_right)
        img_plot_area[j].image(image_draw, width=200)
    
    print(eye_tracker.count)
    eye_tracker.count +=1
    
    # if count >= 277:
    #     check = True
    #event_area_1.image(image_pos_cropped)
    #event_area_2.image(image_neg_cropped)

    num_pos = eye_tracker.events_stats(filtered_pos)
    num_neg = eye_tracker.events_stats(filtered_neg)
    if events.size() > 300:
        movement_direction  = ''
        if eye_tracker.filtered_counts[2] >  1.2*eye_tracker.filtered_counts[3]:
            movement_direction = 'left'
        else:
            movement_direction = 'right'
        col1.write('moving {} '.format(movement_direction))
    #     p
    # when moving, there should be a large but similar amount of negative and positive events
    # as the darker pupil moves right: negative events to the right, positive events to the left and vise versa
    #cv.imshow("Preview", visualizer.generateImage(events, latest_image))

    # If escape button is pressed (code 27 is escape key), exit the program cleanly
    #if cv.waitKey(2) == 27:
    #    exit(0)


# Register a job to be performed every 33 milliseconds
slicer.doEveryTimeInterval(timedelta(milliseconds=50), display_preview)

# Continue the loop while both cameras are connected
while camera.isRunning():
    
    events = camera.getNextEventBatch()
    if events is not None:
        slicer.accept("events", events)

    frame = camera.getNextFrame()
    if frame is not None:
        slicer.accept("frames", [frame])