import dv_processing as dv
from time import sleep
import threading 
# cameras = dv.io.discoverDevices()

# print(cameras)

# capture = dv.io.CameraCapture(cameraName=cameras[0])

# if capture.isEventStreamAvailable():
#     # Get the event stream resolution
#     resolution = capture.getEventResolution()

#     # Print the event stream capability with resolution value
#     print(f"* Events at ({resolution[0]}x{resolution[1]}) resolution")


class Recorder:
    def __init__(self):
        self.capture = None
        self.stop_recording = False
        self.init_capture()


    def init_capture(self):
        cameras = dv.io.discoverDevices()

        print(cameras)

        self.capture = dv.io.CameraCapture(cameraName=cameras[0])
        self.eventsAvailable = self.capture.isEventStreamAvailable()
        self.framesAvailable = self.capture.isFrameStreamAvailable()
        self.imuAvailable = self.capture.isImuStreamAvailable()
        self.triggersAvailable = self.capture.isTriggerStreamAvailable()

    def stop_record(self):
        self.stop_recording = True

    def start_record(self, file_name):
        # Check whether frames are available
        self.stop_recording = False

        self.writer = dv.io.MonoCameraWriter(file_name, self.capture)
        print("Start recording")
        return 
    
    def save_recording(self):

        while not self.stop_recording:#self.capture.isConnected():
            #if eventsAvailable:
            # Get Events
            events = self.capture.getNextEventBatch()
            # Write Events
            if events is not None:
                self.writer.writeEvents(events, streamName='events')
                print(events[0])
            if self.framesAvailable:
                # Get Frame
                frame = self.capture.getNextFrame()
                # Write Frame
                if frame is not None:
                    self.writer.writeFrame(frame, streamName='frames')
            if self.stop_recording:
                print("Stop recording")
                break
        #self.stop_recording = False
        
            # if imuAvailable:
            #     # Get IMU data
            #     imus = camera.getNextImuBatch()
            #     # Write IMU data
            #     if imus is not None:
            #         writer.writeImuPacket(imus, streamName='imu')

            # if triggersAvailable:
            #     # Get trigger data
            #     triggers = camera.getNextTriggerBatch()
            #     # Write trigger data
            #     if triggers is not None:
            #         writer.writeTriggerPacket(triggers, streamName='triggers')


if __name__ == '__main__':
    recorder = Recorder()
    file_test = 'test.aedat4'
    recorder.start_record(file_test)
    thread_record = threading.Thread(target=recorder.save_recording, daemon=True)
    thread_record.start()
    sleep(3)
    recorder.stop_record()