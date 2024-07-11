import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPainter, QColor, QKeyEvent



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(QDesktopWidget().screenGeometry(1))
        self.setStyleSheet("background-color: black;")
        self.showFullScreen()
        self.circle_position = (-100, -100)
        self.init_ui()
        self.sequence_started = False

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
        print(x,y)
        self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return and not self.sequence_started:
            self.sequence_started = True
            simulate_eye_tracking(self)


def run_sequence(main_window, sequence):
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
