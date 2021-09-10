from worldengine.model.world import World
from worldengine.image_io import PNGWriter
from PyQt5.QtGui import QImage


class IcecapView(object):
    @staticmethod
    def is_applicable(world: World):
        return world.has_icecap()

    @staticmethod
    def draw(world: World, canvas: QImage):
        img = PNGWriter.grayscale_from_array(world.layers['icecap'].data, scale_to_range=True)
        img_bytes = img.to_bytes()
        canvas.loadFromData(img_bytes)
