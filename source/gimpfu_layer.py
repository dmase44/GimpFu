

import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp

from adapter import Adapter





class GimpfuLayer( Adapter ) :

    def __init__(self, img=None, name=None, width=None, height=None, type=None, opacity=None, layer_mode=None, adaptee=None):

        if img is not None:
            # Totally new adaptee, created at behest of GimpFu plugin author
            # Gimp constructor named "new"
            super().__init__( Gimp.Layer.new(img.unwrap(), name, width, height, type, opacity, layer_mode) )
        else:
            # Create wrapper for existing adaptee (from Gimp)
            # Adaptee was created earlier at behest of Gimp user and is being passed into GimpFu plugin
            assert adaptee is not None
            super().__init__(adaptee)

        print("new GimpfuLayer with adaptee", self._adaptee)




    '''
    Methods for convenience.
    i.e. these were defined in PyGimp v2

    They specialize methods that might exist in Gimp.
    Specializations:
    - add convenience parameters
    - rename: old name => new or simpler name
    - one call => many subroutines

    see other examples  gimpfu_image.py
    '''


    def copy(self, alpha=False):
        '''
        Return copy of self.

        Param "alpha" is convenience, on top of Gimp.Layer.copy()

        !!! TODO alpha not used.  Code to add alpha if "alpha" param is true??
        The docs are not clear about what the param means.
        If it means "add alpha", should rename it should_add_alpha
        '''
        # delegate to adapter
        return super().copy()
        # If this class had any data members, we would need to copy their values also


    # TODO inherit Item
    def translate(self, x, y):
        # in app: gimp_item_transform_translate(self->ID
        # adaptee is-a Gimp.Item that has transform methods
        self._adaptee.transform_translate(x,y)


    '''
    Properties.

    For convenience, GimpFu makes certain attributes have property semantics.
    I.E. get without parenthesises, and set by assignment, without calling setter() func

    TODO, does Gimp GI provide this already?
    '''

    # Layer inherits Item
    # TODO inherit ItemWrapper class in Python?
    @property
    def name(self):
        print("Calling Layer.get_name(): ")
        #print(dir(self._adaptee))
        result = self._adaptee.get_name()
        print("name() returns item name: ", result)
        return result
    @name.setter
    def name(self, name):
        return self._adaptee.set_name(name)


    # class Layer
    @property
    def lock_alpha(self):
        return self._adaptee.get_lock_alpha()
    @lock_alpha.setter
    def lock_alpha(self, truth):
        return self._adaptee.set_lock_alpha(truth)


    #raise RuntimeError("not implemented")
