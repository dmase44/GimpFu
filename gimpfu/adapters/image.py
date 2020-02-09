

import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp

# from adaption import adapter
#from adaption import adapter
#from adapter import Adapter
#from adaption.adapter import Adapter

# absolute from SYSPATH that points to top of gimpfu package
from adaption.adapter import Adapter

#from gimpfu_property import GimpfuProperty, GimpfuProperty2

'''

Adapts (wraps) Gimp.Image.

Constructor appears in GimpFu plugin code as e.g. : gimp.Image(w, h, RGB)
I.E. an attribute of gimp instance (see gimpfu_gimp.py.)

In PyGimp v2, similar concept implemented by pygimp-image.c
Since v3, implemented in Python using GI.

Method kinds:
Most have an identical signature method in Gimp.Image. (delegated)
Some have changed signature here, but same action as in Gimp.Image. (convenience)
Some are unique to PyGimp, not present in Gimp.Image. (augment)
    - methods
    - properties (data members)
    TODO do we need to wrap property get/set
'''






class GimpfuImage( Adapter ) :

    # classmethods needed by Adapter
    '''
    Notes:
    filename is NOT a canonical property of Image, at least in v3
    TODO active_layer should be
    '''
    @classmethod
    def DynamicWriteableAdaptedProperties(cls):
        return ( )

    @classmethod
    def DynamicReadOnlyAdaptedProperties(cls):
        return ('selection', )

    @classmethod
    def DynamicTrueAdaptedProperties(cls):
        return ('width', 'height')


    '''
    Constructor exported to Gimpfu authors.
    Called internally for existing images as GimpfuImage(None, None, None, adaptee)

    See SO "How to overload __init__ method based on argument type?"
    '''
    def __init__(self, width=None, height=None, image_mode=None, adaptee=None):
        '''Initialize  GimpfuImage from attribute values OR instance of Gimp.Image. '''
        if width is None:
            final_adaptee = adaptee
        else:
            # Gimp constructor named "new"
            print("Calling Gimp.Image.new with width", width)
            final_adaptee = Gimp.Image.new(width, height, image_mode)

        # super is Adaper, and it stores adaptee
        super().__init__(final_adaptee)

        # TODO WIP
        #self.filename = GimpfuProperty(final_adaptee, "filename")

        # self.filename = None is not correct, because self.filename is a property of each instance


    def adaptee(self):
        ''' Getter for private _adaptee '''
        # Handled by super Adaptor
        result = self._adaptee
        print("adaptee getter returns:", result)
        return result



    # OLD filename = GimpfuProperty2("filename")

    '''
    WIP
    Overload constructors using class methods.
    # Hidden constructor
    @classmethod
    def fromAdaptee(cls, adaptee):
         "Initialize GimpfuImage from attribute values"

         return cls(data
    '''


    # Methods we specialize


    # Special: allow optional args
    def insert_layer(self, layer, parent=None, position=-1):
        print("insert_layer called")

        # Note that first arg to Gimp comes from self
        success = self._adaptee.insert_layer(layer.unwrap(), parent, position)
        if not success:
            raise Exception("Failed insert_layer")



    # Properties we specialize
    # In fact GI Gimp does not have property semantics?


    @property
    def layers(self):
        # avoid circular import, import when needed
        from adaption.marshal import Marshal

        '''
        Override:
        - to insure returned objects are wrapped ???
        - because the Gimp name is get_layers

        Typical use by authors: position=img.layers.index(drawable) + 1
        And then the result goes out of scope quickly.
        But note that the wrapped item in the list
        won't be equal to other wrappers of the same Gimp.Layer
        UNLESS we also override equality operator for wrapper.

        !!! If you break this, the error is "AttributeError: Image has no attr layers"
        '''
        print("layers property accessed")
        layer_list = self._adaptee.get_layers()
        result_list = []
        for layer in layer_list:
            # rebind item in list
            result_list.append(Marshal.wrap(layer))
        print("layers property returns ", result_list)
        return result_list

    # No layers setter

    @property
    def vectors(self):
        # avoid circular import, import when needed
        from adaption.marshal import Marshal

        unwrapped_list = self._adaptee.get_vectors()
        result_list = Marshal.wrap_args(unwrapped_list)
        return result_list


    # TODO all these properties are rote changes to name i.e. prefix with get_
    # Do this at runtime, or code generate?

    # TODO this is canonical, move to DynamicReadOnlyAdaptedProperties
    @property
    def active_layer(self):
        # Delegate to Gimp.Image
        # TODO wrap result or lazy wrap
        return self._adaptee.get_active_layer()
    @active_layer.setter
    def active_layer(self, layer):
        # TODO:
        raise RuntimeError("not implemented")


    @property
    def base_type(self):
        # Delegate to Gimp.Image
        # Result is fundamental type (enum int)
        return self._adaptee.base_type()

    """
    !!! This is not correct, since get_file() can return None.
    file = self._adaptee.get_file()
    # assert file is-a Gio.File
    result = file.get_path()
    """
    @property
    def filename(self):
        '''
        Result is-a string.
        Really a path.
        Returns "Untitled" if image not loaded from file, or not saved.
        '''
        # print("GimpfuImage.filename get called")
        result = self._adaptee.get_name()
        return result


    """
    @property
    def width(self):
        return self._adaptee.width()
    @property
    def height(self):
        return self._adaptee.height()
    """