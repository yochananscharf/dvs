import streamlit as st
import sys
from PyQt5.QtWidgets import QApplication, QLabel
from qt_window import EyeTrackingWindow


USE_APP = False



def main():
    if USE_APP:
        st.title("Eye Tracking App")

    # Range slider for setting the circle diameter
    circle_diameter = st.slider("Circle Diameter", min_value=10, max_value=100, value=50, step=1)

    # Range slider for setting the duration between circle coordinates
    duration_between_coordinates = st.slider("Duration Between Coordinates (ms)", min_value=100, max_value=2000, value=500, step=100)

    # Launch button
    if USE_APP:
        if st.button("Launch Eye Tracking Window"):
        # Instantiate EyeTrackingWindow class with user-defined parameters
            eye_tracking_window = EyeTrackingWindow(size=circle_diameter, duration=duration_between_coordinates)
            ###
            ###
    eye_tracking_window = EyeTrackingWindow(size=circle_diameter, duration=duration_between_coordinates)
    eye_tracking_window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    app = QApplication(sys.argv)  # Initialize QApplication instance

    main()