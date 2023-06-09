


"""
We don't use gi directly, but it must be in scope for exec.
Similarly for GObject, Gimp.
I.E. we evaluate strings like "Gimp.ObjectArray", so "Gimp" must be in scope.
"""
import gi
from gi.repository import GObject

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp   # for Gimp enum RunMode

import string

import logging



"""
Factory that creates a GObject having a templated property.

Used to pass properties to Gimp to specify parameters.
This all could go away if GParamSpec is fixed in PyGObject
"""
class PropHolderFactory():



    def __init__(self):

        self.logger = logging.getLogger("GimpFu.PropHolderFactory")

        """
        Template strings.

        !!! Note that string.Template may call repr() on any substitutions
        when a value passed is not already type string.
        Thus the string returned by __repr__  must be true to the standard for repr
        i.e. when execed it must reproduce the value.

        Indentation important on template strings.
        # type, nick, blurb, default, min, max, flags

        nick is the documentary name of the property, i.e. nickname, almost always the same as the name of the property
        """
        # TODO float() for float, insure is proper type literal
        self.template_string_numeric = r'''
global Foo
class Foo(GObject.GObject):
    __gproperties__ = {
        "$name": ($type, "$name", "blurb", $min, $max, $default, GObject.ParamFlags.READWRITE ),
    }
'''

        # !!! note default is quoted
        self.template_string_str = r'''
global Foo
class Foo(GObject.GObject):
  __gproperties__ = {
    "$name": ($type, "$name", "blurb", "$default", GObject.ParamFlags.READWRITE ),
  }
'''

        """
        case: type is Gimp types
        !!! Default is omitted.
        """
        self.template_string_gimp_value = r'''
global Foo
class Foo(GObject.GObject):
  __gproperties__ = {
    "$name": ($type, "$name", "blurb", GObject.ParamFlags.READWRITE ),
  }
'''




    """
    TODO also pass blurb, substitute into template
    """
    def produce(self, unique_prop_name, type, default, min, max):
        """
        Produce an instance of GObject with a property as described by the args.
        We will use the instance to convey to Gimp a
        formal declaration of an argument of a PDB procedure.
        Again, ideally we would just use a GParamSpec.
        Its very convoluted.
        """

        # assert type is a Python type

        self.logger.info(f"produce property, name: {unique_prop_name} type: {type} default: {default}, min: {min}, max: {max}")

        # OLD generate a name
        # unique_prop_name = name_generator.get_unique_name()

        # substitute into template
        # !!! need strings but str() and repr() don't work for type
        # dispatch on type
        if type is int:
            """
            ??? TODO
            For IN args, default must be specified.
            For OUT args, default can be None.
            """
            if not (isinstance(default, int) or isinstance(default, bool)):
                #self.logger.warning(f"Default is None.  If this is not an IN parameter, default should not be None.")
                raise RuntimeError(f"default: {default} having type: {type(default)} class: {default.__class__}, should be of type int.")
            template = string.Template(self.template_string_numeric)
            code_string = template.substitute(type="int", name=unique_prop_name, default=default, min=min, max=max)
        elif type is float:
            template = string.Template(self.template_string_numeric)
            code_string = template.substitute(type="float", name=unique_prop_name, default=default, min=min, max=max)
        elif type is str:
            template = string.Template(self.template_string_str)
            code_string = template.substitute(type="str", name=unique_prop_name, default=default)
        elif isinstance(type, str):
            # assert str names a Gimp type or GLib type (GStrv)
            template = string.Template(self.template_string_gimp_value)
            # !!! Omit default
            code_string = template.substitute(type=type, name=unique_prop_name)

        else:
            # fatal, useless to proceed if we can't convey args to Gimp
            raise RuntimeError(f"Unhandled property type: {type}")

        # This logs a long string
        #self.logger.info(f"exec( {code_string} )")

        # create class Foo in globals by exec template

        self.logger.info(f"exec> {code_string} <to define class for property")
        exec(code_string)

        # create instance of class
        instance = Foo()
        # assert instance is-a GObject with property as specified
        assert instance is not None

        # OLD also return generated name
        return instance
