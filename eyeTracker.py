import dv_processing as dv
from PIL import Image, ImageDraw 
import numpy as np
#from skimage.transform import hough_circle, hough_circle_peaks
import pandas as pd
import random
from scipy.optimize import curve_fit

#file_path_a  = 'data/dvSave-2024_01_09_18_02_30.aedat4'
#file_path_b  = 'data/dvSave-2024_01_09_18_02_32.aedat4'

class EyeTracking():
    def __init__(self, file_name=None) -> None:
        self.file_name = 'data/'+file_name#.name
        self.camera         =None  
        self.slicer=None
        self.resolution=None
        self.visualizer=None
        self.visualizer_true=None
        self.visualizer_fals=None
        self.visualizer_gray=None
        self.data_path = ''
        self.prev_time = -1
        self.events_thresh = 200
        self.create_visualizers()
        self.visualize_image_size = self.resolution
        offset = int(self.resolution[0]/12)
        self.crop_box = (int(self.resolution[0]/2), offset, self.resolution[0], int(self.resolution[1]/2)+offset)
        self.iris_width = 110 # in pixels (iris is the colorfull circle that is larger and encircles the pupil)
        self.pupil_width = 40 # in pixels
        self.iris_start_x = 160
        self.iris_start_y = 40
        self.draw_blank =  Image.new('RGBA', self.visualize_image_size, (255, 255, 255, 0))#for opacity 
        self.roi_iris = (self.iris_start_x, self.iris_start_y,  self.iris_start_x+int(1.5*self.iris_width),self.iris_start_y+int(1.5*self.iris_width))
        x = int(self.crop_box[0]+self.iris_start_x/2)
        y = int(self.crop_box[1]+self.iris_start_y/4)
        w = int(self.iris_width/2)
        h = int(self.iris_width/2)
        self.roi = (x, 
                    y, 
                    x+w, 
                    y+h)
        self.roi_left = (x, y, x+w//2, y+h)
        self.roi_right = (x+w//2, y, x+w, y+h)
        self.previous_center = (-1,-1)
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
        self.slicer = dv.EventMultiStreamSlicer("events")

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

    def plot_points(self, points, selected_points = None):
            
        frame = np.zeros((200, 600), dtype=np.float16)  # Create empty frame
        for p in points: # Accumulate events
            frame[p[1], p[0]] += 0.5
        if selected_points:
            for p in selected_points: # Accumulate events
                frame[int(p[1]), int(p[0])] += 1
        # Normalize to 0-255 for display
        frame = (frame * (255.0)).astype(np.uint8)
        img = Image.fromarray(frame)
        return img


    def filter_center(self, events):
        events_array = np.array([events.coordinates()])[0]
        polarities = np.array([events.polarities()])[0]
        new_center, inlier_mask = self.fit_circle_with_radius_filter(points=events_array,polarities=polarities, expected_radius=self.pupil_width//2, radius_tolerance=self.pupil_width//5, min_inner_radius=self.pupil_width//2.5)
        return new_center, inlier_mask
        

    def fit_ellipse(self, x, y):
        """

        Fit the coefficients a,b,c,d,e,f, representing an ellipse described by
        the formula F(x,y) = ax^2 + bxy + cy^2 + dx + ey + f = 0 to the provided
        arrays of data points x=[x1, x2, ..., xn] and y=[y1, y2, ..., yn].

        Based on the algorithm of Halir and Flusser, "Numerically stable direct
        least squares fitting of ellipses'.


        """

        D1 = np.vstack([x**2, x*y, y**2]).T
        D2 = np.vstack([x, y, np.ones(len(x))]).T
        S1 = D1.T @ D1
        S2 = D1.T @ D2
        S3 = D2.T @ D2
        T = -np.linalg.inv(S3) @ S2.T
        M = S1 + S2 @ T
        C = np.array(((0, 0, 2), (0, -1, 0), (2, 0, 0)), dtype=float)
        M = np.linalg.inv(C) @ M
        eigval, eigvec = np.linalg.eig(M)
        con = 4 * eigvec[0]* eigvec[2] - eigvec[1]**2
        ak = eigvec[:, np.nonzero(con > 0)[0]]
        return np.concatenate((ak, T @ ak)).ravel()

    def cart_to_pol(self, coeffs):
        """

        Convert the cartesian conic coefficients, (a, b, c, d, e, f), to the
        ellipse parameters, where F(x, y) = ax^2 + bxy + cy^2 + dx + ey + f = 0.
        The returned parameters are x0, y0, ap, bp, e, phi, where (x0, y0) is the
        ellipse centre; (ap, bp) are the semi-major and semi-minor axes,
        respectively; e is the eccentricity; and phi is the rotation of the semi-
        major axis from the x-axis.

        """

        # We use the formulas from https://mathworld.wolfram.com/Ellipse.html
        # which assumes a cartesian form ax^2 + 2bxy + cy^2 + 2dx + 2fy + g = 0.
        # Therefore, rename and scale b, d and f appropriately.
        a = coeffs[0]
        b = coeffs[1] / 2
        c = coeffs[2]
        d = coeffs[3] / 2
        f = coeffs[4] / 2
        g = coeffs[5]

        den = b**2 - a*c
        if den > 0:
            raise ValueError('coeffs do not represent an ellipse: b^2 - 4ac must'
                            ' be negative!')

        # The location of the ellipse centre.
        x0, y0 = (c*d - b*f) / den, (a*f - b*d) / den

        num = 2 * (a*f**2 + c*d**2 + g*b**2 - 2*b*d*f - a*c*g)
        fac = np.sqrt((a - c)**2 + 4*b**2)
        # The semi-major and semi-minor axis lengths (these are not sorted).
        ap = np.sqrt(num / den / (fac - a - c))
        bp = np.sqrt(num / den / (-fac - a - c))

        # Sort the semi-major and semi-minor axis lengths but keep track of
        # the original relative magnitudes of width and height.
        width_gt_height = True
        if ap < bp:
            width_gt_height = False
            ap, bp = bp, ap

        # The eccentricity.
        r = (bp/ap)**2
        if r > 1:
            r = 1/r
        e = np.sqrt(1 - r)

        # The angle of anticlockwise rotation of the major-axis from x-axis.
        if b == 0:
            phi = 0 if a < c else np.pi/2
        else:
            phi = np.arctan((2.*b) / (a - c)) / 2
            if a > c:
                phi += np.pi/2
        if not width_gt_height:
            # Ensure that phi is the angle to rotate to the semi-major axis.
            phi += np.pi/2
        phi = phi % np.pi

        return x0, y0, ap, bp, e, phi


    def find_circle_center_from_three_points(self, p1, p2, p3, radius, radius_thresh):
        """
        Finds the center of a circle passing through three given points.

        Args:
            p1: First point (x1, y1) as a tuple or list.
            p2: Second point (x2, y2) as a tuple or list.
            p3: Third point (x3, y3) as a tuple or list.

        Returns:
            A tuple (x, y) representing the center of the circle, or None if the points are collinear.
        """

        # Calculate midpoints of chords
        midpoint1 = [(p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2]
        midpoint2 = [(p1[0] + p3[0]) / 2, (p1[1] + p3[1]) / 2]

        # Calculate slopes of chords
        try:
            slope1 = (p2[1] - p1[1]) / (p2[0] - p1[0])
        except ZeroDivisionError:
            slope1 = float('inf')  # Handle vertical lines
        try:
            slope2 = (p3[1] - p1[1]) / (p3[0] - p1[0])
        except ZeroDivisionError:
            slope2 = float('inf')

        # Calculate slopes of perpendicular bisectors
        if slope1 == float('inf'):
            slope_perp1 = 0
        else:
            slope_perp1 = -1 / slope1
        if slope2 == float('inf'):
            slope_perp2 = 0
        else:
            if slope2 == 0:
                slope2 = slope2+0.001
            slope_perp2 = -1 / slope2+0.001

        # Calculate y-intercepts of perpendicular bisectors
        intercept1 = midpoint1[1] - slope_perp1 * midpoint1[0]
        intercept2 = midpoint2[1] - slope_perp2 * midpoint2[0]

        # Find the intersection of perpendicular bisectors
        if slope_perp1 == slope_perp2:  # Parallel lines, points are collinear
            return (-1,-1)

        x = (intercept2 - intercept1) / (slope_perp1 - slope_perp2)
        y = slope_perp1 * x + intercept1
        center = (x, y)
        # Check for potential glint point
        distances = [
            np.linalg.norm(np.array(p1) - np.array(center)),
            np.linalg.norm(np.array(p2) - np.array(center)),
            np.linalg.norm(np.array(p3) - np.array(center))
        ]

        if any(dist < (radius - radius_thresh) for dist in distances) or any(dist > (radius + radius_thresh) for dist in distances):
            return (-1,-1)  # Potential glint detected

        return x, y


    def balanced_points_selection(self, points_on, points_off, sample_size=None):
        """
        Estimate center by sampling equal numbers of ON and OFF events
        
        Args:
        - points_on: numpy array of (x, y) coordinates
        - points_off: numpy array of (x, y) coordinates
        - sample_size: number of points to sample from each polarity
        
        Returns:
        - Balanced center estimation
        """
        
        # If sample_size not specified, use minimum of ON/OFF points
        if sample_size is None:
            sample_size = min(len(points_on), len(points_off))
        
        # Randomly sample equal number of points from each polarity
        on_sample = points_on[np.random.choice(len(points_on), sample_size, replace=False)]
        off_sample = points_off[np.random.choice(len(points_off), sample_size, replace=False)]
        
        # Combine samples
        balanced_sample = np.concatenate([on_sample, off_sample])
        
        # Compute center of balanced sample
        return balanced_sample




    def fit_circle_with_radius_filter(self, points,polarities,  expected_radius, 
                                    radius_tolerance=0.5, 
                                    min_inner_radius=1.0,  # New parameter to filter center points
                                    max_iterations=100):
        """
        Fit a circle using RANSAC with radius filtering and center point exclusion
        
        Parameters:
        - points: numpy array of (x, y) points
        - expected_radius: approximate known radius of the circle
        - radius_tolerance: maximum allowed deviation from expected radius
        - min_inner_radius: minimum radius to exclude points near the center
        - max_iterations: maximum RANSAC iterations
        
        Returns:
        - center: estimated circle center
        - inlier_mask: boolean mask of inlier points
        """
        # Initial estimate of the center
       
        
        # Best model tracking

        num_points = len(points)


        # if (self.previous_center[0]<=0):# first frame
        #     sample_indices = np.random.choice(len(points), size=num_points//3, replace=False)
        #     random_points =  points[sample_indices]
        #     self.previous_center = np.mean(random_points, axis=0)
       
        
        #best_center = (-1,-1)
        best_inliers = []
        best_inliers_count = -1
        best_inlier_mask = None      
        #best_center_found = False

        #img_points = self.plot_points(points)
        threshold = expected_radius/5

        # Separate ON and OFF events
        on_points = points[polarities > 0]
        off_points = points[polarities == 0]
        num_random_points = 2*expected_radius
        inliers_dict_num = {}
        inliers_dict_centers = {}
        for it in range(max_iterations):
            # Randomly sample subset of points
            potential_center_found = False
            while not potential_center_found:
                balanced_points = self.balanced_points_selection(on_points, off_points, sample_size=2)
                p1, p2, p3 = balanced_points[0], balanced_points[2], random.choice((balanced_points[1],balanced_points[3]) )
                center = self.find_circle_center_from_three_points(p1, p2, p3, expected_radius, threshold)
                
                
                
                if center[0] > 0:
                    img = self.plot_points([p1, p2, p3], [center])
                    potential_center_found = True
                    

            # Calculate distances from all data points to the fitted circle
            balanced_points = self.balanced_points_selection(on_points, off_points, sample_size=num_random_points)

            distances = np.linalg.norm(balanced_points - np.array(center), axis=1) 

            # Identify inliers
            #below_thresh = (distances < (expected_radius + threshold))
            #above_thresh = (distances >= (expected_radius - threshold))
            inlier_mask = (
                (distances < (expected_radius + threshold)) &  # Radius deviation
                (distances >= (expected_radius - threshold))    # Minimum inner radius
            )

            #calculate mean of inliers
            inliers = [balanced_points[i] for i in range(2*num_random_points) if inlier_mask[i]]
            inlier_mean = np.mean(inliers, axis=0)
            distance_means = np.linalg.norm(np.array(inlier_mean) - np.array(center))
        
            num_inliers = np.sum(inlier_mask)
            # Update best fit if the number of inliers is greater
            if (distance_means < threshold):
                inliers_dict_num[it] = num_inliers
                inliers_dict_centers[it] = center
            
            # Update best model if more inliers found
            # if ((num_inliers > best_inliers_count) and (distance_means < threshold)):# or (num_inliers > num_points/2):
               
            #     print(num_inliers)
            #     best_inliers_count = num_inliers
            #     best_inlier_mean = inlier_mean
            #     best_inlier_mask = inlier_mask
            #     best_inliers = np.array(inliers)
            #     best_center = center
            #     best_iter = it


        #sort iterations by number of inliers
        sorted_iterations  = {k: v for k, v in sorted(inliers_dict_num.items(), key=lambda item: item[1], reverse=True)}  
        sorted_centers = [inliers_dict_centers[k] for k in sorted_iterations.keys()]
        img_inliers = self.plot_points(best_inliers, sorted_centers[:5])

        centers_mean = np.mean(sorted_centers[:5], axis=0)
        
        #center_distance = np.linalg.norm(np.array(centers_mean) - np.array(best_inlier_mean))
        #print(center_distance)     
        #print(best_center_found)   
        centers_mean = centers_mean.round().astype(int)        
        return centers_mean, best_inlier_mask


