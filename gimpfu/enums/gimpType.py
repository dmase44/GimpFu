
import gi
gi.require_version("Gimp", "3.0")
from gi.repository import Gimp

import logging



class GimpType():
    """
    Understands how to go back and forth from names of types to types.

    Understands forms of names for types:
    Gimp enum type name in C:  GimpMergeType
    Dotted name in Python:     Gimp.MergeType
    Short name in Python:      MergeType
    """

    logger = logging.getLogger("GimpFu.GimpType")
    # !!! voluminous, so enable logging separately from GIMPFU_DEBUG
    # CRITICAL suppresses messages about overwriting already defined symbols
    # WARNING is the usual
    logger.setLevel(logging.WARNING)
    logger.setLevel(logging.DEBUG)


    @classmethod
    def list_gimp_enums(cls):
        """ Return a list of short names of Gimp enum types. """
        cls.logger.debug(f"list_gimp_enums")

        # call libgimp function.
        # This is first use of gir, which may crash.  No use to try: except:
        # TEMP gtype_names, count_names = Gimp.enums_get_type_names()
        gtype_names = []

        """
        Names are like GimpImageType i.e. not in dot notation, but a GType name.
        Except some are like GeglDistanceMetric !!!!
        Discard those.
        """

        names = []
        for name in gtype_names:
            if name.find("Gegl") == 0:
                continue

            cls.logger.debug(f"Name of Gimp enum {name}")
            names.append(cls.short_name_of_type_name(name))

        cls.logger.debug(f"Short names of Gimp enums {names}")
        # assert short names
        return names


    """ GType names to/from Python names """

    @classmethod
    def short_name_of_type_name(cls, type_name):
        # assert type_name like "GimpMergeType" !!! a string
        return type_name.replace("Gimp", "")

    @classmethod
    def short_name_of_dotted_name(cls, dotted_name):
        # assert type_name like "Gimp.MergeType" !!! a string
        return dotted_name.replace("Gimp.", "")

    @classmethod
    def type_name_from_short_name(cls, short_name):
        # Reconstruct the GType name
        name = "Gimp" + short_name
        cls.logger.debug(f"type_name_from_short_name {name}")
        return name

    # TODO clean up the confusion here about GTypes and Python types
    # e.g. GimpMergeType vs Gimp.MergeType

    @classmethod
    def dotted_name_of_short_name(cls, short_name):
        # Qualify with Gimp namespace
        return "Gimp." + short_name

    @classmethod
    def name_of_type(cls, enum):
        # assert enum is e.g. Gimp.MergeType
        result = enum.__name__
        cls.logger.debug(f"name_of_type {result}")
        # assert result like "Gimp.MergeType", a string
        return result

    @classmethod
    def dotted_name_of_type(cls, enum):
        """ Return dotted name of a Gimp enum type.
        Its a name in Python, not the long name in C.
        """
        return cls.dotted_name_of_short_name(cls.short_name_of_type(enum))



    """ Names to/from types """

    @classmethod
    def short_name_of_type(cls, type):
        # assert type e.g. GimpMergeType (not a string, but a ref to type)
        return cls.short_name_of_type_name(cls.name_of_type(type))

    @classmethod
    def type_from_short_name(cls, short_name):
        """ Return reference to a Gimp.<type> """

        """
        Use eval to convert string to reference to a type.
        Not work: exec("result = " +  cls.dotted_name_of_short_name(short_name))
        """
        eval_string = cls.dotted_name_of_short_name(short_name)
        result = eval(eval_string)
        cls.logger.debug(f"type_from_short_name: {result}")
        # assert result is-a reference to a Gimp.<type>
        return result

        """
        This does not work reliably????
        type_name = type_name_from_short_name(name)
        enum_gtype  = GObject.GType.from_name (type_name)
        """
