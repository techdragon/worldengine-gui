from PyQt5 import QtGui
from worldengine.model.world import World
import worldengine.draw


class BiomeView(object):
    @staticmethod
    def is_applicable(world: World):
        return world.has_biome()

    @staticmethod
    def draw(world: World, canvas):
        worldengine.draw.draw_biome(world, canvas)
