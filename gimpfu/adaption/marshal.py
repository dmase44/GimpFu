
import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp

# TODO make this module the only one that imports GObject
from gi.repository import GObject


from adaption.wrappable import *

# import wrapper classes
# These inherit Adapter which wants to use Marshal, avoid circular import
# in Adapter by selectively import Marshal
from adapters.image import GimpfuImage
from adapters.layer import GimpfuLayer
from adapters.vector import GimpfuVectors

from gimpfu_exception import *




class Marshal():
    '''
    Knows how to wrap and unwrap things.
    Abstractly: AdaptedAdaptee <=> adaptee
    Specifically: Gimp GObjects <=> Gimpfu<foo>
    Fundamental types pass through wrapping and unwrapping without change.

    Hides multiple constructors for wrappers.

    Each wrapped object has an unwrap method to return its adaptee.
    But this provides 'convenience' methods for some cases, like unwrapping args.
    In that case, this hides the need to:
      - upcast (GObject frequently requires explicit upcast)
      - convert (Python will convert int to float), but GimpFu must do that for args to Gimp
      - check for certain errors (wrapping a FunctionInfo)

    Each wrapper also knows how to create a wrapper for a new'd Gimp GObject
    '''



    '''
    Gimp breaks out image and drawable from other args.
    Reverse that.
    And convert type Gimp.ValueArray to type "list of GValue"
    '''
    def prefix_image_drawable_to_run_args(actual_args, image=None, drawable=None):
        '''
        return a list [image, drawable, *actual_args]
        Where:
            actual_args is-a Gimp.ValueArray
            image, drawable are optional GObjects
        !!! Returns a list, not a Gimp.ValueArray
        '''

        args = []
        if image:
            args.append(image)
        if drawable:
            args.append(drawable)

        len = actual_args.length()   # !!! not len(actual_args)
        for i in range(len):
            gvalue = actual_args.index(i)
            # Python can handle the gvalue, we don't need to convert to Python types
            # assuming we have imported gi
            args.append(gvalue)
        # ensure result is-a list, but might be empty
        return args





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
        Wrap Gimp types that GimpFu wraps.
        E.G. Image => GimpfuImage

        Requires gimp_instance is-a Gimp object
        '''
        '''
        Invoke the internal constructor for wrapper class.
        I.E. the adaptee already exists,
        the Nones mean we don't know attributes of adaptee,
        but the adaptee has and knows its attributes.
        '''
        print("Wrap ", gimp_instance)

        if is_gimpfu_wrappable(gimp_instance):
            gimp_type_name = get_gimp_type_name(gimp_instance)
            statement = 'Gimpfu' + gimp_type_name + '(adaptee=gimp_instance)'
            # e.g. statement  'GimpfuImage(adaptee=gimp_instance)'
            result = eval(statement)
        else:
            exception_str = f"GimpFu: can't wrap gimp type {gimp_type_name}"
            do_proceed_error(exception_str)
        return result

        """
        OLD
        # Dispatch on gimp type
        # This is a switch statement, default is an error
        gimp_type = type(gimp_instance).__name__    # idiom for class name
        if  gimp_type == 'Image':
            result = GimpfuImage(adaptee=gimp_instance)
        elif gimp_type == 'Layer':
            result = GimpfuLayer(adaptee=gimp_instance)
        elif gimp_type == 'Display':
            result = GimpfuDisplay(adaptee=gimp_instance)
        elif gimp_type == 'Vectors':
            result = GimpfuVectors(adaptee=gimp_instance)
        #elif gimp_type == 'Channel':
        # result = GimpfuLayer(None, None, None, None, None, None, None, gimp_instance)
        else:
            exception_str = f"GimpFu: can't wrap gimp type {gimp_type}"
            do_proceed_error(exception_str)
        """


    @staticmethod
    def _unwrap_arg(arg):
        '''
        Unwrap any GimpFu wrapped types to Gimp types
        E.G. GimpfuImage => Gimp.Image
        For primitive Python types and GTypes, idempotent, returns given arg unaltered.

        Only fundamental Python types and Gimp types (not GimpfuFoo wrapper TYPE_STRING)
        can be passed to Gimp.
        '''
        # Unwrap wrapped types.
        if  is_gimpfu_unwrappable(arg) :
            # !!! Do not affect the original object by assigning to arg
            # !!! arg knows how to unwrap itself
            result_arg = arg.unwrap()
        else:
            # arg is already Gimp type, or a fundamental type
            result_arg = arg
        print("unwrap_arg:", result_arg)
        return result_arg



    '''
    unwrap to a GParamSpec
    '''

    @staticmethod
    def _unwrap_arg_to_param(arg):
        '''
        Unwrap any wrapped.
        Returns a tuple: (unwrapped arg, type of unwrapped arg)
        For use as arg to PDB, which requires ParamSpec tuple.

        Only fundamental Python types and GTypes can be GObject.value()ed,
        which is what Gimp does with ParamSpec
        '''

        # TODO, possible optimization if arg is already unwrapped, or lazy?
        result_arg = Marshall._unwrap_arg(arg)

        # hack: upcast  subclass e.g. layer to superclass drawable
        # hack that might be removed if Gimp was not wrongly stringent

        # TODO optimize, getting type is simpler when is fundamental
        # We could retain that the arg is fundamental during unwrapping
        result_arg_type = try_upcast_to_drawable(result_arg)

        print("unwrap_arg_to_param", result_arg, result_arg_type)
        return result_arg, result_arg_type

    '''
    '''
    @staticmethod
    def _try_wrap(instance):
        ''' Wrap a single instance if it is wrappable, else the arg. '''
        if is_gimpfu_wrappable(instance):
            result = Marshal.wrap(instance)
        else:   # fundamental
            result = instance
        return result


    @staticmethod
    def wrap_adaptee_results(args):
        '''
        Wrap result of calls to adaptee.

        args may be an iterable e.g. a tuple or list?
        Result is iterable if args is.
        Result is a list if args is?
        '''
        try:
            iterator = iter(args)
        except TypeError:
            # not iterable
            result = Marshal._try_wrap(args)
        else:
            # iterable
            result = []
            for instance in args:
                result.append( Marshal._try_wrap(instance))
        return result





    '''
    wrap and unwrap list of things
    !!! note the 's'
    Generally the list is incoming or outgoing arguments.
    But distinct from arguments to the pdb, which are tuples.
    '''

    @staticmethod
    def wrap_args(args):
        '''
        args is a sequence of unwrapped objects (GObjects from Gimp) and fundamental types,
        (typically received from Gimp calling the plugin.)
        Wraps instances that are not fundamental.
        Returns list.
        '''
        print("wrap_args", args)
        result = []
        for instance in args:
            if is_gimpfu_wrappable(instance):
                result.append(Marshal.wrap(instance))
            else:   # fundamental
                result.append(instance)
        return result


    @staticmethod
    def unwrap_args(args):
        '''
        args is a sequence of possibly wrapped objects (class GimpfuFoo)
        or fundamental types.
        Unwrap instances that are wrapped.
        Returns list.
        '''
        print("unwrap_args", args)
        result = []
        for instance in args:
            if is_gimpfu_unwrappable(instance):
                result.append(Marshal._unwrap_arg(instance))
            else:   # fundamental
                result.append(instance)
        return result






    '''
    Gimp  marshal and unmarshal.
    For Gimp. , Gimp.Layer. , etc. method calls

    This will be very similar (extracted from?) PDB marsha

    marshal_gimp_args, unmarshal_gimp_results
    '''



    '''
    PDB marshal, unmarshal
    '''

    @staticmethod
    def marshal_pdb_args(proc_name, *args):
        '''
        Marshal args to a PDB procedure.

        1. Gather many args into Gimp.ValueArray and return it.

        2. Optionally prefix args with run mode
        GimpFu feature: hide run_mode from calling author

        3. Unwrap wrapped arguments so all args are GObjects

        4. Hacky upcast to Drawable ???

        5. float(arg) as needed

        6. Check error FunctionInfo
        '''

        # TODO python-fu- ?? What procedure names signify need run_mode?
        # Better to introspect ??
        if proc_name.startswith('plug-in-'):
            marshalled_args = Gimp.ValueArray.new(len(args)+1)
             # no GUI, this is a call from a plugin
            marshalled_args.insert(0, Gimp.RunMode.NONINTERACTIVE)
            index = 1
        else:
            marshalled_args = Gimp.ValueArray.new(len(args))
            index = 0


        for x in args:
            ## GObject.Value(GObject.TYPE_STRING, tmp))
            ## print("marshal arg:", x )

            go_arg, go_arg_type = _unwrap_arg_to_param(x)

            '''
            Don't assume any arg does NOT need conversion:
            a procedure can declare any arg of type float

            If more args than formal_args (from GI introspection), conversion will not convert.
            If less args than formal_args, Gimp might return an error when we call the PDB procedure.
            '''
            go_arg, go_arg_type = Marshal.try_convert_to_float(proc_name, go_arg, go_arg_type, index)

            if is_wrapped_function(go_arg):
                do_proceed_error("Passing function as argument to PDB.")


            # !!! Can't assign GObject to python object: marshalled_arg = GObject.Value(Gimp.Image, x)
            # Must pass directly to insert()

            # ??? I don't understand why GObject.Value() doesn't determine the type of its second argument
            # unless GObject.Value() does some sort of casting

            '''
            This exception is not caused by plugin author, usually GimpFu programming error.
            Usually "Must be a GObject.GType, not a type"
            '''
            try:
                marshalled_args.insert(index, GObject.Value(go_arg_type, go_arg))
            except Exception as err:
                do_proceed_error(f"Exception marshalling arg {x} to pdb, {err}")

            index += 1

        print("marshalled_args", marshalled_args )
        return marshalled_args


    @staticmethod
    def unmarshal_pdb_result(values):
        ''' Convert result of a pdb call to Python objects '''

        '''
        values is-a GimpValueArray
        First element is a PDBStatusType, discard it.
        If count remaining elements > 1, return a list,
        else return the one remaining element.

        For all returned objects, wrap as necessary.
        '''

        # caller should have previously checked that values is not a Gimp.PDBStatusType.FAIL
        if values:
            # Remember, values is-a Gimp.ValueArray, not has Pythonic methods
            result_list = []
            # start at 1 to discard status
            for index in range(1, values.length()):
                value = values.index(index)
                result_list.append(value)
            # unpack list of one element
            if len(result_list) is 1:
                result = result_list[0]
            else:
                result = result_list
        else:
            result = None

        # ensure result is None or result is list or result is one object
        # TODO ensure wrapped?
        print("unmarshal_pdb_result", result)
        return result




    '''
    Type conversions.

    GimpFu converts Python ints to floats on behalf of Gimp.
    GimpFu converts Layer to Drawable where Gimp is uneccessarily demanding.
    '''

    # TODO optimize.  Get all the args at once, memoize

    def _get_formal_argument_type(proc_name, index):
        '''
        Get the formal argument type for a PDB procedure
        where argument identified by index.
        Returns an instance of GType e.g. GObject.TYPE_INT

        Another implementation: Gimp.get_pdb().run_procedure( proc_name , 'gimp-pdb-get-proc-argument', args)
        '''
        # require procedure in PDB, it was checked earlier
        procedure = Gimp.get_pdb().lookup_procedure(proc_name)
        ## OLD config = procedure.create_config()
        ## assert config is type Gimp.ProcedureConfig, having properties same as args of procedure

        arg_specs = procedure.get_arguments()    # some docs say it returns a count, it returns a list of GParam??
        print(arg_specs)
        # assert is a list

        ## arg_specs = Gimp.ValueArray.new(arg_count)
        ##config.get_values(arg_specs)

        # assert arg_specs is Gimp.ValueArray, sequence describing args of procedure
        # index may be out of range, GimpFu author may have provided too many args
        try:
            arg_spec = arg_specs[index]   # .index(index) ??
            print(arg_spec)
            # assert is-a GObject.GParamSpec or subclass thereof
            ## OLD assert arg_spec is GObject.Value, describes arg of procedure (its GType is the arg's type)

            '''
            CRUFT, some comments may be pertinent.

            The type of the subclass of GParamSpec is enough for our purposes.
            Besides, GParamSpec.get_default_value() doesn't work???

            formal_arg_type = type(arg_spec)
            '''

            '''
            print(dir(arg_spec)) shows that arg_spec is NOT a GParamSpec, or at least doesn't have get_default_value.
            I suppose it is a GParam??
            Anyway, it has __gtype__
            '''
            """
            formal_default_value = arg_spec.get_default_value()
            print(formal_default_value)
            # ??? new to GI 2.38
            # assert is-a GObject.GValue

            formal_arg_type = formal_default_value.get_gtype()
            """
            formal_arg_type = arg_spec.__gtype__

        except IndexError:
            do_proceed_error("Formal argument not found, probably too many actual args.")
            formal_arg_type = None


        print( "get_formal_argument returns", formal_arg_type)

        # assert type of formal_arg_type is GObject.GType
        ## OLD assert formal_arg_type has python type like GParamSpec<Enum>
        return formal_arg_type


    def try_convert_to_float(proc_name, actual_arg, actual_arg_type, index):
        '''
        Convert the described actual arg to float if is int
        and PDB procedure wants a float
        (procedure's formal parameter is type GObject.TYPE_FLOAT).
        Only converts Python int to float.

        Returns actual_arg, type(actual_arg), possibly converted

        Later, GObject will convert Python types to GTypes.
        '''
        # require type(actual_arg_type) is Python type or a GType

        result_arg = actual_arg
        result_arg_type = actual_arg_type

        print("Actual arg type:", type(actual_arg))

        if type(actual_arg) is int:
            formal_arg_type = Marshal._get_formal_argument_type(proc_name, index)
            if formal_arg_type is not None:
                # GType has property "name"
                print("     Formal arg type ", formal_arg_type.name )

                #if formal_arg_type == GObject.TYPE_FLOAT or formal_arg_type == GObject.TYPE_DOUBLE :
                if formal_arg_type.name in ('GParamFloat', 'GParamDouble'): # ParamSpec ???
                    # ??? Tell Gimpfu plugin author their code would be more clear if they used float() themselves
                    # ??? Usually the source construct is a literal such as "1" that might better be float literal "1.0"
                    print("GimpFu: Suggest: converting int to float.  Your code might be clearer if you use float literals.")
                    result_arg = float(actual_arg)  # type conversion
                    result_arg_type = type(result_arg)  # i.e. float
            else:
                # Failed to get formal argument type.  Probably too many actual args.
                # Do not convert type.
                pass

        # ensure result_arg_type == type of actual_arg OR (type(actual_arg) is int AND result_type_arg == float)
        # likewise for value of result_arg
        print("try_convert_to_float returns ", result_arg, result_arg_type)
        return result_arg, result_arg_type


    '''
    Seems like need for upcast is inherent in GObj.
    But probably Gimp should be doing most of the upcasting,
    so that many plugs don't need to do it.
    '''
    @staticmethod
    def try_upcast_to_drawable(arg):
        '''
        When type(arg) is subclass of Gimp.Drawable,
        and return new type Gimp.Drawable, else return original type.
        Does not actually change type of arg.

        Require arg a GObject (not wrapped)
        '''
        # idiom for class name
        print("Attempt upcast type", type(arg).__name__ )
        if is_subclass_of_drawable(arg):
            result = Gimp.Drawable
        else:
            result = type(arg)
        # assert result is-a type (a Gimp type, a GObject type)
        print("upcast result:", result)
        return result



    """
    Cruft: more than necessary, but keep it, it documents how to use GTypes

    def try_convert_to_float(proc_name, actual_arg, actual_arg_type, index):
        '''
        Convert the described actual arg to float if is int
        and PDB procedure wants a float (procedure's formal parameter is type float)

        Returns arg, arg_type    possibly converted
        '''
        # require actual_arg_type is a GType

        result_arg = actual_arg
        result_arg_type = actual_arg_type

        print("Actual arg type:", actual_arg_type)

        '''
        GType types are enumerated by constants of GObject.
        E.G. GObject.TYPE_INT is-a GType .
        In GObject docs, see "Constants"
        '''
        if actual_arg_type == GObject.TYPE_INT :    # INT_64 ???
            formal_arg_type = _get_formal_argument_type(proc_name, index)
            if formal_arg_type == GObject.TYPE_FLOAT or formal_arg_type == GObject.TYPE_DOUBLE :
                print("GimpFu: Warning: converting int to float.")
                result_arg = float(actual_arg)
                result_arg_type = GObject.TYPE_DOUBLE

        return result_arg, result_arg_type
    """
