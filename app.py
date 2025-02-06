import sys
import ctypes
from lib.windows.main_window import MainWindow
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

# tell Windows the correct AppUserModelID, to set Taskbar Icon. See link below for more details:
# https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
app_id = u'CSVthis'  # arbitrary string (in unicode)
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

# If you know you won't use command line arguments QApplication([]) works too.
app = QApplication(sys.argv)

# sets icon for all
app.setWindowIcon(QIcon("lib/assets/CSVthis256x256.ico"))

# Create a Qt widget, which will be our window.
main_window = MainWindow()
main_window.show()  # Windows are hidden by default.

# Start the event loop.
app.exec()

# Your application won't reach here until you exit and the event loop has stopped.
