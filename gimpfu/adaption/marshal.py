
import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp

from gimpfu.adaption.wrappable import *
from gimpfu.adaption.types import Types

# import wrapper classes
# These inherit Adapter which wants to use Marshal, avoid circular import
# in Adapter by selectively import Marshal
from gimpfu.adapters.image import GimpfuImage
from gimpfu.adapters.layer import GimpfuLayer
from gimpfu.adapters.channel import GimpfuChannel
from gimpfu.adapters.vectors import GimpfuVectors
from gimpfu.adapters.rgb import GimpfuRGB
from gimpfu.adapters.display import GimpfuDisplay

from gimpfu.message.proceed import proceed

import logging


class Marshal():
    '''
    Knows how to wrap and unwrap things.
    Abstractly: AdaptedAdaptee <=> adaptee
    Specifically: Gimp GObjects <=> Gimpfu<foo>

    Fundamental types pass through wrapping and unwrapping without change.

    Hides multiple constructors for wrappers.

    Each wrapped object (instance of AdaptedAdaptee) has an unwrap() method to return its adaptee.
    Wrapper class  AdaptedAdaptee also knows how to wrap() a new'd Gimp GObject

    But this provides 'convenience' methods for some cases, like unwrapping args.
    In that case, this hides the need to:
      - upcast (GObject frequently requires explicit upcast)
      - convert (Python will convert int to float), but GimpFu must do that for args to Gimp
      - check for certain errors (wrapping a FunctionInfo)

    For calls to Gimp, these methods suffice,
    since Gimp is a library linked to the Python interpreter and takes GObject's.

    For call to PDB, see marshal_pdb.py.
    '''

    # static attribute of singleton class
    logger = logging.getLogger('GimpFu.Marshal')

    '''
    Gimp breaks out image and drawable from other args.
    Reverse that.
    And convert type Gimp.ValueArray to type "list of GValue"
    '''
    def prefix_image_drawable_to_run_args(actual_args, image=None, drawable=None):
        '''
        Requires:
            - actual_args is-a Gimp.ValueArray
            - image, drawable are optional GObjects

        Return a list of the incoming items,
        where the items are still GValues

        !!! Returns Python list, not a Gimp.ValueArray
        '''
        Marshal.logger.info(f"prefix_image_drawable_to_run_args")

        args_list = Types.convert_gimpvaluearray_to_list_of_gvalue(actual_args)

        # Prepend to Python list
        if drawable:
            args_list.insert(0, drawable)
        if image:
            args_list.insert(0, image)

        # ensure result is-a list, but might be empty
        return args_list

    def convert_gimpvaluearray_to_list_of_gvalue(actual_args):
        """ Delegate to Types """
        return Types.convert_gimpvaluearray_to_list_of_gvalue(actual_args)



    '''
    wrap and unwrap

    These are generic: not special to an wrapper type.

    See wrapper class, i.e. AdaptedAdaptee e.g. GimpfuLayer.
    Wrapper class also have a unwrap() method specialized to the class.
    Wrapper class also has a constructor that effectively wraps.
    '''



    @staticmethod
    def wrap(gimp_instance):
        '''
        Wrap an instance from Gimp.
        E.G. Image => GimpfuImage

        Requires gimp_instance is-a Gimp object that should be wrapped,
        else exception.
        '''
        '''
        Invoke the internal constructor for wrapper class.
        I.E. the adaptee already exists,
        the Nones mean we don't know attributes of adaptee,
        but the adaptee has and knows its attributes.
        '''
        Marshal.logger.info(f"Wrap: {gimp_instance}")
        result = None

        wrapper_type_name = wrapper_type_name_for_instance(gimp_instance)
        if wrapper_type_name is None:
            proceed(f"GimpFu: can't wrap gimp type {get_type_name(gimp_instance)}")
            return result

        statement =  wrapper_type_name + '(adaptee=gimp_instance)'

        # e.g. statement  'GimpfuImage(adaptee=gimp_instance)'
        Marshal.logger.info(f"attempting to eval: {statement}")
        try:
            result = eval(statement)
        except Exception as err:
            """ Exception in Gimpfu code e.g. missing wrapper. """
            proceed(f"Wrapping: {err}")

        return result




    @staticmethod
    def unwrap(arg):
        '''
        Unwrap a single instance. Returns adaptee or a fundamental type.

        Knows which are wrapped types versus fundamental types,
        and unwraps only wrapped types.

        Unwrap any GimpFu wrapped types to Gimp types
        E.G. GimpfuImage => Gimp.Image
        For primitive Python types and GTypes, idempotent, returns given arg unaltered.

        Only fundamental Python types and Gimp types (not GimpfuFoo wrapper TYPE_STRING)
        can be passed to Gimp.
        '''
        # Unwrap wrapped types.
        if  is_gimpfu_unwrappable(arg) :
            # !!! Do not affect the original object by assigning to arg
            # assert arg isinstance(Adapter) and has method unwrap()
            result_arg = arg.unwrap()
        else:
            # arg is already Gimp type, or a fundamental type
            result_arg = arg
        Marshal.logger.info(f"unwrapped to: {result_arg}")
        return result_arg




    '''
    '''
    @staticmethod
    def _try_wrap(instance):
        ''' Wrap a single instance if it is wrappable, else the arg. '''
        if is_gimpfu_wrappable(instance):
            result = Marshal.wrap(instance)
        else:   # fundamental
            result = instance
        Marshal.logger.info(f"_try_wrap returns: {result}")
        return result


    @staticmethod
    def wrap_adaptee_results(args):
        '''
        Wrap result of calls to adaptee.

        args can be an iterable container e.g. a tuple or list or a non-iterable fundamental type.
        Result is iterable list if args is iterable, a non-iterable if args is not iterable.
        Except: strings are iterable but also fundamental.
        '''
        Marshal.logger.info(f"wrap_adaptee_results: {args}")
        try:
            unused_iterator = iter(args)
        except TypeError:
            # not iterable, but not necessarily fundamental
            result = Marshal._try_wrap(args)
        else:
            # iterable, but could be a string
            if isinstance(args, str):
                # No need to unwrap
                Marshal.logger.info(f"wrap_adaptee_results returns: a string")
                result = args
            else:
                # is container, return container of unwrapped
                result = [Marshal._try_wrap(item) for item in args]
        Marshal.logger.info(f"wrap_adaptee_results returns: {result}")
        return result





    '''
    wrap and unwrap sequence of things
    !!! note the 's'
    Generally the sequence is incoming or outgoing arguments.
    But distinct from arguments to the pdb, which are tuples.
    '''

    @staticmethod
    def wrap_args(args):
        '''
        args is a sequence of unwrapped objects (GObjects from Gimp) and fundamental types.
        Wraps instances that are not fundamental.
        Returns list.

        Typically args are:
        - from Gimp calling back the plugin.
        - from the plugin calling Gimp
        '''
        # args are in a list, but are GValues
        assert isinstance(args, list)

        result = []
        for instance in args:
            if is_gimpfu_wrappable(instance):
                result.append(Marshal.wrap(instance))
            else:   # fundamental
                Marshal.logger.info(f"Not wrapped: {instance}")
                result.append(instance)
        return result


    @staticmethod
    def unwrap_heterogenous_sequence(args):
        '''
        args is a sequence (Iterable) of possibly wrapped objects (class Gimpfu.Adapter)
        or fundamental types (int, etc.)
        Unwrap instances that are wrapped.
        Returns list.
        '''
        result = []
        for instance in args:
            if is_gimpfu_unwrappable(instance):
                result.append(Marshal.unwrap(instance))
            else:   # fundamental
                Marshal.logger.info(f"Not unwrapped: {instance}")
                result.append(instance)
        return result


    # TODO we could have method that takes sequence of definitely wrapped items

    @staticmethod
    def unwrap_homogenous_sequence(args):
        """
        Return new list where each item in args was unwrapped.
        Require each item in result is the same type.
        (Usually a Gimp type.)

        !!! Not require each item in args is a GimpFu wrapped type.
        It could already be an unwrapped type.

        Used to create GimpObjectArray, which are homogenous.
        """
        Marshal.logger.debug(f"unwrap_homogenous_sequence")
        result_list = []
        contained_type = None
        for item in args:
            # !!! This permits items already unwrapped
            new_item = Marshal.unwrap(item)
            if contained_type is not None:
                if type(new_item) != contained_type:
                    proceed(f"Unwrapped sequence is not type homogenous")
            else:
                contained_type = type(new_item)
            result_list.append(Marshal.unwrap(new_item))

        return result_list




    '''
    Gimp  marshal and unmarshal.
    For Gimp. , Gimp.Layer. , etc. method calls

    This will be very similar (extracted from?) PDB marsha

    marshal_gimp_args, unmarshal_gimp_results
    '''
