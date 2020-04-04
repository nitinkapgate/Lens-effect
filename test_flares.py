"""
MIT License

Copyright (c) 2019 Yoann Berenguer

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


# PROJECT:


# TECHNIQUE:


# EFFECTS


REQUIREMENT:
- python > 3.0
- numpy arrays
- pygame with SDL version 1.2 (SDL version 2 untested)
  Cython
- A compiler such visual studio, MSVC, CGYWIN setup correctly
  on your system


BUILDING PROJECT:
Use the following command:
C:\>python setup_lights.py build_ext --inplace




"""

import timeit
import os

# NUMPY IS REQUIRED
try:
    import numpy
    from numpy import ndarray, zeros, empty, uint8, int32, float64, float32, dstack, full, ones, \
        asarray, ascontiguousarray
except ImportError:
    raise ImportError("\n<numpy> library is missing on your system."
                      "\nTry: \n   C:\\pip install numpy on a window command prompt.")

# PYGAME IS REQUIRED
try:
    import pygame
    from pygame import Color, Surface, SRCALPHA, RLEACCEL, BufferProxy, gfxdraw
    from pygame.surfarray import pixels3d, array_alpha, pixels_alpha, array3d
    from pygame.image import frombuffer

except ImportError:
    raise ImportError("\n<Pygame> library is missing on your system."
                      "\nTry: \n   C:\\pip install pygame on a window command prompt.")

try:
    import FLARES
    from FLARES import create_flare_sprite, make_vector2d, \
        LayeredUpdatesModified, second_flares, polygon, get_angle, display_flare_sprite
except ImportError:
    print("\nHave you build the project?"
          "\nC:>python setup_flare.py build_ext --inplace")

try:
    import bloom
    from bloom import bloom_effect_array
except ImportError:
    print("\n library bloom is missing on your system.")


# ALL SHARE CONSTANT(s) GOES HERE
class GL:
    TIME_PASSED_SECONDS = 0
    All = 0
    screenrect = 0


AVG_FPS = []

SCREENRECT = pygame.Rect(0, 0, 500, 500)
GL.screenrect = SCREENRECT

os.environ['SDL_VIDEODRIVER'] = 'windib'

pygame.display.init()
SCREEN = pygame.display.set_mode(SCREENRECT.size, pygame.SWSURFACE, 32)
SCREEN.set_alpha(None)
pygame.init()
pygame.mixer.pre_init(44100, 16, 2, 4095)
# globalisation
clock = pygame.time.Clock()
All = LayeredUpdatesModified()
GL.All = All
GL.SCREEN = SCREEN


# ************************* TEXTURE ********************************
# LOAD ALL THE LENS AND FLARE TEXTURES
STOP_GAME = False
FRAME = 0
BCK1 = pygame.image.load('A1.jpg').convert(32, pygame.RLEACCEL)
BCK1 = pygame.transform.smoothscale(BCK1, (SCREENRECT.w, SCREENRECT.h))
BCK1.set_alpha(None)

# SUB FLARES
TEXTURE = pygame.image.load('Assets\\Untitled3.png').convert(24)
TEXTURE = pygame.transform.smoothscale(TEXTURE, (100, 100))
TEXTURE.set_colorkey((0, 0, 0, 0), pygame.RLEACCEL)

TEXTURE1 = pygame.image.load('Assets\\Untitled1.png').convert(24)
TEXTURE1 = pygame.transform.smoothscale(TEXTURE1, (100, 100))
TEXTURE1.set_colorkey((0, 0, 0, 0), pygame.RLEACCEL)

# GLARE SPRITE
TEXTURE2 = pygame.image.load('Assets\\untitled7.png').convert(24)
TEXTURE2 = pygame.transform.smoothscale(TEXTURE2, (256, 256))
TEXTURE2.set_colorkey((0, 0, 0, 0), pygame.RLEACCEL)

# SPRITE DISPLAY AT THE END OF THE VECTOR
TEXTURE3 = pygame.image.load('Assets\\untitled8.png').convert(24)
TEXTURE3 = pygame.transform.smoothscale(TEXTURE3, (256, 256))
TEXTURE3.set_colorkey((0, 0, 0, 0), pygame.RLEACCEL)

# ********************************************************************

# SPRITE OF THE STAR CAUSING THE FLARE EFFECT
STAR_BURST = pygame.image.load('Assets\\Untitled5.png').convert(24)
STAR_BURST.set_colorkey((0, 0, 0, 0), pygame.RLEACCEL)
w, h = STAR_BURST.get_size()
# STAR SIZE TIME 4 TO INCREASE BRIGHTNESS
STAR_BURST3x = pygame.transform.smoothscale(
    STAR_BURST.copy(), (w * 3, h * 3))

STAR_BURST3x = STAR_BURST3x.convert(24)

# CREATE A BLOOM EFFECT (INCREASE BRIGHTNESS)
A = pygame.transform.smoothscale(STAR_BURST3x, (w * 3, h * 3))
STAR_BURST3x = bloom_effect_array(A, 0, smooth_=1)

# MOUSE POSITION INITIALISATION
mouse_pos = [0, 0]

VECTOR = pygame.math.Vector2(0, 0)


# BLUE STAR POSITION ONTO THE SCREEN (CENTRE OF THE EFFECT)
FLARE_POSITION = pygame.math.Vector2(280, 120)


# GROUP USED FOR REFERENCING ALL THE SUB-FLARES.
# THE GROUP CONTAINS OBJECT WITH FOLLOWING ATTRIBUTES
# FLARES =[[SURFACE, DISTANCE], [...] ]
# SURFACE  : FLARE TEXTURE
# DISTANCE : DISTANCE FROM THE CENTER (FLOAT).
# OBJECT SIZE WILL CHANGE ACCORDING TO POSITION/DISTANCE FROM THE CENTRE.
# WE COULD HAVE USED A PYGAME.SPRITE.GROUP INSTEAD, BUT THIS OFFER BETTER
# PERFORMANCES.
FLARES = []

# CHILD FLARE(s) GROUP (SPRITE LIST)
# THIS IS NO A PYGAME.SPRITE.GROUP
CHILD = []

# CREATE AN OCTAGON (SECOND FLARE POLYGON)
# AT THIS STAGE THE POLYGON IS EMPTY (NO TEXTURE)
# OCTAGON IS A NUMPY NDARRAY SHAPE (W, H)
octagon = polygon()

# REFERENCE ALL SECOND FLARE TEXTURE WHOM DOES NOT NEED
# TO BE APPLY TO THE POLYGON SUCH AS TEXTURE2.
# THOSE TEXTURE ARE ALREADY FINALIZED AND JUST NEED TO BE
# BLIT ALONG THE LENS VECTOR DIRECTION
exc = [TEXTURE2]

# CREATE SUB-FLARE(s)
# FIRST ARGUMENT (TEXTURE) REPRESENT THE TEXTURE BLIT
# TO THE POLYGON. make_vector2d IS A FUNCTION THAT CONVERT
# PYGAME.MATH.VECTOR2 INTO C EQUIVALENT VECTOR OBJECT.
# 0.8 AND 1.2 ARE MIN AMD MAX OF THE RANDOMIZE VALUE USED
# FOR RESIZING THE POLYGON. NOTHING IS MORE BORING THAT
# POLYGON WITH EXACT SAME SIZES.

# DRAW POLYGON FLARES (TEXTURE & TEXTURE HAVE DIFFERENT TRANSPARENCY LEVEL)
# ALSO INSERT POLYGON INTO THE PYTHON LIST FLARES
for r in range(20):
    FLARES.append(second_flares(TEXTURE, octagon.copy(),
                                make_vector2d(FLARE_POSITION), 0.8, 1.2, exc))
for r in range(5):
    FLARES.append(second_flares(TEXTURE1, octagon.copy(),
                                make_vector2d(FLARE_POSITION), 0.8, 1.2, exc))
# DRAW GLARES
for r in range(5):
    FLARES.append(second_flares(TEXTURE2, octagon.copy(),
                                make_vector2d(FLARE_POSITION), 0.8, 1.2, exc))

# GO TROUGH THE LIST FLARES AND CREATE FLARES SPRITES.
# THE SPRITE ARE INSERTED INTO THE PYTHON LIST CHILD
for flares in FLARES:
    create_flare_sprite(
        images_=flares[0], distance_=flares[1], vector_=VECTOR,
        position_=FLARE_POSITION, layer_=0, gl_=GL,
        child_group_=CHILD, blend_=pygame.BLEND_RGB_ADD, event_type='CHILD', delete_=False)

# SPRITE DISPLAY AT THE END OF THE VECTOR
create_flare_sprite(
        images_=TEXTURE3, distance_=2.0, vector_=VECTOR,
        position_=FLARE_POSITION, layer_=0, gl_=GL,
        child_group_=CHILD, blend_=pygame.BLEND_RGB_ADD, event_type='CHILD', delete_=False)

# BLUE BRIGHT STAR
create_flare_sprite(
        images_=STAR_BURST, distance_=0.5, vector_=VECTOR,
        position_=FLARE_POSITION, layer_=0, gl_=GL,
        child_group_=CHILD, blend_=pygame.BLEND_RGB_ADD, event_type='PARENT', delete_=False)


# MAIN LOOP
screendump = 0
while not STOP_GAME:

    pygame.event.pump()

    for event in pygame.event.get():

        keys = pygame.key.get_pressed()

        if keys[pygame.K_ESCAPE]:
            STOP_GAME = True

        # screenshots
        elif keys[pygame.K_F8]:
            pygame.image.save(SCREEN, 'Assets\\Screenshot\\Screendump'
                              + str(screendump) + '.png')
            screendump += 1

        if event.type == pygame.MOUSEMOTION:
            mouse_pos = pygame.mouse.get_pos()

            # VECTOR IS A PYGAME.MATH.VECTOR2 TYPE
            # VECTOR GIVEN BETWEEN THE MOUSE CURSOR AND THE CENTRE
            # OF THE BLUE STAR
            VECTOR = get_angle(
                make_vector2d(FLARE_POSITION),
                make_vector2d(pygame.math.Vector2(mouse_pos[0], mouse_pos[1])))

    # DISPLAY THE BACKGROUND IMAGE
    SCREEN.blit(BCK1, (0, 0))

    # BLIT ALL THE SPRITE ONTO THE BACKGROUND
    # CHECK METHOD display_flare_sprite FOR MORE DETAILS
    display_flare_sprite(CHILD, STAR_BURST, STAR_BURST3x, GL, VECTOR)

    # WE DO NOT NEED TO UPDATE
    # SPRITE DOES NOT BELONG TO PYGAME GROUP
    # All.update()
    All.draw(SCREEN)

    # DISPLAY CHANGES
    pygame.display.flip()

    TIME_PASSED_SECONDS = clock.tick_busy_loop(400)
    GL.TIME_PASSED_SECONDS = TIME_PASSED_SECONDS
    avg_fps = clock.get_fps()
    print(avg_fps, 1000/(avg_fps + 0.001))

    FRAME += 1

pygame.quit()