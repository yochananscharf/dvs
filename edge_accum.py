import dv_processing as dv
from PIL import Image
import streamlit as st
from datetime import timedelta
import time

file_path_a  = 'data/dvSave-2024_01_09_18_02_30.aedat4'
file_path_b  = 'data/dvSave-2024_01_09_18_02_32.aedat4'

image_area = st.empty()

capture = dv.io.MonoCameraRecording(file_path_a)

# Make sure it supports event stream output, throw an error otherwise
if not capture.isEventStreamAvailable():
    raise RuntimeError("Input camera does not provide an event stream.")

# Initialize an accumulator with some resolution
accumulator = dv.EdgeMapAccumulator(capture.getEventResolution())

# Apply configuration, these values can be modified to taste
accumulator.setNeutralPotential(0.25)
accumulator.setContribution(0.25)
#accumulator.setNeutralPotential(0.75)
accumulator.setIgnorePolarity(False)


# Initialize a slicer
slicer = dv.EventStreamSlicer()


# Declare the callback method for slicer
def slicing_callback(events: dv.EventStore):
    # Pass events into the accumulator and generate a preview frame
    accumulator.accept(events)
    frame = accumulator.generateFrame()

    # Show the accumulated image
    image_area.image(Image.fromarray(frame.image))


# Register callback to be performed every 33 milliseconds
slicer.doEveryTimeInterval(timedelta(milliseconds=33), slicing_callback)

# Run the event processing while the camera is connected
while capture.isRunning():
    # Receive events
    events = capture.getNextEventBatch()

    # Check if anything was received
    if events is not None:
        # If so, pass the events into the slicer to handle them
        slicer.accept(events)
        time.sleep(0.01)