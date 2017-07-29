#
# Part of p5: A Python package based on Processing
# Copyright (C) 2017 Abhik Pal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""Provides an Object Oriented interface to OpenGL."""

from abc import ABCMeta, abstractmethod
import ctypes as ct

from pyglet import gl

_buffer_type_map = {
    'data': gl.GL_ARRAY_BUFFER,
    'elem': gl.GL_ELEMENT_ARRAY_BUFFER
}

_dtype_map = {
    'float': (gl.GLfloat, gl.GL_FLOAT),
    'uint': (gl.GLuint, gl.GL_UNSIGNED_INT)
}

_mode_map = {
    'POINTS': gl.GL_POINTS,
    'LINE_STRIP': gl.GL_LINE_STRIP,
    'LINE_LOOP': gl.GL_LINE_LOOP,
    'TRIANGLES': gl.GL_TRIANGLES,
    'TRIANGLE_FAN': gl.GL_TRIANGLE_FAN,
}

class GLObject(metaclass=ABCMeta):
    """An abstract class for GL objects."""
    @abstractmethod
    def activate(self):
        """Activate the object."""
        pass

    @abstractmethod
    def deactivate(self):
        """Deactivate the object."""
        pass

    @abstractmethod
    def delete(self):
        """Delete the object."""
        pass

    @property
    def id(self):
        return self._id

class VertexBuffer(GLObject):
    """Encapsulates an OpenGL VertexBuffer.
    """
    def __init__(self, dtype, data=None, buffer_type='data'):
        self.buffer_type = buffer_type
        self._type = _buffer_type_map[buffer_type]

        self.data_type = dtype
        self._dtype, self._dtype_const = _dtype_map[dtype]

        self._data = None

        self._id = gl.GLuint()
        gl.glGenBuffers(1, ct.pointer(self._id))

        if data is not None:
            self.data = data

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        value_typed = (self._dtype * len(value))(*value)
        self.activate()
        gl.glBufferData(self._type, ct.sizeof(value_typed),
                        value_typed, gl.GL_STATIC_DRAW)
        self.deactivate()
        self._data = value

    def activate(self):
        """Activate the current buffer.
        """
        gl.glBindBuffer(self._type, self._id)

    def deactivate(self):
        """Deactivate the current buffer.
        """
        gl.glBindBuffer(self._type, 0)

    @staticmethod
    def deactivate_all():
        """Deactivate all buffers.
        """
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

    def draw(self, mode):
        draw_mode = _mode_map[mode]
        self.activate()
        if self.buffer_type == 'elem':
            gl.glDrawElements(draw_mode, len(self.data), self._dtype_const, 0)
        else:
            raise ValueError("cannot draw a data buffer.")
        self.deactivate()

    def delete(self):
        """Delete the current buffer."""
        gl.glDeleteBuffers(1, self._id)

class Texture(GLObject):
    def __init__(self, width, height):
        self._id = gl.GLuint()
        gl.glGenTextures(1, ct.pointer(self._id))
        self.width = width
        self.height = height
        self._data = None

    @property
    def data(self):
        return self._data

    def _set_texture_parameters(self):
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_LINEAR)

    @data.setter
    def data(self, value):
        self.activate()
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, self.width,
                        self.height, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, value)
        self._set_texture_parameters()
        self._data = value
        self.deactivate()

    def activate(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._id)

    def deactivate(self):
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    def delete(self):
        gl.glDeleteTextures(1, ct.pointer(self._id))

class DummyFrameBuffer:
    """A dummy FrameBuffer.

    For machines where we don't have actual FrameBuffer support.
    """
    def __init__(self, *args, **kwargs):
        pass
    def activate(self, *args, **kwargs):
        pass
    def deactivate(self, *args, **kwargs):
        pass
    def attach_texture(self, *args, **kwargs):
        pass
    def delete(self, *args, **kwargs):
        pass

class FrameBuffer(GLObject):
    """Encapsulates an OpenGL FrameBuffer."""
    def __init__(self):
        self._id = Gluint()
        gl.glGenFramebuffersEXT(1, pointer(self._id))

        self._check_completion_status()

    def _check_completion_status(self):
        """Check the completion status of the framebuffer.

        :raises Exception: When the frame buffer is incomplete.
        """
        status = gl.glCheckFramebufferStatusEXT(gl.GL_FRAMEBUFFER_EXT)
        if status != gl.GL_FRAMEBUFFER_COMPLETE_EXT:
            msg = "ERR {}: FrameBuffer could not be created.".format(status)
            raise Exception(msg)

    def activate(self):
        """Activate the current framebuffer."""
        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, self._id)

    def deactivate(self):
        """Deactivate the current framebuffer."""
        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, self._id)

    def attach_texture(self, texture):
        self.activate()
        gl.glFramebufferTexture2DEXT(gl.GL_FRAMEBUFFER_EXT,
                                     gl.GL_COLOR_ATTACHMENT0_EXT,
                                     gl.GL_TEXTURE_2D, texture.id, 0)
        self.deactivate()

    def delete(self):
        """Delete the current frame buffer."""
        gl.glDeleteFramebuffersEXT(self._id)

    def __del__(self):
        self.delete()
