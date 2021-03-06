#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Unicorn HAT HD library.

Drive the 16x16 RGB pixel Pimoroni Unicorn HAT HD
over SPI from a Raspberry Pi or compatible platform.

"""

import colorsys
import time


try:
    import spidev
except ImportError:
    raise ImportError('This library requires the spidev module\nInstall with: sudo pip install spidev')

try:
    import numpy
except ImportError:
    raise ImportError('This library requires the numpy module\nInstall with: sudo pip install numpy')


__version__ = '0.0.4'

_SOF = 0x72
_DELAY = 1.0 / 120

WIDTH = 16
HEIGHT = 16

PHAT = None
HAT = None
PHAT_VERTICAL = None
AUTO = None
PANEL_SHAPE = (16, 16)

_rotation = 0
_brightness = 0.5
_buffer_width = WIDTH
_buffer_height = HEIGHT
_addressing_enabled = False
_buf = numpy.zeros((_buffer_width, _buffer_height, 3), dtype=int)

COLORS = {
    'red': (255, 0, 0),
    'lime': (0, 255, 0),
    'blue': (0, 0, 255),
    'yellow': (255, 255, 0),
    'magenta': (255, 0, 255),
    'cyan': (0, 255, 255),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'gray': (127, 127, 127),
    'grey': (127, 127, 127),
    'silver': (192, 192, 192),
    'maroon': (128, 0, 0),
    'olive': (128, 128, 0),
    'green': (0, 128, 0),
    'teal': (0, 128, 128),
    'navy': (0, 0, 128),
    'orange': (255, 165, 0),
    'gold': (255, 215, 0),
    'purple': (128, 0, 128),
    'indigo': (75, 0, 130)
}

class Display:
    """Represents a single display in a multi-display chain.

    Contains the coordinates for the slice of the pixel buffer
    which should be visible on this particular display.

    """

    def __init__(self, enabled, x, y, rotation):
        """Initialise display.

        :param enabled: True/False to indicate if this display is enabled
        :param x: x offset of display portion in buffer
        :param y: y offset of display portion in buffer
        :param rotation: rotation of display

        """
        self.enabled = enabled
        self.update(x, y, rotation)

    def update(self, x, y, rotation):
        """Update display position.

        :param x: x offset of display portion in buffer
        :param y: y offset of display portion in buffer
        :param rotation: rotation of display

        """
        self.x = x
        self.y = y
        self.rotation = rotation

    def get_buffer_window(self, source):
        """Grab the correct portion of the supplied buffer for this display.

        :param source: source buffer, should be a numpy array

        """
        view = source[self.x:self.x + PANEL_SHAPE[0], self.y:self.y + PANEL_SHAPE[1]]
        return numpy.rot90(view, self.rotation + 1)

_displays = [Display(False, 0, 0, 0) for _ in range(8)]
is_setup = False

def setup():
    """Initialize Unicorn HAT HD."""
    global _spi, _buf, is_setup

    if is_setup:
        return

    _spi = spidev.SpiDev()
    _spi.open(0, 0)
    _spi.max_speed_hz = 9000000

    is_setup = True

def enable_addressing(enabled=True):
    """Enable multi-panel addressing support (for Ubercorn)."""
    global _addressing_enabled
    _addressing_enabled = enabled

def setup_buffer(width, height):
    """Set up the internal pixel buffer.

    :param width: width of buffer, ideally in multiples of 16
    :param height: height of buffer, ideally in multiples of 16

    """
    global _buffer_width, _buffer_height, _buf

    _buffer_width = width
    _buffer_height = height
    _buf = numpy.zeros((_buffer_width, _buffer_height, 3), dtype=int)

def enable_display(address, enabled=True):
    """Enable a single display in the chain.

    :param address: address of the display from 0 to 7
    :param enabled: True/False to indicate display is enabled

    """
    _displays[address].enabled = enabled

def setup_display(address, x, y, rotation):
    """Configure a single display in the chain.

    :param x: x offset of display portion in buffer
    :param y: y offset of display portion in buffer
    :param rotation: rotation of display

    """
    _displays[address].update(x, y, rotation)
    enable_display(address)

def set_brightness(b):
    """Set the display brightness between 0.0 and 1.0.

    :param b: Brightness from 0.0 to 1.0 (default 0.5)

    """
    global _brightness

    _brightness = b

def set_rotation(r):
    """Set the display rotation in degrees.

    Actual rotation will be snapped to the nearest 90 degrees.

    """
    global _rotation

    _rotation = int(round(r / 90.0))

def get_rotation():
    """Return the display rotation in degrees."""
    return _rotation * 90

def set_layout(pixel_map=None):
    """Do nothing, for library compatibility with Unicorn HAT."""
    pass

def set_all(r, g=None, b=None):
    """Set all pixels to RGB colour.

    :param r: Amount of red from 0 to 255
    :param g: Amount of green from 0 to 255
    :param b: Amount of blue from 0 to 255

    """

    if type(r) is tuple:
        r, g, b = r

    elif type(r) is str:
        try:
            r, g, b = COLORS[r.lower()]

        except KeyError:
            raise ValueError('Invalid color!')

    _buf[:] = r, g, b

def set_pixel(x, y, r, g=None, b=None):
    """Set a single pixel to RGB colour.

    :param x: Horizontal position from 0 to 15
    :param y: Veritcal position from 0 to 15
    :param r: Amount of red from 0 to 255
    :param g: Amount of green from 0 to 255
    :param b: Amount of blue from 0 to 255

    """
    if type(r) is tuple:
        r, g, b = r

    elif type(r) is str:
        try:
            r, g, b = COLORS[r.lower()]

        except KeyError:
            raise ValueError('Invalid color!')

    _buf[int(x)][int(y)] = r, g, b

def safe_set_pixel(x, y, r, g=None, b=None):
    if x >= 0 and y >= 0 and  x < WIDTH and y < HEIGHT:
        set_pixel(x, y, r, g, b)

def draw_circle(x, y, radius, r, g=None, b=None):
    #swap x and y
    x0 = y
    y0 = x
    radius = max(0, radius)
    f = 1 - radius
    ddf_x = 1
    ddf_y = -2 * radius
    x = 0
    y = radius
    safe_set_pixel(x0, y0 + radius, r, g, b)
    safe_set_pixel(x0, y0 - radius, r, g, b)
    safe_set_pixel(x0 + radius, y0, r, g, b)
    safe_set_pixel(x0 - radius, y0, r, g, b)
 
    while x < y:
        if f >= 0: 
            y -= 1
            ddf_y += 2
            f += ddf_y
        x += 1
        ddf_x += 2
        f += ddf_x    
        safe_set_pixel(x0 + x, y0 + y, r, g, b)
        safe_set_pixel(x0 - x, y0 + y, r, g, b)
        safe_set_pixel(x0 + x, y0 - y, r, g, b)
        safe_set_pixel(x0 - x, y0 - y, r, g, b)
        safe_set_pixel(x0 + y, y0 + x, r, g, b)
        safe_set_pixel(x0 - y, y0 + x, r, g, b)
        safe_set_pixel(x0 + y, y0 - x, r, g, b)
        safe_set_pixel(x0 - y, y0 - x, r, g, b)
        
def draw_line(x0, y0, x1, y1, r, g=None, b=None):
    """Draw a line from position x0, y0 to position x1, y1

    :param x0: Horizontal starting position from 0 to 15
    :param y0: Vertical starting position from 0 to 15
    :param x1: Horizontal ending position from 0 to 15
    :param y1: vertical ending position from 0 to 15
    :param r: Amount of red from 0 to 255
    :param g: Amount of green from 0 to 255
    :param b: Amount of blue from 0 to 255
    """
    def _plotLineLow(x0, y0, x1, y1, r, g, b):
        dx = x1 - x0
        dy = y1 - y0
        yi = 1
        if dy < 0:
            yi = -1
            dy = -dy
        D = 2*dy - dx
        y = y0
    
        for x in range(x0, x1):
            safe_set_pixel(x, y, r, g, b)
            if D > 0:
                y = y + yi
                D = D - 2*dx
            D = D + 2*dy

    def _plotLineHigh(x0, y0, x1, y1, r, g, b):
        dx = x1 - x0
        dy = y1 - y0
        xi = 1
        if dx < 0:
            xi = -1
            dx = -dx
        D = 2*dx - dy
        x = x0
    
        for y in range(y0, y1):
            safe_set_pixel(x, y, r, g, b)
            if D > 0:
                x = x + xi
                D = D - 2*dy
            D = D + 2*dx

    if abs(y1 - y0) < abs(x1 - x0):
        if x0 > x1:
            _plotLineLow(x1, y1, x0, y0, r, g, b)
        else:
            _plotLineLow(x0, y0, x1, y1, r, g, b)
    elif y0 > y1:
        _plotLineHigh(x1, y1, x0, y0, r, g, b)
    else:
        _plotLineHigh(x0, y0, x1, y1, r, g, b)

    safe_set_pixel(x0, y0, r, g, b)
    safe_set_pixel(x1, y1, r, g, b)

def draw_rect(x, y, w, h, r, g=None, b=None):
    """Draw an unfilled rectangle from position x, y 
    with width w and height h

    :param x: Horizontal position from 0 to 15
    :param y: Veritcal position from 0 to 15
    :param w: Width of rectangle
    :param h: Height of rectangle
    :param r: Amount of red from 0 to 255
    :param g: Amount of green from 0 to 255
    :param b: Amount of blue from 0 to 255
    """
    x1 = x + h
    y1 = y + w
    draw_line(x, y, x1, y, r, g, b)
    draw_line(x1, y, x1, y1, r, g, b)
    draw_line(x1, y1, x, y1, r, g, b)
    draw_line(x, y1, x, y, r, g, b)

def fill_rect(x, y, w, h, r, g=None, b=None):
    """Draw a filled rectangle from position x, y 
    with width w and height h

    :param x: Horizontal position from 0 to 15
    :param y: Veritcal position from 0 to 15
    :param w: Width of filled rectangle
    :param h: Height of filled rectangle
    :param r: Amount of red from 0 to 255
    :param g: Amount of green from 0 to 255
    :param b: Amount of blue from 0 to 255
    """
    x1 = x + h
    for i in range(abs(w+1)):
        draw_line(x, y+i, x1, y+i, r, g, b)

def set_pixel_hsv(x, y, h, s=1.0, v=1.0):
    """Set a single pixel to a colour using HSV.

    :param x: Horizontal position from 0 to 15
    :param y: Veritcal position from 0 to 15
    :param h: Hue from 0.0 to 1.0 ( IE: degrees around hue wheel/360.0 )
    :param s: Saturation from 0.0 to 1.0
    :param v: Value (also known as brightness) from 0.0 to 1.0

    """
    r, g, b = [int(n * 255) for n in colorsys.hsv_to_rgb(h, s, v)]
    set_pixel(x, y, r, g, b)

def safe_set_pixel_hsv(x, y, h, s=1.0, v=1.0):
    """Set a single pixel to a colour using HSV
    (This version will not cause an error if x or y
    is out of range.)
    """
    if x >= 0 and y >= 0 and  x < WIDTH and y < HEIGHT:
        set_pixel_hsv(x, y, h, s, v)    

def get_pixel(x, y):
    """Get pixel colour in RGB as a tuple.

    :param x: Horizontal position from 0 to 15
    :param y: Veritcal position from 0 to 15

    """
    return tuple(_buf[int(x)][int(y)])

def shade_pixels(shader):
    """Set all pixels to a colour determined by a shader function.

    :param shader: function that accepts x/y position and returns an r,g,b tuple.

    """
    for x in range(WIDTH):
        for y in range(HEIGHT):
            r, g, b = shader(x, y)
            set_pixel(x, y, r, g, b)

def swap_pixels(x0, y0, x1, y1):
    """Swap the r, g, b values of pixels at positions x0,y0 and x1,y1    
    """
    p0 = get_pixel(x0, y0)
    p1 = get_pixel(x1, y1)
    safe_set_pixel(x0, y0, p1)
    safe_set_pixel(x1, y1, p0)

def get_pixels():
    """Return entire buffer."""
    return _buf
   
def set_pixels(buf):
    """Set entire buffer"""
    _buf = buf
    
def hscroll(dx):
    """Scroll entire buffer horizontally"""
    _buf[0:] = numpy.roll(_buf[0:], dx, axis=1)
    
def vscroll(dy):
    """Scroll entire buffer vertically"""
    _buf[0:] = numpy.roll(_buf[0:], dy, axis=0)

def get_shape():
    """Return the shape (width, height) of the display."""
    return _buffer_width, _buffer_height

def clear():
    """Clear the buffer."""
    _buf.fill(0)

def off():
    """Clear the buffer and immediately update Unicorn HAT HD.

    Turns off all pixels.

    """
    clear()
    show()

def show():
    """Output the contents of the buffer to Unicorn HAT HD."""
    setup()
    if _addressing_enabled:
        for address in range(8):
            display = _displays[address]
            if display.enabled:
                if _buffer_width == _buffer_height or _rotation in [0, 2]:
                    window = display.get_buffer_window(numpy.rot90(_buf, _rotation))
                else:
                    window = display.get_buffer_window(numpy.rot90(_buf, _rotation))

                _spi.xfer2([_SOF + 1 + address] + (window.reshape(768) * _brightness).astype(numpy.uint8).tolist())
                time.sleep(_DELAY)
    else:
        _spi.xfer2([_SOF] + (numpy.rot90(_buf, _rotation).reshape(768) * _brightness).astype(numpy.uint8).tolist())

    time.sleep(_DELAY)

rotation = set_rotation
brightness = set_brightness
