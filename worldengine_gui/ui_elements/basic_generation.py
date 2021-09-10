import random
import threading

import numpy
import platec
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QSpinBox
from worldengine.generation import center_land, add_noise_to_elevation, place_oceans_at_map_borders, \
    initialize_ocean_and_thresholds
from worldengine.model.world import World, Size, GenerationParameters
from worldengine.step import Step


class GenerateDialog(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self._init_ui()

    def _init_ui(self):
        self.resize(500, 250)
        self.setWindowTitle('Generate a new world')
        grid = QGridLayout()

        seed = random.randint(0, 65535)

        name_label = QLabel('Name')
        grid.addWidget(name_label, 0, 0, 1, 1)
        name = 'world_seed_%i' % seed
        self.name_value = QLineEdit(name)
        grid.addWidget(self.name_value, 0, 1, 1, 2)

        seed_label = QLabel('Seed')
        grid.addWidget(seed_label, 1, 0, 1, 1)
        self.seed_value = self._spinner_box(0, 65525, seed)
        grid.addWidget(self.seed_value, 1, 1, 1, 2)

        width_label = QLabel('Width')
        grid.addWidget(width_label, 2, 0, 1, 1)
        self.width_value = self._spinner_box(100, 8192, 512)
        grid.addWidget(self.width_value, 2, 1, 1, 2)

        height_label = QLabel('Height')
        grid.addWidget(height_label, 3, 0, 1, 1)
        self.height_value = self._spinner_box(100, 8192, 512)
        grid.addWidget(self.height_value, 3, 1, 1, 2)

        plates_num_label = QLabel('Number of plates')
        grid.addWidget(plates_num_label, 4, 0, 1, 1)
        self.plates_num_value = self._spinner_box(2, 100, 10)
        grid.addWidget(self.plates_num_value, 4, 1, 1, 2)

        buttons_row = 5
        cancel = QPushButton('Cancel')
        generate = QPushButton('Generate')
        grid.addWidget(cancel, buttons_row, 1, 1, 1)
        grid.addWidget(generate, buttons_row, 2, 1, 1)

        cancel.clicked.connect(self._on_cancel)
        generate.clicked.connect(self._on_generate)

        self.setLayout(grid)

    @staticmethod
    def _spinner_box(min_value, max_value, value):
        spinner = QSpinBox()
        spinner.setMinimum(min_value)
        spinner.setMaximum(max_value)
        spinner.setValue(value)
        return spinner

    def _on_cancel(self):
        QDialog.reject(self)

    def _on_generate(self):
        QDialog.accept(self)

    def seed(self):
        return self.seed_value.value()

    def width(self):
        return self.width_value.value()

    def height(self):
        return self.height_value.value()

    def num_plates(self):
        return self.plates_num_value.value()

    def name(self):
        return self.name_value.text()


class GenerationProgressDialog(QDialog):
    def __init__(self, parent, seed, name, width, height, num_plates):
        QDialog.__init__(self, parent)
        self._init_ui()
        self.world = None
        self.gen_thread = GenerationThread(self, seed, name, width, height,
                                           num_plates)
        self.gen_thread.start()

    def _init_ui(self):
        self.resize(400, 100)
        self.setWindowTitle('Generating a new world...')
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


class GenerationThread(threading.Thread):
    def __init__(self, ui, seed, name, width, height, num_plates):
        threading.Thread.__init__(self)
        self.plates_generation = PlatesGeneration(seed, name, width, height,
                                                  num_plates=num_plates)
        self.ui = ui

    def run(self):
        # FIXME it should be merged with world_gen
        finished = False
        while not finished:
            (finished, n_steps) = self.plates_generation.step()
            self.ui.set_status('Plate simulation: step %i' % n_steps)
        self.ui.set_status('Plate simulation: terminating plates simulation')
        w = self.plates_generation.world()
        self.ui.set_status('Plate simulation: center land')
        center_land(w)
        self.ui.set_status('Plate simulation: adding noise')
        add_noise_to_elevation(w, random.randint(0, 4096))
        self.ui.set_status('Plate simulation: forcing oceans at borders')
        place_oceans_at_map_borders(w)
        self.ui.set_status('Plate simulation: finalization (can take a while)')
        initialize_ocean_and_thresholds(w)
        self.ui.set_status('Plate simulation: completed')
        self.ui.world = w
        self.ui.on_finish()


class PlatesGeneration(object):
    def __init__(self, seed, name, width, height,
                 sea_level=0.65, erosion_period=60,
                 folding_ratio=0.02, aggr_overlap_abs=1000000,
                 aggr_overlap_rel=0.33,
                 cycle_count=2, num_plates=10):
        self.name = name
        self.width = width
        self.height = height
        self.seed = seed
        self.n_plates = num_plates
        self.ocean_level = sea_level
        self.p = platec.create(seed, width, height, sea_level, erosion_period,
                               folding_ratio,
                               aggr_overlap_abs, aggr_overlap_rel, cycle_count,
                               num_plates)
        self.steps = 0

    def step(self):
        if platec.is_finished(self.p) == 0:
            platec.step(self.p)
            self.steps += 1
            return False, self.steps
        else:
            return True, self.steps

    def world(self):
        world = World(
            name=self.name,
            size=Size(self.width, self.height),
            seed=self.seed,
            generation_params=GenerationParameters(
                n_plates=self.n_plates,
                ocean_level=self.ocean_level,
                step=Step.get_by_name("plates")
            )
        )
        hm = platec.get_heightmap(self.p)
        pm = platec.get_platesmap(self.p)
        world.elevation = (numpy.array(hm).reshape(self.width, self.height), None)
        world.plates = numpy.array(pm, dtype=numpy.uint16).reshape(self.width, self.height)
        return world