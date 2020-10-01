import pyglet
import json
import math
import numpy as np
from time import time

pyglet.options['debug_gl', 'shadow_window'] = [False, False]
pyglet.graphics.vertexdomain.create_attribute_usage('v2f/stream')
pyglet.graphics.vertexdomain.create_attribute_usage('c3B/stream')
batch = pyglet.graphics.Batch()

def sort(file):
    with open(file, 'r') as f:
        result = json.load(f)
    with open(file, 'w') as f:
        json.dump(dict(sorted(result.items())), f, indent=4)
    return result


class _LSystem:
    def __init__(self, data, default):
        self.__dict__ = {**data, **default}
        self.theta = np.radians(self.theta)

    def __repr__(self):
        return f'_LSystem{self.axiom, self.rules, round(math.degrees(self.theta))}'
    __str__ = __repr__

    def _setup_(self):
        self._set_iteration_()
        self._set_rgb_()
        self.verts += self.start_pos
        self._set_vertex_list_()

    def _set_iteration_(self):
        # grow word
        self.word = self.axiom
        for _ in range(self.iteration):
            self.word = ''.join(self.rules.get(char, char) for char in self.word)

        # look-up dict
        operations = {
            '-': -self.theta,
            '+': self.theta,
            '|': math.pi
        }

        # define verts
        verts = np.array([operations.get(char, 0) for char in self.word], dtype=np.float_)
        verts = np.cumsum(verts)[:, np.newaxis]
        verts = np.hstack((np.cos(verts), np.sin(verts)))

        # sum across array to get vertices
        self.verts = np.cumsum(verts, axis=0)
        self.center = np.average(self.verts, axis=0)

    def _set_rgb_(self):
        rgb = np.arange(len(self.word), dtype=np.uint8)[:, np.newaxis]

        # apply lambda function
        self.rgb = np.hstack((
            self.r(rgb),
            self.g(rgb),
            self.b(rgb)
        )).flatten()

    def _set_vertex_list_(self):
        self.vertex_list = batch.add(
            len(self.word), pyglet.gl.GL_LINE_STRIP, None,
            ('v2f', self.verts.flatten()),
            ('c3B', self.rgb)
        )

    def _set_line_width_(self):
        pyglet.gl.glLineWidth(self.line_width)

    def _rotate_(self):
        # translation matrix
        c, s = math.cos(self.rotation[-1]), np.sin(self.rotation[-1])
        translation_matrix = np.array([[c, -s], [s, c]], dtype=np.float_)

        # apply translation matrix around fractal center
        verts = self.verts - self.center
        self.verts = verts.dot(translation_matrix) + self.center

    def _draw_(self):
        # transform fractal
        np.cumsum(self.translation, axis=1, out=self.translation)
        np.cumsum(self.rotation, out=self.rotation)
        np.cumsum(self.scale, out=self.scale)
        np.cumsum(self.color, out=self.color)

        self.center = np.average(self.verts, axis=0)
        self._rotate_()

        # update vertices and scale them relative to their center
        verts = (self.verts - self.center) * self.scale[-1] + self.center + self.translation[:, -1]
        self.vertex_list.vertices = verts.flatten()
        self.vertex_list.colors = self.rgb + self.color[-1].astype(np.uint8)
        self.vertex_list.draw(pyglet.gl.GL_LINE_STRIP)


class LSystem(pyglet.window.Window):
    def __init__(self, default='default', **kwargs):
        super().__init__(vsync=False, **kwargs)

        self.default = sort('property.json')[default]
        self.default['start_pos'] = self.default['start_pos'] or self.center

        self.wrap('r', 'g', 'b', wrap=lambda func: eval('lambda x:' + func))
        self.wrap('start_pos', 'translation', 'rotation', 'scale', 'color', wrap=np.array)

        self.instances = {
            name: _LSystem(system, self.default)
            for (name, system) in sort('data.json').items()
        }

    def __iter__(self):
        return iter(self.instances)

    def __setitem__(self, key, value):
        if isinstance(key, str):
            self[key] = value

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.instances.get(key)
        return (self.instances.get(k) for k in key)

    def wrap(self, *keys, wrap):
        for key in keys:
            self.default[key] = wrap(self.default[key])

    def setup(self):
        for instance in self.instances.values():
            instance._setup_()

    def __call__(self, *instances, draw_time=1):
        start_time = time()
        while time() - start_time < draw_time:

            # self.clear()
            for instance in self[instances]:
                instance._set_line_width_()
                instance._draw_()
            # self.flip()

    def on_key_press(self, symbol, modifier):
        self.close()

    @property
    def center(self):
        return [self.width / 2, self.height / 2]


if __name__ == '__main__':
    lsystem = LSystem(fullscreen=True)
    lsystem.setup()
    lsystem()
