import jack
import sys

from PyQt5.QtWidgets import QApplication

from superboucle.gui import Gui

client = jack.Client("Super Boucle")
app = QApplication(sys.argv)
gui = Gui(client, app)