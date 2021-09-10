import random
import threading

from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QPushButton


class SingleOperationDialog(QDialog):
    def __init__(self, parent, world, operation):
        QDialog.__init__(self, parent)
        self.operation = operation
        self._init_ui()
        self.op_thread = SingleOperationThread(world, operation, self)
        self.op_thread.start()

    def _init_ui(self):
        self.resize(400, 100)
        self.setWindowTitle(self.operation.title())
        grid = QGridLayout()

        self.status = QLabel('....')
        grid.addWidget(self.status, 0, 0, 1, 3)

        cancel = QPushButton('Cancel')
        grid.addWidget(cancel, 1, 0, 1, 1)
        cancel.clicked.connect(self._on_cancel)

        done = QPushButton('Done')
        grid.addWidget(done, 1, 2, 1, 1)
        done.clicked.connect(self._on_done)
        done.setEnabled(False)
        self.done = done

        self.setLayout(grid)

    def _on_cancel(self):
        QDialog.reject(self)

    def _on_done(self):
        QDialog.accept(self)

    def on_finish(self):
        self.done.setEnabled(True)

    def set_status(self, message):
        self.status.setText(message)


class SingleOperationThread(threading.Thread):
    def __init__(self, world, operation, ui):
        threading.Thread.__init__(self)
        self.world = world
        self.operation = operation
        self.ui = ui

    def run(self):
        self.operation.execute(self.world, self.ui)


class SingleSimulationOp(object):
    def __init__(self, title, simulation):
        self._title = title
        self.simulation = simulation

    def title(self):
        return self._title

    def execute(self, world, ui):
        """

        :param ui: the dialog with the set_status and on_finish methods
        :return:
        """
        seed = random.randint(0, 65536)
        ui.set_status("%s: started (seed %i)" % (self.title(), seed))
        self.simulation.execute(world, seed)
        ui.set_status("%s: done (seed %i)" % (self.title(), seed))
        ui.on_finish()