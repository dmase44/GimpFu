

import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp




'''
see comments at gimpfu_image, which is very similar
'''




# TODO how do we make instances appear to be the type of the adaptee
# when passed as args to Gimp?????

class GimpfuLayer( ) :

    # img->ID, name, width, height, type, opacity, mode);
    def __init__(self, img=None, name=None, width=None, height=None, type=None, opacity=None, layer_mode=None, adaptee=None):
        if img is None:
            # Wrap adaptee
            self._adaptee = adaptee
        else:
            # Totally new, invoked by GimpFu plugin author
            # Gimp constructor named "new"
            self._adaptee = Gimp.Layer.new(img.unwrap(), name, width, height, type, opacity, layer_mode)
        print("new layer", self._adaptee)


    def __eq__(self, other):
         '''
         Override equality.
         Two wrappers are equal if their adaptee's are equal.

         Require self and other both wrappers.
         Otherwise, raise exception.
         I.E. not general purpose equality such as foo == 1
         '''
         try:
             # Compare ID's or names instead?
             # Could use public unwrap() for more generality
             return self._adaptee == other.unwrap()
         except AttributeError:
             print("Can't compare GimpfuLayer to type ", type(other))
             raise



    def unwrap(self):
        ''' Return inner object, of a Gimp type, when passing arg to Gimp'''
        print("unwrap to", self._adaptee)
        return self._adaptee


    # Methods we specialize
    # see other examples  gimpfu_image.py

    '''
    copy() was implemented in v2, but I am not sure it went through the __copy__ mechanism.
    Anyway, a GimpFu author uses layer.copy().
    That invokes the copy() method, defined here.

     __copy__ is invoked by copy module i.e. copy.copy(foo)
    Any copy must be deep, to copy attribute _adaptee.
    To allow Gimpfu plugin authors to use the copy module,
    we should override __copy__ and __deepcopy__ also.
    Such MUST call gimp to copy the adaptee.
    TODO

    See SO "How to override the copy/deepcopy operations for a Python object?"
    This is a hack of that answer code.
    '''
    '''
    Arg "alpha" is convenience, on top of Gimp.Layer.copy()
    TODO alpha not used.  Code to add alpha if "alpha" param is true
    '''
    # TODO just Marshal.wrap() ??? Would work if self has no attributes not computed from adaptee
    def copy(self, alpha=False):
        """
        OLD
        ''' Deep copy wrapper, with cloned adaptee'''
        cls = self.__class__
        result = cls.__new__(cls)
        result.__dict__.update(self.__dict__)

        '''
        clone _adaptee
        v2 called run_procedure()
        Here we use Gimp.Layer.copy() directly???
        '''
        adaptee_clone = self._adaptee.copy()
        setattr(result, "_adaptee", adaptee_clone)
        """
        from gimpfu_marshal import Marshal
        adaptee_clone = self._adaptee.copy()
        result =  Marshal.wrap(adaptee_clone)

        print("Copy type: ", adaptee_clone, " into result",  result)
        return result

    '''
    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            setattr(result, k, deepcopy(v, memo))
        return result
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



    # Methods and properties offered dynamically.
    # __getattr__ is only called for methods not found on self

    def __getattr__(self, name):
        '''
        when name is callable, return callable which is soon to be called
        when name is data member, returns value
        !!! This does not preclude public,direct access to _adaptee, use unwrap()
        '''
        return getattr(self.__dict__['_adaptee'], name)


    def __setattr__(self, name, value):
        if name in ('_adaptee',):
            self.__dict__[name] = value
        else:
            setattr(self.__dict__['_adaptee'], name, value)

    def __delattr__(self, name):
        delattr(self.__dict__['_adaptee'], name)
