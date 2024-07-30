import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor
from qt_window import Session
from random import uniform, shuffle



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(QDesktopWidget().screenGeometry(1))
        self.setStyleSheet("background-color: black;")
        self.showFullScreen()
        self.circle_position = (-100, -100)
        self.session = Session(screen_geometry=self.frameGeometry())
        self.init_ui()
        self.sequence_started = False
        self.trial_number = 0
        self.total_trials = 3

    def init_ui(self):
        # Set up any UI elements or signals/slots here
        pass

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('white'))
        painter.drawEllipse(self.circle_position[0], self.circle_position[1], 100, 100)

    def update_circle_position(self, x, y):
        self.circle_position = (x, y)
        #print(x,y)
        self.update()

    def show_circle_origin(self):
        #print('at origin')
        self.circle_position = self.session.coords_origin
        self.update()

    def show_blank_screen(self):
        self.circle_position = (-100, -100)
        self.update()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not self.sequence_started:
            self.trial_number += 1
            if self.trial_number <= self.total_trials:
                self.sequence_started = True
                self.show_blank_screen()
                self.run_trial()
                #self.simulate_eye_tracking()
               
            else:
                # End of experiment logic
                #print("Experiment finished!")
                self.close()

    def run_trial(self):
        # this runs after key has been pressed
        
        rec_file_name = 'rec_circle_{}.aedat4'.format(self.trial_number) # set recording file-name
        rand_1 = uniform(0.5,1) # set first random wait time 
        x, y = self.session.coords_list[self.session.shuffled_dest_order[self.trial_number]]

        msec = 100
        QTimer.singleShot(msec,  self.show_circle_origin) # show circle at center of screen
        
        msec += 100
        #QTimer.singleShot(msec, self.session.recorder.start_record(rec_file_name))#start recording
        
        msec += (500 +int(rand_1*1000))
        
        QTimer.singleShot(msec, lambda x=x, y=y: self.update_circle_position(x, y))
        
        msec += 1000
        #QTimer.singleShot(msec, self.session.recorder.stop_record())#stop recording
        
        msec += 100
        QTimer.singleShot(msec,  self.show_blank_screen)
        self.trial_number += 1
        self.sequence_started = False  # Reset flag after sequence ends


    def simulate_eye_tracking(self):
        # Simulated eye-tracking data
        sequences = [
            [(200, 200), (300, 300), (400, 400)]#,
            #[(500, 500), (600, 600), (400, 400)]#,
            #[(600, 200), (700, 300), (400, 400)]
        ]

        # Run each sequence with a delay after the previous one finishes
        count = 0
        for count, sequence in enumerate(sequences):
            QTimer.singleShot(len(sequence) * 1000 * count, lambda seq=sequence: self.run_sequence(seq))
        
        QTimer.singleShot(len(sequence) *(count+1) * 1000, lambda x=-100, y=-100: self.update_circle_position(x, y))

        self.sequence_started = False  # Reset flag after sequence ends


    def run_sequence(self, sequence):
        for i, (x, y) in enumerate(sequence):
            QTimer.singleShot(i * 1000, lambda x=x, y=y: main_window.update_circle_position(x, y))


def run_circle(main_window, position, delay=1000):
    QTimer.singleShot(delay, lambda x=position[0], y=position[1]: main_window.update_circle_position(x, y))

def simulate_eye_tracking(main_window):
    # Simulated eye-tracking data
    sequences = [
        [(200, 200), (300, 300), (400, 400)],
        [(500, 500), (600, 600), (400, 400)],
        [(600, 200), (700, 300), (400, 400)]
    ]

    # Run each sequence with a delay after the previous one finishes
    for i, sequence in enumerate(sequences):
        QTimer.singleShot(len(sequence) * 1000*i, lambda seq=sequence: run_sequence(main_window, seq))
    main_window.sequence_started = False

def run_eye_tracking_sequences(main_window):
    pos = (900, 100)
    pos_black = (-200,-200)
    time_first = 2000
    time_second = 4000
    QTimer.singleShot(time_first, lambda pos=pos: run_circle(main_window, pos))
    QTimer.singleShot(time_second, lambda pos=pos: run_circle(main_window, pos_black))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    
    #simulate_eye_tracking(main_window)
    #run_eye_tracking_sequences(main_window)

    sys.exit(app.exec_())
