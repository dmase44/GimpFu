

import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp
from gi.repository import GObject    # marshalling

from gimpfu.adaption.marshal_pdb import MarshalPDB
from gimpfu.adaption.compatibility import pdb_name_map

from gimpfu.message.proceed import proceed

import logging


class GimpfuPDB():
    '''
    Adaptor to Gimp.PDB
    GimpFu defines a symbol "pdb", an instance of this class.
    Its attributes appear to have similar names as procedures in the Gimp.PDB.

    GimpFu v2 also allowed access using index notation.
    Obsolete? not supported here yet.

    GimpFu creates one instance named "pdb"
    TODO enforce singleton, but author doesn't even imagine this class exists.

    FBC
    Problems it solves:

    1) We can't just "pdb = Gimp.get_pdb()" at gimpfu import time
    because Gimp.main() hasn't been called yet
    (which would create the PDB instance and establish self type is GimpPlugin).
    Such code would bind "pdb" to None, forever, since that is the way import works.
    Besides, the object returned by Gimp.get_pdb() is the PDB manager,
    not having a method for each procedure IN the PDB???

    Alternatively, we could require a plugin's "func" to always first call pdb = Gimp.get_pdb().
    But that is new boilerplate for s, and not backward compatible.

    2) PyGimp v2 made an object for pdb some other way???? TODO
    '''

    '''
    Implementation:

    See:
    1)"Adaptor pattern"
    2) Override "special method" __get_attribute__.
    3) "intercept method calls"
    4) "marshalling" args.

    An author's access (on right hand side) of an attribute of this class (instance "pdb")
    is adapted to run a procedure in the PDB.
    Requires all accesses to attributes of pdb are function calls (as opposed to get data member.)
    Each valid get_attribute() returns an interceptor func.
    The interceptor func marshalls arguments for a call to PDB.run_procedure()
    and returns result of run_procedure()

    ???Some get_attributes ARE attributes on Gimp.PDB e.g. run_procedure().
    We let those pass through, with mangling of procedure name and args?

    Notes:

    Since we override __getattribute__, use idiom to avoid infinite recursion:
    call super to access self attributes without recursively calling overridden __getattribute__.
    super is "object".  Alternatively: super().__getattribute__()

    TODO should use __getattr__ instead of __getattribute__ ??

    Errors:

    Exception if cannot get a reference to PDB
    (when this is called before Gimp.main() has been called.)

    Exception if attribute name not a procedure of PDB

    No set attribute should be allowed, i.e. author use pdb on left hand side.
    The PDB (known by alias "pdb") can only be called, it has no data members.
    But we don't warn, and the effect would be to add attributes to an instance of this class.
    Or should we allow set attribute to mean "store a procedure"?
    '''

    def __init__(self):
        self.logger = logging.getLogger("GimpFu.GimpfuPDB")

    def _nothing_adaptor_func(self, *args):
        ''' Do nothing when an unknown PDB procedure is called. '''
        self.logger.warning("_nothing_adaptor_func called for unknown PDB procedure")
        return None


    def _adaptor_func(self, *args, **kwargs):
        """
        Run a PDB procedure whose name was used like "pdb.name()" e.g. like a method call of pdb object.

        Crux: wrap a call to PDB.run_procedure()
        Wrapping requires marshalling args from Python types to GObject types.
        Wrapping also requires inserting run_mode arg (GimpFu hides that from Authors.)

        Args are from Author.  That is, they are external (like i/o, beyond our control).
        Thus we catch exceptions (and check for other errors) and proceed.
        """

        self.logger.debug(f"_adaptor_func called, args: {args}")

        if kwargs:
            proceed(f"PDB procedures do not take keyword args.")

        # !!! avoid infinite recursion
        proc_name = object.__getattribute__(self, "adapted_proc_name")

        # !!! Must unpack args before passing to _marshall_args
        try:
            marshaled_args = MarshalPDB.marshal_args(proc_name, *args)
        except Exception as err: # TODO catch only MarshalError ???
            proceed(f"marshalling args to pdb.{proc_name} {err}")
            marshaled_args = None

        if marshaled_args is not None:
            # marshaled_args is-a list of GValues, but it could be an empty list.
            # PyGObject will marshall the list into a GimpValueArray

            """
            This is almost always a segfaulted callee plugin,
            a separate process that crashed and is failing to respond to IPC.
            We assert and don't try/except/proceed because the error is
            serious and external to Author's plugin.
            """
            inner_result = Gimp.get_pdb().run_procedure( proc_name , marshaled_args)
            assert inner_result is not None, f"PDB procedure {proc_name} failed to return value array."

            # The first element of result is the PDB status
            self.logger.debug(f"run_procedure {proc_name}, result is: {inner_result.index(0)}")

            # pdb is stateful for errors, i.e. gets error from last invoke, and resets on next invoke
            error_str = Gimp.get_pdb().get_last_error()
            if error_str != 'success':   # ??? GIMP_PDB_SUCCESS
                """
                Log the args because it is a common failure: wrong args.
                We might also log what Author gave (args) before we marshalled them.
                TODO i.e. { {*args} } ?, but that leaves braces in the output
                TODO  { {*args} } throws "unhashable type GimpfuImage"
                """
                self.logger.warning(f"Args: {marshaled_args}")
                proceed(f"PDB call fail: {proc_name} Gimp says: {error_str}")
                result = None
            else:
                result = MarshalPDB.unmarshal_results(inner_result)
        else:
            result = None

        # This is the simplified view of what we just did, without all the error checks
        # object.__getattribute__(self, "_marshall_args")(proc_name, *args)

        # Most PDB calls have side_effects on image, but few return values?

        # ensure result is defined and (is-a list OR None)

        # TODO throws for GBoxed, so log the types and not the values
        self.logger.debug(f"_adaptor_func for: {proc_name}  returns: {result}")
        return result




    # def  __getattribute__(self, name):
    def __getattr__(self, name):
        '''
        Adapts attribute access to become invocation of PDB procedure.
        Returns an adapter_func

        Override of Python special method.
        The more common purpose of such override is to compute the attribute,
        or get it from an adaptee.
        '''

        '''
        Require that author previously called main()
        which calls Gimp.main() to create PDB and establish GimpFu type is GimpPlugin
        '''
        if Gimp.get_pdb() is None:
            # Severe error in GimpFu code, or  did not call main()
            # Cannot proceed.
            raise Exception("Gimpfu: pdb accessed before calling main()")
        else:
            # TODO leave some calls unadapted, direct to PDB
            # ??? e.g. run_procedure ???, recursion ???

            # Map hyphens, and deprecated names.
            mangled_proc_name = pdb_name_map[name]

            if Gimp.get_pdb().procedure_exists(mangled_proc_name):
                self.logger.debug(f"__getattr__ returns callable _adaptor_func for reference to: {mangled_proc_name}")
                # remember state for soon-to-come call
                self.adapted_proc_name = mangled_proc_name
                # return intercept function soon to be called
                result = object.__getattribute__(self, "_adaptor_func")

                # TODO We could redirect deprecated names to new procedure names
                # if they have same signature
                # e.g. gimp_image_get_filename => gimp-image-get-file (but not same signature)
                # That case should be adapted, since a filename is not a GFile
                # elif name = deprecate_pdb_procedure_name_map()
            else:
                # Can proceed if we catch the forthcoming call
                # by returning a do_nothing_intercept_func
                proceed(f"unknown pdb procedure {mangled_proc_name}")
                result = object.__getattribute__(self, "_nothing_adaptor_func")

            return result

            # OLD
            # will raise AttributeError for names that are not defined by GimpPDB
            # return adapteeValue.__getattribute__(mangled_proc_name)






    # specialized, convenience



    def get_last_error(self):
        """ Return last error from PDB.

        For some reason, this is not in the gir nor the PDB Browser,
        but it is a method on the PDB.
        """
        return Gimp.get_pdb().get_last_error()


    '''
    These are pdb procedures from v2 that Gimp deprecated.
    Since some plugins may still use them, FBC define adaptors.
    '''

    # TODO say deprecated

    def gimp_ellipse_select(self, img, x, y, width, height, channel_op, foo, bar, zed):
        # 1. Discard last three parameters.  I don't know what effect that has.
        # 2. Reorder the other parameters
        # 3. renamed
        """
        We either must mangle the procedure name hyphens to call Gimp.get_pdb()
        or call the Gimp function directly.
        """
        # Not this:  Gimp.get_pdb().gimp_image_select_ellipse(img, channel_op, x, y, width, height)
        Gimp.Image.select_ellipse(img.unwrap(), channel_op, x, y, width, height)


    def gimp_edit_bucket_fill(self, layer, fill_type, layer_mode, opacity, threshold, sample_merged, x, y):
        """
        1.  Discard some parameters, effect could differ.
        2. renamed.
        """
        Gimp.Drawable.edit_bucket_fill(layer.unwrap(), fill_type, x, y)

    """
    These PDB procedures in v2 took integer ID.
    In v3 PDB, the procedures don't exist, instead there is e.g. gimp_item_ID_is_layer().
    An author could convert v2 to v3 by:
    gimp_item_is_layer(item) => gimp_item_ID_is_layer(item.ID).
    But FBC, here GimpFu provides adaptor procedure.
    """
    def gimp_item_is_layer(self, item):      return Gimp.Item.is_layer(item.unwrap())
    # TODO there are many more related to ID

    """
    These PDB procedures in v2 took a single layer.
    In v3 PDB, the procedures take an array of layer.

    FBC
    Pass a sequence (a tuple) to the v3 function, the binding will convert.
    """
    def gimp_edit_copy(self, item):      return Gimp.edit_copy( [item.unwrap(), ] )


    """
    WIP
    # Since v3 obsolete but having replacement with different return type in signature.
    def gimp_image_get_filename(image):
        file = Gimp.gimp_image_get_file(image):
        if file:
            # is-a GFile
            result = file.name ....
        else:
            result = None
        return result
    """
