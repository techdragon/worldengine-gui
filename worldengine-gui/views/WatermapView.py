from PyQt5 import QtGui

import worldengine as we
import worldengine.draw

class WatermapView(object):

    @staticmethod
    def is_applicable(world):
        return world.has_watermap()

    @staticmethod
    def draw(world, canvas):
        we.draw.draw_ocean(world.layers['ocean'].data, canvas)
