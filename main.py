import os
import sys

sys.path.append("./com_utils") 
sys.path.append("./subtitle") 

from PyQt5.QtWidgets import QApplication, QMainWindow

#os.environ["IMAGEIO_FFMPEG_EXE"] = "d:\\bin\\ffmpeg\\bin\\ffmpeg.exe"

import Ui_MainWindow

if __name__ == '__main__' :
	app = QApplication(sys.argv)
	MainWindow = QMainWindow()
	ui = Ui_MainWindow.Ui_MainWindow()
	ui.setupUi(MainWindow)
	MainWindow.show()
	sys.exit(app.exec_())