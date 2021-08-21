from PyQt5 import QtGui

from worldengine.model.world import World
import worldengine.draw


class WatermapView(object):
    @staticmethod
    def is_applicable(world):
        return world.has_watermap()

    @staticmethod
    def draw(world: World, canvas):
        worldengine.draw.draw_ocean(world.layers['ocean'].data, canvas)
