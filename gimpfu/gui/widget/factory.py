

# WidgetFactory is main use of PF_enum
from gimpfu.enums.gimpfu_enums import *

# WidgetFactory is main use of Widget constructors

# widget classes grouped by how implemented
from gimpfu.gui.widget.primitive  import *
from gimpfu.gui.widget.float      import *
from gimpfu.gui.widget.range      import *
from gimpfu.gui.widget.gimp       import *
from gimpfu.gui.widget.gtk        import *
from gimpfu.gui.widget.resource   import *
from gimpfu.gui.widget.brush      import *
from gimpfu.gui.widget.color      import *

from gimpfu.procedure.extras import Extras

from gimpfu.adapters.rgb import GimpfuRGB

import logging



class WidgetFactory:

    logger = logging.getLogger("GimpFu.WidgetFactory")

    def does_widget_have_view(a_formal_param):
        return a_formal_param.PF_TYPE == PF_TEXT


    def produce(a_formal_param, guiable_initial_value):
        """ Produce a widget described by formal_param, having initial value. """

        # TODO widget types not range checked earlier
        # author COULD err by specifying out of range widget type

        try:
            #  e.g. widget_constructor = StringEntry
            widget_constructor = _edit_map[a_formal_param.PF_TYPE]
        except KeyError:
            exception_str = f"Invalid or not implemented PF_ widget type: {a_formal_param.PF_TYPE}"
            raise Exception(exception_str)

        widget_initial_value = guiable_initial_value

        proc_name = 'bar' # TODO procedure.procedure_name()

        args_for_widget_constructor = WidgetFactory._get_args_for_widget_constructor(a_formal_param, widget_initial_value)

        # TODO pass tooltip_text
        # tooltip_text = a_formal_param.tooltip_text)

        WidgetFactory.logger.debug(f"produce: {widget_constructor}, args: {args_for_widget_constructor}")

        if args_for_widget_constructor:
            result = widget_constructor(*args_for_widget_constructor)
        else:
            result = widget_constructor()

        return result


    def is_gimp_widget(a_formal_param):
        """ Does the widget wrap i.e. own a Gimp widget (for ephemeral Gimp objects) """
        return a_formal_param.PF_TYPE in (PF_IMAGE, PF_DRAWABLE, PF_LAYER, PF_CHANNEL, PF_VECTORS)

    def is_wrapped_widget(a_formal_param):
        """ Do we wrap a Gimp widget (for which inheriting fails.) """
        return ( WidgetFactory.is_gimp_widget(a_formal_param)
                or a_formal_param.PF_TYPE == PF_COLOR
                or a_formal_param.PF_TYPE == PF_SPINNER
                or a_formal_param.PF_TYPE == PF_SLIDER
                )



    def _enumerate_names(names_tuple):
        result = [(count, name) for name, count in enumerate(names_tuple)]
        # assert result like [(name1, 0), (name2, 1), ...]
        return result


    def _get_args_for_widget_constructor(formal_param, widget_initial_value):
        ''' Get args for a widget constructor from formal spec.
        Override formal declaration of default with widget_initial_value.
        Returns list of args.
        Args are (<initial value>, <title>, <extras i.e. constraints> )
        '''
        WidgetFactory.logger.debug(f"_get_args_for_widget_constructor, {formal_param}, {widget_initial_value}")
        # This is a switch statement on  PF_TYPE
        # Since data comes from , don't trust it
        pf_type = formal_param.PF_TYPE

        if pf_type in ( PF_RADIO, ):
            """
            widget_initial_value is-a int?? Allow string values???

            EXTRAS is tuple of tuples: ((name, value), ...)
            """
            args = [widget_initial_value, formal_param.EXTRAS]
        elif pf_type in ( PF_OPTION, ):
            """
            EXTRAS is tuple of names without values: (name, ...)
            """
            # Enumerate the names into tuple of name/value pairs
            args = [widget_initial_value, WidgetFactory._enumerate_names(formal_param.EXTRAS)]
        elif pf_type in (PF_FILE, PF_FILENAME, PF_DIRNAME):
            # args template [<title>, <default>]

            # TEMP: when widget is omitted, use default defined by author
            # args = [widget_initial_value,]

            # TEMP: when ProcedureConfig broken, use a string default here
            # args = [formal_param.LABEL, "/tmp/lkkfoopluginout"]

            args = [formal_param.LABEL, widget_initial_value]
        elif pf_type in (PF_INT, PF_INT8, PF_INT16, PF_INT32, PF_STRING, PF_BOOL,  PF_TEXT ):
            args = [widget_initial_value]
        elif pf_type in (PF_FLOAT, ):
            # Using FloatEntry, no range specified
            args = [widget_initial_value,]
        elif pf_type in (PF_SLIDER, PF_SPINNER, ):
            # Hack, we are using FloatEntry, should use Slider???
            minMaxStepTuple = Extras.derive_min_max_step_from_extras(pf_type, formal_param.EXTRAS)
            args = [widget_initial_value, minMaxStepTuple]
        elif pf_type == PF_COLOR:
            # require widget_initial_value is-a string, name of color, or is-a 3-tuple of RGB ints
            # TODO, if initial_value came from ProcedureConfig, could be wrong
            # TODO Widget omitted
            # color = GimpfuRGB.color_from_python_type(widget_initial_value)

            # temporarily using a constant color
            color = GimpfuRGB.color_from_python_type("orange")
            # title is DESC, not LABEL
            args = [color, formal_param.DESC]
        elif pf_type in (PF_FONT, PF_PALETTE, PF_PATTERN, PF_BRUSH, PF_GRADIENT):
            # PF_PALETTE is special ???
            args = [widget_initial_value,]
        elif WidgetFactory.is_gimp_widget(formal_param):
            # pf_type in (PF_IMAGE, PF_DRAWABLE, PF_LAYER, PF_CHANNEL, PF_VECTORS):
            args = None   # [None,]
        elif pf_type in (PF_DISPLAY, PF_ITEM):
            # TODO proceed
            raise NotImplementedError(f"Not implemented: GUI to choose Item or Display.")
        else:
            # PF_SPINNER,
            raise RuntimeError(f"Unhandled PF_ widget type {pf_type}.")

        return args



'''
Map PF_ enum to Widget class

Key is-a PF_ enum.
Value is-a FuWidget class.

Many-to-one.
Many PF_enums map to same FuWidget class.

A FuWidget class is also many-to-one with Gtk widgets.
E.g. a Gtk string entry widget may be used to enter both strings and ints.
The FuWidget class may convert types yielded by Gtk widgets.

A PF_enum specifies both the look and feel of the widget,
and the type yielded by the widget, back to GimpFu.
(Except in v2, a PF_RADIO could yield either an int or str type.)

Currently a PF_enum may describe a more restrictive type (E.G. INT8)
than the FuWidget class yields (E.G. INT)
but in some cases that is not enforced at GUI time.

The formal param spec declares a PF_ enum, as well as an EXTRAS.
EXTRAS further specifies parameters of the FuWidget class,
and the widget enforces that type restriction at GUI time.

Feb. 2020 status:
complete keys, but using OmitteEntry for not implemented widgets.
For omitted, subsequently GimpFu uses the default value which should be sane.
'''
_edit_map = {
        # Single-valued, simple widgets
        PF_INT         : IntEntry,
        PF_INT8        : IntEntry,
        PF_INT16       : IntEntry,
        PF_INT32       : IntEntry,

        # both return strings, just different widgets?
        PF_STRING      : StringEntry,
        PF_TEXT        : StringEntry,

        # checkbox
        # both return bool,  just different widgets?
        PF_BOOL        : ToggleEntry,
        PF_TOGGLE      : ToggleEntry,  # alias for PF_BOOL

        # TODO slider and spinner floats, or int?
        # PF_ADJUSTMENT is alias for PF_SPINNER
        PF_FLOAT       : FloatEntry,
        PF_SLIDER      : SliderWidget,
        PF_SPINNER     : SpinnerWidget,

        # finite set of choices: two look-and-feels
        # radio button group, values are declared
        PF_RADIO       : RadioButtonsEntry,
        # pull down option menu widget,  values not declared, always int-valued
        PF_OPTION      : OptionMenuEntry,

        # PF_COLOUR is deprecated alias for PF_COLOR
        PF_COLOR       : FuColorWidget,

        # TODO is PF_FILENAME deprecated alias for PF_FILE?
        PF_FILE        : FuFileEntry,
        PF_FILENAME    : FuFileEntry,
        PF_DIRNAME     : FuDirEntry,

        # ??? meaning?
        PF_VALUE       : OmittedEntry,

        # Widgets provided by Gimp for Gimp ephemeral objects
        # Doesn't work to reference GimpUi.DrawableComboBox, the class is not a constructor??
        # must call GimpUi.DrawableComboBox.new() by a G_OBJECT_WARN_INVALID_PROPERTY_ID
        PF_ITEM        : OmittedEntry,  # TODO user has no use for a generic item
        PF_DISPLAY     : OmittedEntry,  # GimpUi has no widget

        # Subclasses of GimpUi.IntComboBox returning a Gimp.Item.ID
        PF_IMAGE       : FuImageWidget,
        PF_LAYER       : FuLayerWidget,
        PF_CHANNEL     : FuChannelWidget,
        PF_DRAWABLE    : FuDrawableWidget,
        PF_VECTORS     : FuVectorsWidget,

        # Widgets provided by Gimp for Gimp data objects?
        # "data" objects are loaded at run-time, not as ephemeral
        # i.e. configured, static data of the app
        PF_FONT        : FuFontWidget,
        PF_BRUSH       : FuBrushWidget,
        PF_PATTERN     : FuPatternWidget,
        PF_GRADIENT    : FuGradientWidget,
        # formerly gimpui.palette_selector
        # Now I think palette is a parameter, but should not have a control?
        # since the currently selected palette in palette dialog is passed for context menu plugins?
        # Still could have a use by other plugins?
        PF_PALETTE     : FuPaletteWidget,
        }
