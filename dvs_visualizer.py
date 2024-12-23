# based on code from https://dv-processing.inivation.com/rel_1_7/event_stream_slicing.html

from PIL import Image, ImageDraw 
from datetime import timedelta
import numpy as np
from streamlit import session_state as ss
import streamlit as st
from pathlib import Path
from time import sleep



from eyeTracker import EyeTracking

st.title('Event Based Camera - Eye Tracking')
sidebar = st.sidebar
col1, col2 = st.columns(2)

image_area = col1.empty()
image_area1 = col1.empty()
img_plot_area =[]
for i in range(4):
    img_plot_area.append(col2.empty())
# event_area_1 = col2.empty()
# event_area_2 = col2.empty()
# event_area_3 = col2.empty()
# event_area_2 = col2.empty()



# Callback method for time based slicing
def display_preview(data):
    sleep(0.02)
    #if st.sidebar.button('next-frame',count):
        # Retrieve frame data using the named method and stream name
    frames = data.getFrames("frames")

    # Retrieve event data
    events = data.getEvents("events")
    
    #filter for positive polarity events
    ss.eye_tracker.filter_pos.accept(events)
    filtered_pos = ss.eye_tracker.filter_pos.generateEvents()
    ss.eye_tracker.filter_neg.accept(events)
    filtered_neg = ss.eye_tracker.filter_neg.generateEvents()
    filtered_list= ss.eye_tracker.filter_events_regions(events)
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
            #latest_image_pil = Image.fromarray(frames[-1].image)#.crop(ss.eye_tracker.crop_box)#.convert('RGB')
    else:
        return

    # Generate a preview and show the final image
    preview_image = Image.fromarray(ss.eye_tracker.visualizer.generateImage(events, latest_image))
    
    if ss.eye_center[0] > 0:
        draw = ImageDraw.Draw(preview_image)
        x0, y0 = ss.eye_center[0]-5, ss.eye_center[1]-5
        x1, y1 = ss.eye_center[0]+5, ss.eye_center[1]+5
        bounding_box = (x0, y0, x1, y1)
        draw.ellipse(bounding_box, fill="red")
      
    preview_image_cropped = preview_image.crop(ss.eye_tracker.crop_box)
    preview_image_cropped = preview_image_cropped.resize(ss.eye_tracker.resolution) # back to size of original image
    image_draw = ss.eye_tracker.draw_image(preview_image_cropped, ss.eye_tracker.roi_iris)
    image_area.image(image_draw)
    ss.eye_tracker.filter_region.accept(events)
    events_area = ss.eye_tracker.filter_region.generateEvents()
    
    

    image_array = ss.eye_tracker.visualizer_gray.generateImage(events_area)
    image_events = Image.fromarray(image_array)

    #plot events
    preview_image_cropped = image_events.crop(ss.eye_tracker.crop_box)
    preview_image_cropped = preview_image_cropped.resize(ss.eye_tracker.resolution)
    image_area1.image(preview_image_cropped)

    # plot polarities separate
    image_blue = Image.fromarray(image_array[:,:,2]).crop(ss.eye_tracker.crop_box)
    image_red = Image.fromarray(image_array[:,:,1]).crop(ss.eye_tracker.crop_box)

    #img_plot_area[0].image(image_blue, width=346)
    #img_plot_area[1].image(image_red, width=346)
    #image = img_as_ubyte(image_events)
    #edges = canny(image, sigma=5)
    #c = ndi.center_of_mass(image)
    #r = 8
    #draw_blank =  Image.new('RGBA', ss.eye_tracker.resolution, (255, 255, 255, 0))
    #draw = ImageDraw.Draw(draw_blank)
    #draw.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(255,0,0))
    #out = Image.alpha_composite(image_events.convert('RGBA'), draw_blank)

    # if accums[0] >0.05:
    #     draw_blank =  Image.new('RGBA', resolution, (255, 255, 255, 0))
    #     draw = ImageDraw.Draw(draw_blank)
    #     draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(255,0,0))
    #     out = Image.alpha_composite(image_events.convert('RGBA'), draw_blank)
    #     img_plot_area[0].image(out, width=300)
    #print(ss.eye_tracker.count)

    # save events for future use
    for evnt in events:
        ss.eye_tracker.store.push_back(evnt)
    #if len(events_area) > 0:
    #    ss.eye_tracker.save_events(events_area, latest_image_pil)
    ss.eye_tracker.count +=1
    if True:
        #image_pos = Image.fromarray(ss.eye_tracker.visualizer_true.generateImage(filtered_pos))
        #image_pos_cropped = image_pos.crop(ss.eye_tracker.roi_right)
        #image_pos = eye_tracker.draw_image(image_pos)
        #image_neg = Image.fromarray(ss.eye_tracker.visualizer_false.generateImage(filtered_neg))
        #image_neg_cropped = image_neg.crop(ss.eye_tracker.roi_left)
        # for j, fltrd in enumerate(filtered_list):
        #     events_image = Image.fromarray(ss.eye_tracker.visualizer_false.generateImage(fltrd))
        #     if (j%2)==0:
        #         image_draw = ss.eye_tracker.draw_image(events_image, ss.eye_tracker.roi_left)
        #     else:
        #         image_draw = ss.eye_tracker.draw_image(events_image, ss.eye_tracker.roi_right)
        #     img_plot_area[j].image(image_draw, width=200)
        
        #num_pos = ss.eye_tracker.events_stats(filtered_pos)
        #num_neg = ss.eye_tracker.events_stats(filtered_neg)
        if events.size() > ss.eye_tracker.events_thresh:

            ss.eye_center, inlier_mask =  ss.eye_tracker.filter_center(events_area)
            num_events = len(events_area)
            #events_inliers = [events_area[i] for i in range(num_events) if inlier_mask[i]]
            #image_array = ss.eye_tracker.visualizer_gray.generateImage(events_area)
         


            movement_direction  = ''
            if ss.eye_tracker.filtered_counts[2] >  1.2*ss.eye_tracker.filtered_counts[3]:
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
    
if __name__ == '__main__':
    if 'count' in ss:
        #clicked = sidebar.button('save events', on_click=ss.eye_tracker.save_events(), key=ss.count)
        #if clicked:
        #events = ss.eye_tracker.camera.getNextEventBatch()
        #first_time = events[0].timestamp()
        #time_range_frames = ss.eye_tracker.camera.getFramesTimeRange(14, 23)
        #frame = ss.eye_tracker.camera.getNextFrame()
        #frame_time = frame.timestamp
        # while time_diff > 0:
        #     events = ss.eye_tracker.camera.getNextEventBatch()

        while  ss.eye_tracker.camera.isRunning():
            ss.count += 1

            events = ss.eye_tracker.camera.getNextEventBatch()
            if events is not None:# and (events[0].timestamp() > frame_time):
                
                ss.eye_tracker.slicer.accept("events", events)
            #time_diff = (events[0].timestamp()-frame.timestamp)
            #if time_diff > 0:
            frame = ss.eye_tracker.camera.getNextFrame()
            if frame is not None:
                ss.eye_tracker.slicer.accept("frames", [frame])
            #clicked = False
            #print(ss.count, time_diff)
        #print('ended', ss.count)
    else:
        
        #ss.dvs_file = sidebar.file_uploader('choose file')#file_path_a#
        file_path = "dvSave-2024_01_09_18_02_30.aedat4"
        ss.dvs_file = file_path 
        ss.delta_t = sidebar.slider('Set Time-Window', min_value=10, max_value=100, value=30)
        ss.step_t = sidebar.slider('Set Files Time-Step', min_value=10, max_value=50, value=10)
        if ss.dvs_file is not None:
            ss.count = 0
            ss.eye_center = (-1,-1)
            #data_dir = ss.dvs_file.name.split('.')[0]
          
            #running_dir = Path.cwd()
            #data_path = running_dir/data_dir
            #Path.mkdir(data_path,exist_ok=True)
            ss.eye_tracker = EyeTracking(ss.dvs_file)
            ss.eye_tracker.delta_t = ss.delta_t
            ss.eye_tracker.step_t = ss.step_t
            #ss.eye_tracker.data_path = data_path
            ss.eye_tracker.slicer.doEveryTimeInterval(timedelta(milliseconds=ss.step_t), display_preview)
            
            #ss.eye_tracker.run_events()
            st.rerun()

    
    