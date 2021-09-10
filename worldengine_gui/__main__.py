#!/usr/bin/python
"""
PyQt5 GUI Interface for Worldengine
"""

import worldengine.model.world
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction, \
    QFileDialog, QLabel, QWidget, QGridLayout
import sys
from worldengine.model.world import World
from worldengine_gui.views import draw_bw_elevation_on_screen, draw_plates_on_screen, \
    draw_plates_and_elevation_on_screen, draw_land_on_screen
from worldengine.simulations.hydrology import WatermapSimulation
from worldengine.simulations.irrigation import IrrigationSimulation
from worldengine.simulations.humidity import HumiditySimulation
from worldengine.simulations.temperature import TemperatureSimulation
from worldengine.simulations.permeability import PermeabilitySimulation
from worldengine.simulations.biome import BiomeSimulation
from worldengine.simulations.precipitation import PrecipitationSimulation
from worldengine.simulations.icecap import IcecapSimulation
# from worldengine.generation import ErosionSimulation
from worldengine.simulations.erosion import ErosionSimulation
from worldengine_gui.views.PrecipitationsView import PrecipitationsView
from worldengine_gui.views.WatermapView import WatermapView
from worldengine_gui.views.BiomeView import BiomeView, BiomeScatterPlotView
from worldengine_gui.views.TemperatureView import TemperatureView
from worldengine_gui.views.SatelliteView import SatelliteView
from worldengine_gui.views.IcecapView import IcecapView
from worldengine_gui.ui_elements.basic_generation import GenerateDialog, GenerationProgressDialog
from worldengine_gui.ui_elements.simulation import SingleOperationDialog, SingleSimulationOp


def array_to_matrix():
    raise Exception("not implemented")


class MapLabel(QLabel):
    def __init__(self, target):
        super(QLabel, self).__init__()
        self.target = target

    def mouseMoveEvent(self, event):
        pos = (event.x(), event.y())
        self.world: worldengine.model.world.World
        elevation_data = self.world.elevation_at(pos)
        biome_data = None
        if self.world.has_biome():
            biome_data = self.world.biome_at(pos).name(),
        temperature_data = None
        if self.world.has_temperature():
            temperature_data = self.world.temperature_at(pos)
        humidity_data = None
        if self.world.has_humidity():
            humidity_data = self.world.humidity_at(pos)
        precipitation_data = None
        if self.world.has_precipitations():
            precipitation_data = self.world.precipitations_at(pos)
        water_map_data = None
        if self.world.has_watermap():
            water_map_data = str(self.world.watermap_at(pos))
        self.target.setText("\n".join((
            f"Position: {pos}",
            f"Biome: {biome_data}",
            f"Elevation: {elevation_data}",
            f"Temperature: {temperature_data}",
            f"Humidity: {humidity_data}",
            f"Precipitations: {precipitation_data}",
            f"Watermap: {water_map_data}"
        )))


class MapCanvas(QImage):
    def __init__(self, label, width, height):
        QImage.__init__(self, width, height, QImage.Format_RGB32)
        self.label = label
        self._update()

    def draw_world(self, world, view):
        self.label.resize(world.width, world.height)
        self.label.setMouseTracking(True)
        if view == 'bw':
            draw_bw_elevation_on_screen(world, self)
        elif view == 'plates':
            draw_plates_on_screen(world, self)
        elif view == 'plates and elevation':
            draw_plates_and_elevation_on_screen(world, self)
        elif view == 'land':
            draw_land_on_screen(world, self)
        elif view == 'precipitations':
            PrecipitationsView().draw(world, self)
        elif view == 'watermap':
            WatermapView().draw(world, self)
        elif view == "icecap":
            IcecapView().draw(world, self)
        elif view == "biome":
            BiomeView().draw(world, self)
        elif view == "biome_scatter_plot":
            BiomeScatterPlotView().draw(world, self)
        elif view == "temperature":
            TemperatureView().draw(world, self)
        elif view == "satellite":
            SatelliteView().draw(world, self)
        else:
            raise Exception("Unknown view %s" % view)
        self._update()

    def _update(self):
        self.label.setPixmap(QPixmap.fromImage(self))

    def set_pixel(self, x, y, col):
        self.setPixel(x, y, QColor(*col).rgb())


class WorldEngineGui(QMainWindow):
    def __init__(self):
        super(WorldEngineGui, self).__init__()
        self._init_ui()
        self.world = None
        self.current_view = None
        self.canvas = None

    def set_status(self, message):
        self.statusBar().showMessage(message)

    def _init_ui(self):
        self.resize(800, 600)
        self.setWindowTitle('Worldengine - A world generator')
        self.set_status('No world selected: create or load a world')
        self._prepare_menu()
        self.label2 = QLabel()
        self.label = MapLabel(self.label2)
        self.canvas = MapCanvas(self.label, 0, 0)

        # dummy widget to contain the layout manager
        self.main_widget = QWidget(self)

        self.setCentralWidget(self.main_widget)
        self.layout = QGridLayout(self.main_widget)
        # Set the stretch
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(2, 1)
        self.layout.setRowStretch(0, 1)
        self.layout.setRowStretch(2, 1)
        # Add widgets
        self.layout.addWidget(self.label, 1, 1)
        self.layout.addWidget(self.label2, 1, 2)

        self.setMouseTracking(True)

        self.show()

    def set_world(self, world):
        self.world = world
        self.canvas = MapCanvas(self.label, self.world.width,
                                self.world.height)
        self.label2.setText("Mouseover")
        self.label.world = world
        self._on_bw_view()

        self.saveproto_action.setEnabled(world is not None)

        self.bw_view.setEnabled(world is not None)
        self.plates_view.setEnabled(world is not None)
        self.plates_bw_view.setEnabled(world is not None)
        self.land_and_ocean_view.setEnabled(world is not None)

        self.erosion_action.setEnabled(world is not None and ErosionSimulation().is_applicable(world))
        self.humidity_action.setEnabled(world is not None and HumiditySimulation().is_applicable(world))
        self.irrigation_action.setEnabled(world is not None and IrrigationSimulation().is_applicable(world))
        self.permeability_action.setEnabled(world is not None and PermeabilitySimulation().is_applicable(world))

        self.temperature_action.setEnabled(world is not None and TemperatureSimulation().is_applicable(world))
        self.temperature_view.setEnabled(world is not None and TemperatureView().is_applicable(world))

        self.watermap_action.setEnabled(world is not None and WatermapSimulation().is_applicable(world))
        self.watermap_view.setEnabled(world is not None and WatermapView().is_applicable(world))

        self.precipitations_action.setEnabled(world is not None and PrecipitationSimulation.is_applicable(world))
        self.precipitations_view.setEnabled(world is not None and PrecipitationsView().is_applicable(world))

        self.icecap_action.setEnabled(world is not None and IcecapSimulation().is_applicable(world))
        self.icecap_view.setEnabled(world is not None and IcecapView.is_applicable(world))

        self.biome_action.setEnabled(world is not None and BiomeSimulation().is_applicable(world))
        self.biome_view.setEnabled(world is not None and BiomeView().is_applicable(world))
        self.biome_scatter_plot_view.setEnabled(world is not None and BiomeView().is_applicable(world))

        self.satellite_view.setEnabled(world is not None and SatelliteView.is_applicable(world))

    # noinspection DuplicatedCode
    def _prepare_menu(self):
        menubar = self.menuBar()
        menubar.setNativeMenuBar(False)


        # ----------
        # File Menu
        # ----------
        file_menu = menubar.addMenu('&File')
        # ----------------------------------------------------------------
        generate_action = QAction('&Generate', self)
        generate_action.setShortcut('Ctrl+G')
        generate_action.setStatusTip('Generate new world')
        generate_action.triggered.connect(self._on_generate)
        file_menu.addAction(generate_action)
        # ----------------------------------------------------------------
        open_action = QAction('&Open', self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open a saved world")
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)
        # ----------------------------------------------------------------
        self.saveproto_action = QAction('&Save (protobuf)', self)
        self.saveproto_action.setEnabled(False)
        self.saveproto_action.setShortcut('Ctrl+S')
        self.saveproto_action.setStatusTip('Save (protobuf format)')
        self.saveproto_action.triggered.connect(self._on_save_protobuf)
        file_menu.addAction(self.saveproto_action)
        # ----------------------------------------------------------------
        exit_action = QAction('Leave', self)
        exit_action.setShortcut('Ctrl+L')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(QApplication.quit)
        file_menu.addAction(exit_action)

        # -----------------
        # Simulations Menu
        # -----------------
        simulations_menu = menubar.addMenu('&Simulations')

        self.precipitations_action = QAction('Precipitations', self)
        self.precipitations_action.setEnabled(False)
        self.precipitations_action.triggered.connect(self._on_precipitations)
        simulations_menu.addAction(self.precipitations_action)

        self.erosion_action = QAction('Erosion', self)
        self.erosion_action.setEnabled(False)
        self.erosion_action.triggered.connect(self._on_erosion)
        simulations_menu.addAction(self.erosion_action)

        self.watermap_action = QAction('Watermap', self)
        self.watermap_action.setEnabled(False)
        self.watermap_action.triggered.connect(self._on_watermap)
        simulations_menu.addAction(self.watermap_action)

        self.irrigation_action = QAction('Irrigation', self)
        self.irrigation_action.setEnabled(False)
        self.irrigation_action.triggered.connect(self._on_irrigation)
        simulations_menu.addAction(self.irrigation_action)

        self.humidity_action = QAction('Humidity', self)
        self.humidity_action.setEnabled(False)
        self.humidity_action.triggered.connect(self._on_humidity)
        simulations_menu.addAction(self.humidity_action)

        self.temperature_action = QAction('Temperature', self)
        self.temperature_action.setEnabled(False)
        self.temperature_action.triggered.connect(self._on_temperature)
        simulations_menu.addAction(self.temperature_action)

        self.icecap_action = QAction('Icecap', self)
        self.icecap_action.setEnabled(False)
        self.icecap_action.triggered.connect(self._on_icecap_simulation)
        simulations_menu.addAction(self.icecap_action)

        self.permeability_action = QAction('Permeability', self)
        self.permeability_action.setEnabled(False)
        self.permeability_action.triggered.connect(self._on_permeability)
        simulations_menu.addAction(self.permeability_action)

        self.biome_action = QAction('Biome', self)
        self.biome_action.setEnabled(False)
        self.biome_action.triggered.connect(self._on_biome)
        simulations_menu.addAction(self.biome_action)

        # ----------
        # View Menu
        # ----------
        view_menu = menubar.addMenu('&View')

        self.bw_view = QAction('Black and white', self)
        self.bw_view.setEnabled(False)
        self.bw_view.triggered.connect(self._on_bw_view)
        view_menu.addAction(self.bw_view)

        self.plates_view = QAction('Plates', self)
        self.plates_view.setEnabled(False)
        self.plates_view.triggered.connect(self._on_plates_view)
        view_menu.addAction(self.plates_view)

        self.plates_bw_view = QAction('Plates and elevation', self)
        self.plates_bw_view.setEnabled(False)
        self.plates_bw_view.triggered.connect(self._on_plates_and_elevation_view)
        view_menu.addAction(self.plates_bw_view)

        self.land_and_ocean_view = QAction('Land and ocean', self)
        self.land_and_ocean_view.setEnabled(False)
        self.land_and_ocean_view.triggered.connect(self._on_land_view)
        view_menu.addAction(self.land_and_ocean_view)

        self.precipitations_view = QAction('Precipitations', self)
        self.precipitations_view.setEnabled(False)
        self.precipitations_view.triggered.connect(self._on_precipitations_view)
        view_menu.addAction(self.precipitations_view)

        self.watermap_view = QAction('Watermap', self)
        self.watermap_view.setEnabled(False)
        self.watermap_view.triggered.connect(self._on_watermap_view)
        view_menu.addAction(self.watermap_view)

        self.temperature_view = QAction("Temperature", self)
        self.temperature_view.setEnabled(False)
        self.temperature_view.triggered.connect(self._on_temperature_view)
        view_menu.addAction(self.temperature_view)

        self.icecap_view = QAction("Icecap", self)
        self.icecap_view.setEnabled(False)
        self.icecap_view.triggered.connect(self._on_icecap_view)
        view_menu.addAction(self.icecap_view)

        self.biome_view = QAction('Biome', self)
        self.biome_view.setEnabled(False)
        self.biome_view.triggered.connect(self._on_biome_view)
        view_menu.addAction(self.biome_view)

        self.biome_scatter_plot_view = QAction("Biome scatter plot", self)
        self.biome_scatter_plot_view.setEnabled(False)
        self.biome_scatter_plot_view.triggered.connect(self._on_biome_scatter_plot_view)
        view_menu.addAction(self.biome_scatter_plot_view)

        self.satellite_view = QAction("Satellite", self)
        self.satellite_view.setEnabled(False)
        self.satellite_view.triggered.connect(self._on_satellite_view)
        view_menu.addAction(self.satellite_view)

        self.setMenuBar(menubar)

    def _on_bw_view(self):
        self.current_view = 'bw'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_plates_view(self):
        self.current_view = 'plates'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_plates_and_elevation_view(self):
        self.current_view = 'plates and elevation'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_land_view(self):
        self.current_view = 'land'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_precipitations_view(self):
        self.current_view = 'precipitations'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_watermap_view(self):
        self.current_view = 'watermap'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_icecap_view(self):
        self.current_view = 'icecap'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_biome_view(self):
        self.current_view = 'biome'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_biome_scatter_plot_view(self):
        self.current_view = 'biome_scatter_plot'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_temperature_view(self):
        self.current_view = 'temperature'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_satellite_view(self):
        self.current_view = 'satellite'
        self.canvas.draw_world(self.world, self.current_view)

    def _on_generate(self):
        dialog = GenerateDialog(self)
        ok = dialog.exec_()
        if ok:
            seed = dialog.seed()
            width = dialog.width()
            height = dialog.height()
            num_plates = dialog.num_plates()
            name = str(dialog.name())
            dialog2 = GenerationProgressDialog(self, seed, name, width, height,
                                               num_plates)
            ok2 = dialog2.exec_()
            if ok2:
                self.set_world(dialog2.world)

    def _on_save_protobuf(self):
        filename = QFileDialog.getSaveFileName(self, "Save world", "", "*.world")
        self.world.protobuf_to_file(filename[0])

    def _on_open(self):
        filename = QFileDialog.getOpenFileName(self, "Open world", "", "*.world")
        if filename[0] != '':
            world = World.open_protobuf(filename[0])
            self.set_world(world)

    def _on_precipitations(self):
        dialog = SingleOperationDialog(self, self.world, SingleSimulationOp("Simulating precipitations", PrecipitationSimulation()))
        ok = dialog.exec_()
        if ok:
            # just to refresh things to enable
            self.set_world(self.world)

    def _on_erosion(self):
        dialog = SingleOperationDialog(self, self.world, SingleSimulationOp("Simulating erosion", ErosionSimulation()))
        ok = dialog.exec_()
        if ok:
            # just to refresh things to enable
            self.set_world(self.world)

    def _on_watermap(self):
        dialog = SingleOperationDialog(self, self.world, SingleSimulationOp("Simulating water flow", WatermapSimulation()))
        ok = dialog.exec_()
        if ok:
            # just to refresh things to enable
            self.set_world(self.world)

    def _on_irrigation(self):
        dialog = SingleOperationDialog(self, self.world,
                                       SingleSimulationOp("Simulating irrigation",
                                                          IrrigationSimulation()))
        ok = dialog.exec_()
        if ok:
            # just to refresh things to enable
            self.set_world(self.world)

    def _on_humidity(self):
        dialog = SingleOperationDialog(self, self.world, SingleSimulationOp("Simulating humidity", HumiditySimulation()))
        ok = dialog.exec_()
        if ok:
            # just to refresh things to enable
            self.set_world(self.world)

    def _on_temperature(self):
        dialog = SingleOperationDialog(self, self.world, SingleSimulationOp("Simulating temperature", TemperatureSimulation()))
        ok = dialog.exec_()
        if ok:
            # just to refresh things to enable
            self.set_world(self.world)

    def _on_icecap_simulation(self):
        dialog = SingleOperationDialog(self, self.world, SingleSimulationOp("Simulating Icecap", IcecapSimulation()))
        ok = dialog.exec_()
        if ok:
            # just to refresh things to enable
            self.set_world(self.world)

    def _on_permeability(self):
        dialog = SingleOperationDialog(self, self.world, SingleSimulationOp("Simulating permeability", PermeabilitySimulation()))
        ok = dialog.exec_()
        if ok:
            # just to refresh things to enable
            self.set_world(self.world)

    def _on_biome(self):
        dialog = SingleOperationDialog(self, self.world, SingleSimulationOp("Simulating biome", BiomeSimulation()))
        ok = dialog.exec_()
        if ok:
            # just to refresh things to enable
            self.set_world(self.world)


app = QApplication(sys.argv)
lg = WorldEngineGui()
assert lg
sys.exit(app.exec_())
