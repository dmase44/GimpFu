
import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp


from gimpfu.adapters.item import GimpfuItem
from gimpfu.adapters.adapter_logger import AdapterLogger


'''
Not instantiable by itself, only inheritable.
No Author should/can use "d = gimp.Drawable" or "a = Drawable.foo"
In other words, private to GimpFu
'''


class GimpfuDrawable( GimpfuItem ) :
    '''
    Attributes common to subclasses Layer, Channel, Vectors.  See wrappable.py
    '''

    '''
    Notes on properties:
    offsets() is on Drawable but set_offset() is on Layer
    Is specially adapted below.
    '''

    @classmethod
    def DynamicWriteableAdaptedProperties(cls):
        return ('mode', 'name', 'lock_alpha' ) + super().DynamicWriteableAdaptedProperties()

    # inherits DynamicReadOnlyAdaptedProperties() from super

    @classmethod
    def DynamicTrueAdaptedProperties(cls):
        return ('height', 'width', 'has_alpha', 'is_rgb', ) + super().DynamicTrueAdaptedProperties()




    '''
    methods
    '''

    '''
    properties
    '''


    '''
    Simple adaption of callable to property, without renaming.
    '''
    """
    OLD now Dynamic
    @property
    def height(self):
        return self._adaptee.height()

    @property
    def width(self):
        return self._adaptee.width()

    @property
    def has_alpha(self):
        return self._adaptee.has_alpha()

    @property
    def is_rgb(self):
        return self._adaptee.is_rgb()
    """


    # special: adapt return values
    @property
    def mask_bounds(self):

        bounds = self._adaptee.mask_bounds()
        '''
        bounds returns (is_selection, x1, y1, x2, y2)
        is_selection value was never of any use,
        since the bounding box can be empty even if there is a selection.
        Discard is_selection
        '''
        result = bounds[1:]
        AdapterLogger.logger.debug(f"mask_bounds() returns {result}")
        return result
    # no setter


    # special: returns extra result: True
    @property
    def offsets(self):
        offsets = self._adaptee.offsets()
        # slice off leading True
        result = offsets[1:]
        return result
