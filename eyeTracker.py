import dv_processing as dv
from PIL import Image, ImageDraw 
import numpy as np
#from skimage.transform import hough_circle, hough_circle_peaks
import pandas as pd


#file_path_a  = 'data/dvSave-2024_01_09_18_02_30.aedat4'
#file_path_b  = 'data/dvSave-2024_01_09_18_02_32.aedat4'

class EyeTracking():
    def __init__(self, file_name=None) -> None:
        self.file_name = 'data/'+file_name.name
        self.camera         =None  
        self.slicer=None
        self.resolution=None
        self.visualizer=None
        self.visualizer_true=None
        self.visualizer_fals=None
        self.visualizer_gray=None
        self.data_path = ''
        self.prev_time = -1
        self.create_visualizers()
        self.visualize_image_size = self.resolution
        offset = int(self.resolution[0]/12)
        self.crop_box = (int(self.resolution[0]/2), offset, self.resolution[0], int(self.resolution[1]/2)+offset)
        self.pupil_width = 100 # in pixels
        self.pupil_start_x = 180
        self.pupil_start_y = 45
        self.draw_blank =  Image.new('RGBA', self.visualize_image_size, (255, 255, 255, 0))#for opacity 
        self.roi_pupil = (self.pupil_start_x, self.pupil_start_y,  self.pupil_start_x+int(1.25*self.pupil_width),self.pupil_start_y+int(1.25*self.pupil_width))
        x = int(self.crop_box[0]+self.pupil_start_x/2)
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
        self.filter_region = None
        self.filter_region_left =    None
        self.filter_region_right =   None
        self.filter_chain_left_pos = None
        self.filter_chain_right_pos =None
        self.filter_chain_left_neg = None
        self.filter_chain_right_neg =None
        self.filtered_counts = []
        self.hough_radii = np.arange(85, 120, 5)
        self.create_filters()
        
        # self.filters_dict = {
        #     'left-pos':self.filter_region_left_pos, 
        #     'right-pos':self.filter_region_right_pos,
        #     'left-neg':self.filter_region_left_neg ,
        #     'right-neg':self.filter_region_right_neg,
        # }
        self.count = 0
        self.store = dv.EventStore()
        self.step_t = -1
        self.delta_t = 50
        pass

    def create_visualizers(self):

        self.camera = dv.io.MonoCameraRecording(self.file_name)

        # Initialize a multi-stream slicer
        self.slicer = dv.EventMultiStreamSlicer("events-frames")
        self.slicer.addEventStream("events")
        # Add a frame stream to the slicer
        self.slicer.addFrameStream("frames")

        # Initialize a visualizer for the overlay
        self.resolution = self.camera.getEventResolution()


        self.visualizer = dv.visualization.EventVisualizer(self.camera.getEventResolution(), dv.visualization.colors.white(),
                                                    dv.visualization.colors.green(), dv.visualization.colors.red())

        self.visualizer_true = dv.visualization.EventVisualizer(self.camera.getEventResolution(), dv.visualization.colors.black(),
                                                    dv.visualization.colors.green(), dv.visualization.colors.red())
        self.visualizer_false = dv.visualization.EventVisualizer(self.camera.getEventResolution(), dv.visualization.colors.black(),
                                                    dv.visualization.colors.green(), dv.visualization.colors.red())

        self.visualizer_gray = dv.visualization.EventVisualizer(self.camera.getEventResolution(), dv.visualization.colors.black(),
                                                    dv.visualization.colors.green(), dv.visualization.colors.red())#, dv.visualization.colors.white())

    def create_filters(self):
        self.filter_pos = dv.EventPolarityFilter(True)
        self.filter_neg = dv.EventPolarityFilter(False)
        self.filter_region = dv.EventRegionFilter(self.roi)
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
        #print(self.filtered_counts)
        return filtered_events_list


    # def detect_circle(self, edges):
        
    #     hough_res = hough_circle(edges, self.hough_radii)
    #     accums, cx, cy, radii = hough_circle_peaks(hough_res, self.hough_radii,
    #                                        total_num_peaks=1)
    #     print(accums, cx, cy)
    #     return accums, cx, cy
    
    def events_to_csv(self, events, pth_str):
        highest_t = events.getHighestTime()
        events_list =[ {'x':event.x(),'y': event.y(), 'polarity': event.polarity()} for event in events ]
        df = pd.DataFrame(events_list)
        #path_str = '{}_{}_{}_{}.csv'.format(self.count, str(highest_t), self.delta_t, self.step_t)
        csv_path = pth_str+'.csv'
        df_path = self.data_path/csv_path
        df.to_csv(df_path, index=False)

    def save_frame(self, frame, pth_str):
        frame_path = pth_str+'.jpg'
        save_path = self.data_path/frame_path
        frame.convert('RGB').save(save_path)

    def save_events(self, events, frame=None):#, events, image):
        
        #print(self.count)
        highest_t = events.getHighestTime()
        lowest_t = events.getLowestTime()


        if self.step_t < self.delta_t:
            step_start = highest_t - self.delta_t*1000
            step_stop = highest_t+1
            #delta_start = lowest_t
            #while step_start > delta_start:
            delta_slice = self.store.sliceTime(step_start, step_stop)
            #step_start -= self.step_t*1000
            path_str = '{}_{}_{}_{}'.format(self.count, str(highest_t), self.delta_t, self.step_t)
            self.events_to_csv(delta_slice, path_str)
            self.save_frame(frame, path_str)
        else:

            self.events_to_csv(events)
        