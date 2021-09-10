import worldengine.draw
from worldengine.model.world import World
import worldengine.draw
from worldengine.image_io import PNGWriter
from PyQt5.QtGui import QImage


class SatelliteView(object):
    @staticmethod
    def is_applicable(world: World):
        return world.has_watermap() and world.has_biome() and world.has_icecap()

    @staticmethod
    def draw(world: World, canvas: QImage):
        img = PNGWriter.rgba_from_dimensions(world.width, world.height)
        worldengine.draw.draw_satellite(world, img)
        img_bytes = img.to_bytes()
        canvas.loadFromData(img_bytes)
