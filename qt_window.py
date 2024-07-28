import sys
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
#from pyqtdarktheme import DarkPalette, DarkStyle
from PIL import Image, ImageDraw
from time import sleep
from random import uniform, shuffle
from camera_cap import Recorder


# class ImageLoaderThread(QThread):
#     image_loaded = pyqtSignal(QImage)

#     def __init__(self, parent=None):
#         super().__init__(parent)
        


#     def run(self):
#         while True:
#             image_path = self.get_next_image_path()  # Your logic to get next image path
#             if not image_path:
#                 break

#             try:
#                 image = QImage(image_path)
#                 if image.isNull():
#                     # Handle invalid image loading (optional)
#                     print(f"Error loading image: {image_path}")
#                 else:
#                     self.image_loaded.emit(image)
#             except Exception as e:
#                 # Handle potential errors during image loading
#                 print(f"Error loading image: {image_path} ({e})")

#             # Optional: Add a delay between images (use sleep or timer)


# class EyeTrackingWindow(QTWidget):
#     def __init__(self, duration=1000, size=20):
#         super().__init__()
#         self.setWindowTitle("Eye Tracking Window")
#         self.setScaledContents(True)
#         self.loop_count=3
#         # Initialize loop counter
#         self.current_loop_count = 0

#         # Get the screen geometry of the second screen
#         screen_number = 1  # Index of the second screen
#         self.screen_geometry = QApplication.screens()[screen_number].geometry()
        
#         # Set window geometry to match screen geometry
#         self.setGeometry(self.screen_geometry)

#         # Calculate the radius based on screen size
#         self.circle_radius = min(self.screen_geometry.width(), self.screen_geometry.height()) // 20
        
#         self.image_label = QLabel(self)

#         self.current_coordinate_index = 0

#         # Create a timer to update the window periodically (every 100 ms)
#         #self.timer = QTimer(self)
#         #self.timer.timeout.connect(self.move_circle)
#         #self.timer.start(10)  # Milliseconds
#         # Create a separate thread for loading images
#         #self.image_loader_thread = ImageLoaderThread()
#         #self.image_loader_thread.image_loaded.connect(self.set_image)
#         #self.image_loader_thread.start()

#     def get_next_image_path(self):
#         """Sets the image path and triggers image loading in the thread."""
#         self.image_path = 'origin.png'
#         self.image_updated.emit(self.image_path)  # Emit signal for potential UI updates


#     def set_image(self, image):
#         """Sets the loaded image on the label."""
#         self.image_label.setPixmap(QPixmap.fromImage(image))
#         self.showFullScreen()

#     def move_circle(self):
#         # Get the current coordinate
#         if self.current_coordinate_index < len(self.coordinates_sequence):
#             x, y = self.coordinates_sequence[self.current_coordinate_index]
#             self.current_coordinate_index += 1
#         else:
#             # If reached the end of the sequence
#             # and the loop count is not exceeded, reset index
#             self.current_coordinate_index = 0
#             self.current_loop_count += 1

#             # Get the current coordinate after resetting index
#             x, y = self.coordinates_sequence[self.current_coordinate_index]

#         # Stop the application if the loop count is exceeded
#         if self.current_loop_count >= self.loop_count:
#             QApplication.quit()
#             return

#         # Create an image with a black background
#         # image = Image.new("RGB", (self.width(), self.height()), "black")

#         # Draw a white circle on the image
#         # draw = ImageDraw.Draw(image)
#         # draw.ellipse((x - self.circle_radius, y - self.circle_radius,
#         #               x + self.circle_radius, y + self.circle_radius),
#         #              fill="white")

#         # Save the PIL image to a temporary file
#         #temp_file = tempfile.NamedTemporaryFile(suffix=".png", dir='.',)
#         # temp_file_name = 'temp.png'
#         image.save(temp_file_name, "PNG")

#         # Load the temporary image file into a QPixmap
#         # qimage = QPixmap(temp_file_name)

#         # Set the image on the QLabel
#         # self.setPixmap(qimage)


class Session():

    def __init__(self, screen_geometry) -> None:
        #self.recorder = Recorder()
        # self.qt_window = EyeTrackingWindow()
        self.screen_geometry = screen_geometry
        self.screen_resolution = ()
        self.screen_w = 0
        self.screen_h = 0
        self.circle_radius = 0
        self.num_trials = 3
        self.screen_dims = (0,0)
        self.coords_origin = (0,0)
        self.num_coords = self.num_trials
        self.coords_current_idx = 0
        self.shuffled_dest_order = []
        self.coords_list = []
        self.circles_dict = {}
        self.circles_order = []
        self.process_circles()
        pass

    def process_circles(self):
        self.screen_resolution = (self.screen_geometry.width(),self.screen_geometry.height() )
        self.screen_w = self.screen_resolution[0]
        self.screen_h = self.screen_resolution[1]
        self.circle_radius = self.screen_w //25#min(screen_geometry.width(), screen_geometry.height()) // 20
        #set origin coords
        self.coords_origin = (self.screen_w //2,self.screen_h//2)
        # save origin circle png
        #self.origin_circle_file = 'origin.png'
        #image = Image.new("RGB", (self.screen_w, self.screen_h), "black")
        # Draw a white circle on the image
        #draw = ImageDraw.Draw(image)
        x = self.coords_origin[0]
        y = self.coords_origin[1]
        # draw.ellipse((x - self.circle_radius, y - self.circle_radius,
        #             x + self.circle_radius, y + self.circle_radius),
        #             fill="white")
        # image.save(self.origin_circle_file, "PNG")
        # Define a sequence of coordinates
        self.coords_list = [(self.screen_w // 4, self.screen_h // 2), 
                            (3*self.screen_w // 4, self.screen_h // 2), 
                            (self.screen_w// 4, self.screen_h // 2)]

        self.circles_order = list(range(0,self.num_coords)) # for now ordered list
        #save pngs for respective circles
        for i, coord in enumerate(self.coords_list):
            x = coord[0]
            y = coord[1]
            # Create an image with a black background
            # image = Image.new("RGB", (self.screen_w, self.screen_h), "black")

            # # Draw a white circle on the image
            # draw = ImageDraw.Draw(image)
            # draw.ellipse((x - self.circle_radius, y - self.circle_radius,
            #             x + self.circle_radius, y + self.circle_radius),
            #             fill="white")

            # # Save the PIL image to a png file
            # temp_file_name = 'circle_{}_{}.png'.format(x, y)
            # image.save(temp_file_name, "PNG")
            # self.circles_dict[i] = temp_file_name
        return
        
    # def show_circle(self):
    #     if self.coord_index <0:
    #         circle_file_name = self.origin_circle_file
    #     else:
    #         circle_file_name = self.circles_dict[self.coord_index]

    #     self.qt_window.set_image_path(circle_file_name)
        #qimage = QPixmap(circle_file_name)
        #self.qt_window.setPixmap(qimage)
        
        #self.qt_window.update()

    def run_trial(self):

         
        #x, y = self.coords_list[self.coords_current_idx]
        #rec_file_name = 'rec_circle_{}.aedat4'.format(x, y)
        rec_file_name = 'rec_circle_{}.aedat4'.format(self.trial_num) # set recording file-name
        rand_1 = uniform(0.5,1) # set random wait time 
        
        # wait for key to indicate readiness
        #inpt = input("Press Enter continue: ") 
       
        #show circle at origin 
        self.coord_index = -1

        #self.qt_window.show()
        #self.show_circle()
        
        #wait for 0.1 sec and start recording
        sleep(0.1)
        #self.recorder.start_record(rec_file_name)
        #wait for random time and move circle
        sleep(0.5+rand_1)
        self.coord_index = self.shuffled_dest_order[self.trial_num]
        self.show_circle()
        #wait for 0.5 sec and stop recording
        sleep(0.5)
        #save recording 
        #self.recorder.stop_record()

    def run_session(self):

        #shuffle destination order 
        self.shuffled_dest_order = self.circles_order
        shuffle(self.shuffled_dest_order)
        print(self.shuffled_dest_order)
        self.trial_num = 0
        for i in range(self.num_trials-1):
            self.run_trial()
            self.trial_num = i




def main():
    # test qt-window
    app = QApplication(sys.argv)
    #window = EyeTrackingWindow()
    #window.show()

    session = Session()
    session.run_session()
    #session.qt_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
