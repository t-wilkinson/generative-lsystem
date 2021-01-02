import json
import pyglet
from pyglet import graphics
from pyglet.graphics import vertexdomain
import numpy as np
from time import time

pyglet.options['debug_gl', 'shadow_window'] = [False, False]
pyglet.graphics.vertexdomain.create_attribute_usage('v2f/stream')
pyglet.graphics.vertexdomain.create_attribute_usage('c3B/stream')
batch = pyglet.graphics.Batch()


class LSystemMeta(type):

    def __iter__(cls):
        ''' Iterate through each instance of LSystem class. '''
        return iter(cls._instances)

    def __getitem__(cls, n):
        if isinstance(n, int):
            return cls._instances[n]
        elif isinstance(n, tuple):
            return [getattr(cls, item, item) for item in n]
        elif isinstance(n, str):
            return [getattr(cls, n, n)]

    def __setattr__(cls, attr, value):
        ''' Set attr to class and it's instances. '''
        for fractal in cls._instances:
            setattr(fractal, attr, value)
        super().__setattr__(attr, value)

class LSystem(metaclass=LSystemMeta):
    _instances = []
    _queue = []

    def __init__(
            self,
            name,
            num_of_instances=1,
            iteration=4,
            r=None,
            g=None,
            b=None,
            draw_time=2.0,
            line_width=1.0,
            start_pos=None,
            translation = [[0.0, 0.0], [0.0, 0.0]],
            rotation=[0.0, 0.0],
            scale=[0.0, 20.0],
            color=[255.0, 0.0]):
        '''
        All parameters are optional.
        r, g, b are recommended to change
        :Parameters:
            name : string
                name of the lsystem (found in lsystem_data)
            num_of_instaces : int
                how many instances to be created
            iteration : int
            r : lambda x
            g : lambda x
            b : lambda x
                r, g, b are a lambda function with one varaible
                used to generate color sequence
            draw_time : float
                how long to draw fractal
            line_width : float
                in the domain (0, 7]
            start_pos : list / tuple
                start position; where fractal center should be
            ## translation, rotation, scale, and color are lists/tuples used to transform fractal
                initial value should be the right most position
                other values are added sequentially to the last position
            translation : list / tuple
                Two nested lists / tuples.
                First determines translation along the x-axis
                Second one the y-axis
            rotation : list / tuple
            scale : list / tuple
            color : list / tuple
                used to move colors
        '''
        LSystem._instances.append(self)
        setattr(LSystem, name, self)
        self.__dict__['_instances'] = [_LSystem_(name) for _ in range(num_of_instances)]

        self.name = name
        self.iteration = iteration
        self.r, self.g, self.b = r, g, b
        self.draw_time = draw_time
        self.line_width = line_width
        self.start_pos = start_pos

        self.translation = translation
        self.rotation = rotation
        self.scale = scale
        self.color = color

    def __setattr__(self, attr, value):
        ''' Every time an attribute is changed, afrotationfect sub classes. '''
        super().__setattr__(attr, value)
        if not attr in ['name', 'n']:
            if attr in ['start_pos', 'translation', 'rotation', 'scale', 'color']:
                # if true, the value must be stored as np.array for transformations
                try:
                    for obj in self._instances:
                        setattr(obj, attr, np.array(value, dtype=np.float_))
                except TypeError:
                    raise TypeError(f'{attr} cannot be {type(value)}')
            else:
                try:
                    for obj, i in zip(self._instances, value):
                        obj.__dict__[attr] = i
                except TypeError:
                    for obj in self._instances:
                        obj.__dict__[attr] = value

    def __str__(self):
        return f'{[obj for obj in self._instances]}'

    def __getitem__(self, n):
        return self._instances[n]

    def __iter__(self):
        self.n = 0
        return self
        return iter(self._instances)

    def __next__(self):
        if self.n >= len(self._instances):
            raise StopIteration
        self.n += 1
        return self._instances[self.n - 1]

    @classmethod
    def add_to_queue(cls, instance):
        cls._queue.append(instance)

    @classmethod
    def draw_all(cls, n=None):
        ''' Draw every instance of LSystem. '''
        for fractal in cls._instances:
            fractal.draw()
            fractal.reset(n)
        LSystem._queue.clear()

    def reset(self, n=None):
        if n is None:
            # clear draw queue and delete vertex list
            for fractal in LSystem._queue:
                for obj in fractal._instances:
                    obj.vertex_list.delete()
            LSystem._queue.clear()
        elif 0 <= n <= len(LSystem._queue):
            # keep n fractals on screen
            for obj in LSystem._queue.pop(0):
                obj.vertex_list.delete()

    def draw(self):
        ''' Draw fractal. '''
        LSystem._queue.append(self)
        if self.start_pos is None:
            # translate to center of window
            self.start_pos = [960, 540]

        # prepare each instace to draw
        for obj in self._instances:

            # create verts and rgb
            obj._set_iteration_()
            obj._set_rgb_()

            # translate by start_pos
            obj.verts += obj.start_pos
            obj._set_vertex_list_()

        window.run(self)


class _LSystem_:
    '''
    Base class for drawing fractals.
    No need to interact with this class
    LSystem provides all the necessary methods
    '''
    def __init__(self, name):
        self.name = name

    def __len__(self):
        return len(self.word)

    def __repr__(self):
        return f'''_LSystem_('{self.name}')'''

    def __str__(self):
        return f''''{self.name}' : {LSystem.info[self.name]}'''

    def _set_iteration_(self):
        '''Create verts for instance'''
        self.word = LSystem.info[self.name]['axiom']
        rules = LSystem.info[self.name]['rules']

        # grow word based on iteration
        for _ in range(self.iteration):
            self.word = ''.join(rules.get(char, char) for char in self.word)

        # look-up dic for generating theta based on word
        theta = np.radians(LSystem.info[self.name]['theta'])
        ops = {
            '-': -theta,
            '+': theta,
            '|': np.pi
        }

        # create array of +/- theta and pi values
        verts = np.array([ops.get(char, 0) for char in self.word], dtype=np.float_)
        verts = np.cumsum(verts)[:, np.newaxis]

        # take cos and sin of array and stack them
        verts = np.hstack((
            np.cos(verts),
            np.sin(verts)
        ))

        # sum across array to get vertices
        self.verts = np.cumsum(verts, axis=0)
        self.center = np.average(self.verts, axis=0)

    def _set_rgb_(self):
        ''' Create rgb sequence for coloring fractal. '''
        # create rgb array with length based on vertices
        # np.uint8 limits to values < 255 (rgb values)
        rgb = np.arange(len(self), dtype=np.uint8)[:, np.newaxis]
        if self.r is None: self.r = lambda x: x
        if self.g is None: self.g = lambda x: x
        if self.b is None: self.b = lambda x: x

        # apply lambda function and stack
        self.rgb = np.hstack((
            self.r(rgb),
            self.g(rgb),
            self.b(rgb)
        )).flatten()
        # print(len(self.rgb), len(self))

    def _set_vertex_list_(self):
        ''' Create vertex list using verts(vertices) and rgb(color). '''
        self.vertex_list = batch.add(
            len(self), pyglet.gl.GL_LINE_STRIP, None,
            ('v2f', self.verts.flatten()),
            ('c3B', self.rgb)
        )

    def _set_line_width_(self):
        '''Valid values are in range (0, 7]'''
        pyglet.gl.glLineWidth(self.line_width)

    def _rotate_(self):
        '''Rotate fractal about its center. '''
        # create translation matrix
        c, s = np.cos(self.rotation[-1]), np.sin(self.rotation[-1])
        translation_matrix = np.array([[c, -s], [s, c]], dtype=np.float_)

        # apply translation matrix, around its center
        verts = self.verts - self.center
        self.verts = verts.dot(translation_matrix) + self.center

    def _draw_(self):
        ''' Update values to draw. '''
        # transform fractal
        np.cumsum(self.translation, axis=1, out=self.translation)
        np.cumsum(self.rotation, out=self.rotation)
        np.cumsum(self.scale, out=self.scale)
        np.cumsum(self.color, out=self.color)

        # find center of fractal
        self.center = np.average(self.verts, axis=0)
        # min = np.min(self.verts, axis=0)
        # max = np.max(self.verts, axis=0)
        # self.center = (max + min) / 2
        self._rotate_()

        # update vertices and scale them relative to their center
        verts = (self.verts - self.center) * self.scale[-1] + self.center + self.translation[:, -1]

        self.vertex_list.vertices = verts.flatten()
        self.vertex_list.colors = self.rgb + self.color[-1].astype(np.uint8)
        self.vertex_list.draw(pyglet.gl.GL_LINE_STRIP)


class Window(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(fullscreen=True, vsync=False, *args, **kwargs)

    def run(self, instance):
        start_time = time()
        while time() - start_time < instance.draw_time:

            self.clear()
            for fractal in LSystem._queue:
                for obj in fractal._instances:
                    obj._set_line_width_()
                    obj._draw_()

            self.flip()
            self.dispatch_events()

    def on_key_press(self, symbol, modifier):
        ## future update to change lsystem based on keypress
        if symbol == pyglet.window.key.RIGHT:
            print('Next System')
        elif symbol == pyglet.window.key.LEFT:
            print('Prev System')
        else:
            self.close()

    @property
    def center(self):
        return np.array([self.width / 2, self.height / 2], dtype=np.float_)


def init(file='data.json'):
    '''
    Initialize everything.
    Read from json file to create dictionary
    of all lsystems available.
    '''
    with open(file, 'r') as f:
        info = sorted(json.load(f).items())
        LSystem.info = {k: v for (k, v) in info}

        for name in LSystem.info:
            LSystem(name)

    with open(file, 'w') as f:
        json.dump(LSystem.info, f, indent=4)


window = Window()

if __name__ == '__main__':
    init()

    LSystem.draw_time = 0.1
    LSystem.draw_all(2)

    # initialize LSystem wiith every lsystem with one instance each
    # for system in LSystem:
    #     fractal = LSystem(system.name, 1,
    #         iteration=3,
    #         scale=[0.0004, 0, -50],
    #         rotation=[0, (np.random.random()-.5)/100],
    #         r=lambda x: 255 - x,
    #         g=lambda x: x % 51 * 5,
    #         b=lambda x: x // 3,
    #         draw_time=3,
    #         line_width=7
    #     )

    # ----------------
    # way it should be:
    # LSystem['iteration'] = 3
    # LSystem['scale'] = 3
    # or:
    # LSystem.set(iteration=3, scale=3)
    # ----------------

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

        #for obj in fractal:
        #    print(obj)

        # fractal.draw()
        # fractal.reset(3)
    LSystem.draw_all(3)

window.on_close()


