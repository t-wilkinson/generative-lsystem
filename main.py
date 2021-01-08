import numpy as np
import lsystem
import lsystem_old
from lsystem_old import LSystem


def run_lsystem():
    lsystem1 = lsystem.LSystem(fullscreen=True)
    lsystem1('pentaplexity', 'cross')
    lsystem1('tiled_square', rotation=[0.0, -0.001])
    lsystem1('sierpinski_square')
    lsystem1.on_close()


def run_lsystem_old():
    window = lsystem_old.Window()

    lsystem_old.init()

    LSystem.draw_time = 0.1
    LSystem.draw_all(window, 2)

    LSystem.iteration = 3
    LSystem.scale = [0.0004, 0, -50]
    LSystem.color = [255, 0]
    LSystem.r = lambda x: 255 - x
    LSystem.g = lambda x: x % 51 * 5
    LSystem.b = lambda x: x // 3
    LSystem.draw_time = 3
    LSystem.line_width = 7

    for fractal in LSystem['tiled_square', 'pentaplexity']:
        fractal.scale = [0.00005, 0.002, -40]
        fractal.rotation = [-0.000003, 0.0008]
        fractal.color = 255.0, 0

    for fractal in LSystem['levy_curve', 'sierpinski_arrowhead']:
        fractal.iteration = 5

    for fractal in LSystem:
        fractal.start_pos = [960 * np.random.random() + 480, 540 * np.random.random() + 270]
        fractal.rotation = [0, (np.random.random() - 0.5) / 100]

    LSystem.draw_all(window, 3)

    window.on_close()


if __name__ == '__main__':
    run_lsystem()
    run_lsystem_old()
