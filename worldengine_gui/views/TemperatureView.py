import worldengine.draw
from worldengine.model.world import World
import worldengine.draw


class TemperatureView(object):
    @staticmethod
    def is_applicable(world: World):
        return world.has_temperature()

    @staticmethod
    def draw(world: World, canvas):
        worldengine.draw.draw_temperature_levels(world, canvas)
