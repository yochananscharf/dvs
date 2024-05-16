import sys
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
#from pyqtdarktheme import DarkPalette, DarkStyle
from PIL import Image, ImageDraw

class Session:
    def __init__(self) -> None:
        self.num_trials = 1
        self.screen_dims = (0,0)
        self.coords_origin = (0,0)
        self.coords_list = []
        pass
def run_trial()
def run_session(self):
    for trial in self.num_trials:
        self.run_trial()


class EyeTrackingWindow(QLabel):
    def __init__(self, duration=1000, size=20):
        super().__init__()
        self.setWindowTitle("Eye Tracking Window")
        self.setScaledContents(True)
        self.loop_count=3
        # Initialize loop counter
        self.current_loop_count = 0

        # Get the screen geometry of the second screen
        screen_number = 1  # Index of the second screen
        screen_geometry = QApplication.screens()[screen_number].geometry()
        
        # Set window geometry to match screen geometry
        self.setGeometry(screen_geometry)

        # Calculate the radius based on screen size
        self.circle_radius = min(screen_geometry.width(), screen_geometry.height()) // 20
        
        # Define a sequence of coordinates
        self.coordinates_sequence = [(screen_geometry.width() // 4, screen_geometry.height() // 2), 
                                     (3*screen_geometry.width() // 4, screen_geometry.height() // 2), 
                                     (screen_geometry.width() // 4, screen_geometry.height() // 2)]

        self.current_coordinate_index = 0

        # Create a timer to update the window periodically (every 100 ms)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_circle)
        self.timer.start(1000)  # Milliseconds

    def move_circle(self):
        # Get the current coordinate
        if self.current_coordinate_index < len(self.coordinates_sequence):
            x, y = self.coordinates_sequence[self.current_coordinate_index]
            self.current_coordinate_index += 1
        else:
            # If reached the end of the sequence
            # and the loop count is not exceeded, reset index
            self.current_coordinate_index = 0
            self.current_loop_count += 1

            # Get the current coordinate after resetting index
            x, y = self.coordinates_sequence[self.current_coordinate_index]

        # Stop the application if the loop count is exceeded
        if self.current_loop_count >= self.loop_count:
            QApplication.quit()
            return

        # Create an image with a black background
        image = Image.new("RGB", (self.width(), self.height()), "black")

        # Draw a white circle on the image
        draw = ImageDraw.Draw(image)
        draw.ellipse((x - self.circle_radius, y - self.circle_radius,
                      x + self.circle_radius, y + self.circle_radius),
                     fill="white")

        # Save the PIL image to a temporary file
        #temp_file = tempfile.NamedTemporaryFile(suffix=".png", dir='.',)
        temp_file_name = 'temp.png'
        image.save(temp_file_name, "PNG")

        # Load the temporary image file into a QPixmap
        qimage = QPixmap(temp_file_name)

        # Set the image on the QLabel
        self.setPixmap(qimage)

def main():
    app = QApplication(sys.argv)
    window = EyeTrackingWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
