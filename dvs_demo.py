import dv_processing as dv
from PIL import Image
import streamlit as st
from datetime import timedelta
import time

# Initialize an empty store
# store = dv.EventStore()

# # Get the current timestamp
# timestamp = dv.now()

# # Add some events into the event store
# # This allocates and inserts events at the back, the function arguments are:
# # timestamp, x, y, polarity
# store.push_back(timestamp, 0, 0, True)
# store.push_back(timestamp + 1000, 1, 1, False)
# store.push_back(timestamp + 2000, 2, 2, False)
# store.push_back(timestamp + 3000, 3, 3, True)

# # Perform time-based slicing of event store, the output event store "sliced" will contain
# # the second and third events from above. The end timestamp (second argument) is 2001, since start
# # timestamp (first argument) is inclusive and timestamp is exclusive, so 1 is added.
# sliced = store.sliceTime(timestamp + 1000, timestamp + 2001)

# # This should print two events
# for ev in store:
#     print(f"Sliced event [{ev.timestamp()}, {ev.x()}, {ev.y()}, {ev.polarity()}]")


# Open a file
file_path_a  = 'data/dvSave-2024_01_09_18_02_30.aedat4'
file_path_b  = 'data/dvSave-2024_01_09_18_02_32.aedat4'



reader = dv.io.MonoCameraRecording(file_path_a)

# Get and print the camera name that data from recorded from
print(f"Opened an AEDAT4 file which contains data from [{reader.getCameraName()}] camera")
image_area = st.empty()
event_area = st.empty()
# Declare the callback method for slicer
def slicing_callback(events: dv.EventStore):
    # Pass events into the accumulator and generate a preview frame
    accumulator.accept(events)
    frame = accumulator.generateFrame()
    event_area.image(frame.image)
    # Show the accumulated image
    #cv.imshow("Preview", frame.image)
    #cv.waitKey(2)




# Check if event stream is available
if reader.isEventStreamAvailable():
    # Check the resolution of event stream
    resolution = reader.getEventResolution()

    # Print that the stream is present and its resolution
    print(f"  * Event stream with resolution [{resolution[0]}x{resolution[1]}]")

# Check if frame stream is available
if reader.isFrameStreamAvailable():
    # Check the resolution of frame stream
    resolution = reader.getFrameResolution()

    # Print that the stream is available and its resolution
    print(f"  * Frame stream with resolution [{resolution[0]}x{resolution[1]}]")

# Check if IMU stream is available
if reader.isImuStreamAvailable():
    # Print that the IMU stream is available
    print("  * IMU stream")

# Check if trigger stream is available
if reader.isTriggerStreamAvailable():
    # Print that the trigger stream is available
    print("  * Trigger stream")
# Initialize an accumulator with some resolution
accumulator = dv.Accumulator(reader.getEventResolution())

# Apply configuration, these values can be modified to taste
accumulator.setMinPotential(0.0)
accumulator.setMaxPotential(1.0)
accumulator.setNeutralPotential(0.5)
accumulator.setEventContribution(0.15)
accumulator.setDecayFunction(dv.Accumulator.Decay.EXPONENTIAL)
accumulator.setDecayParam(1e+6)
accumulator.setIgnorePolarity(False)
accumulator.setSynchronousDecay(False)

# Initialize preview window
#cv.namedWindow("Preview", cv.WINDOW_NORMAL)

# Initialize a slicer
slicer = dv.EventStreamSlicer()
slicer.doEveryTimeInterval(timedelta(milliseconds=33), slicing_callback)

# Variable to store the previous frame timestamp for correct playback
lastTimestamp = None

# Run the loop while camera is still connected
cur_frame = 0
success = True

while reader.isRunning():

    cur_frame += 1

    # Read a frame from the camera
    frame = reader.getNextFrame()

    if frame is not None:
   
    #if cur_frame % frame_skip == 0: # only analyze every n=300 frames
        print('frame: {}'.format(cur_frame)) 
        pil_img = Image.fromarray(frame.image) # convert opencv frame (with type()==numpy) into PIL Image
        image_area.image(pil_img)

        # Print the timestamp of the received frame
        print(f"Received a frame at time [{frame.timestamp}]")

        # Show a preview of the image
        #cv.imshow("Preview", frame.image)

        # Calculate the delay between last and current frame, divide by 1000 to convert microseconds
        # to milliseconds
        delay = (2/1000 if lastTimestamp is None else (frame.timestamp - lastTimestamp) / 1000000)
        time.sleep(delay)
        # Perform the sleep
        #cv.waitKey(delay)

        # Store timestamp for the next frame
        lastTimestamp = frame.timestamp

        # Read batch of events
        events = reader.getNextEventBatch()

        # Check if anything was received
        if events is not None:
        # If so, pass the events into the slicer to handle them
            slicer.accept(events)
