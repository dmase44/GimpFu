
import gi

gi.require_version("Gimp", "3.0")
from gi.repository import Gimp

from gimpfu.procedureConfig.procedure_config import FuProcedureConfig
from gimpfu.procedures.procedures import FuProcedures

from gimpfu.adaption.marshal import Marshal

from gimpfu.message.proceed import summarize_proceed_errors
from gimpfu.message.deprecation import Deprecation
from gimpfu.message.suggest import Suggest

from gimpfu.runner.result import FuResult

# See below, more, alternative imports

import logging


"""
Understands how to run a GimpFu procedure
from Gimp's callback to the registered run function.
An author registers a run_func,
GimpFu interposes and registers a wrapped run_func
e.g. run_imageprocedure which calls the author's run_func

Hides:
- adaption of signatures
- GimpFu's hiding of runmode
- GimpFu's messaging

Class was extracted from code formerly in gimpfu_top
"""

class FuRunner:

    logger = logging.getLogger('GimpFu.FuRunner')

    @staticmethod
    def show_exception_dialog(fuProcedure):
        """ Show a modal exception dialog. """
        # TODO seems to be modal, is it?
        from gimpfu.gui.exception_dialog import ExceptionDialog

        ExceptionDialog.show(fuProcedure)
        exc_str, exc_only_str = ExceptionDialog.create_exception_str()
        return exc_str, exc_only_str


    @staticmethod
    def _try_run_func(fuProcedure, function, args):
        '''
        Run the plugin's run_func with args, catching exceptions.
        Return result of run_func.

        This is always non-headless (interactive.)
        But not require an image open.
        Show dialog on exception.
        '''
        try:
            result = function(*args)
        except TypeError:
            # TODO catch this earlier
            from gimpfu.gui.exception_dialog import ExceptionDialog

            exc_str, exc_only_str = ExceptionDialog.create_exception_str()

            # Show a more informative message for a limitation of GimpFu
            if "'gi.FunctionInfo' object is not subscriptable" in exc_str:
                """
                TODO Fix this ???
                Example author code:
                  frisketBounds = grownSelection.mask_bounds
                  frisketLowerLeftX = frisketBounds[0]
                This means either:
                1. GimpFu forgot to implement property mask_bounds
                2. or author combined property with [] e.g. grownSelection.mask_bounds[0]
                """
                FuRunner.logger.critical(f"GimpFu can't subscript pdb methods.  Split the statement.")
                # TODO show a Gimp dialog?
            raise
        except:
            # TODO Show dialog here, or pass exception string back to Gimp or both ???
            exc_str, exc_only_str = FuRunner.show_exception_dialog(fuProcedure)
            FuRunner.logger.critical(f"{exc_str}, {exc_only_str}")
            result = None
            # TODO either pass exc_str back so Gimp shows in dialog,
            # or reraise so Gimp shows a generic "plugin failed" dialog
            # or show our own dialog above
            raise
        return result







    @staticmethod
    def _interact(gimpProcedure, list_wrapped_args, config):
        '''
        Show GUI when guiable args, then execute run_func.
        Progress will show in Gimp window, not dialog window.

        Returns (was_canceled, (results of run_func or None))
        '''
        '''
        Note display/window is global state, not passed.
        # TODO assume first arg is likely an image
        # display = Display.get(proc_name, list_wrapped_args[0])

        from gui.display import Display
        display = Display.get_window(proc_name)
        '''


        # name from instance of Gimp.Procedure
        proc_name = gimpProcedure.get_name()
        FuRunner.logger.info(f"_interact, {proc_name}, {list_wrapped_args}")

        # Use the instance of FuProcedure, it has all data about the procedure
        fuProcedure = FuProcedures.get_by_name(proc_name)

        function = fuProcedure.metadata.FUNCTION

        guiable_formal_params =  fuProcedure.guiable_formal_params

        """
        CRUFT from implementation where dialog executed run_script
        guiable_formal_params =  fuProcedure.guiable_formal_params
        nonguiable_actual_args, guiable_actual_args = fuProcedure.split_guiable_actual_args(list_wrapped_args)

        # effectively a closure, partially bound to function, nonguiable_actual_args
        # passed to show_plugin_dialog to be executed after dialog
        def run_script(guiable_actual_args):
            # guiable_actual_args may have been altered by the GUI from earlier values
            nonlocal function
            nonlocal nonguiable_actual_args

            wrapped_run_args = fuProcedure.join_nonguiable_to_guiable_args(nonguiable_actual_args,  guiable_actual_args)
            FuRunner.logger.info("wrapped_run_args", wrapped_run_args)
            '''
            invoke Authors func on unpacked args
            !!! Authors func never has run_mode, Gimpfu hides need for it.
            '''
            result = function(*wrapped_run_args)
            return result
        """



        if len(guiable_formal_params) == 0:
            # Just execute, don't open ControlDialog, but may show ExceptionDialog
            FuRunner.logger.info("no guiable parameters")
            was_canceled = False
            # !!! no gui can change the in_args
            result = FuRunner._try_run_func(fuProcedure, function, list_wrapped_args)
        else:
            # create GUI from guiable formal args, let user edit actual args

            #TODO duplicate??
            fuProcedure.on_run()

            """
            The procedure knows what its guiable args are (versus args such as "image", already fixed and not guiable).
            The guiable args are similar to a ProcedureConfig.
            Here we use the GimpFu implementation.
            Instead, we could just use the config?
            """
            nonguiable_actual_args, guiable_actual_args = fuProcedure.split_guiable_actual_args(list_wrapped_args)
            # FuRunner.logger.info(f"in guiable args: {guiable_actual_args}")

            """ Choice of implementation here. """

            # choice 1: use gimpfu.gui
            from gimpfu.gui.gimpfu_controls_runner import GimpFuControlsRunner
            was_canceled, guied_args = GimpFuControlsRunner.run(
                fuProcedure, gimpProcedure, list_wrapped_args, guiable_formal_params)

            # choice 2: use GimpUi
            # WIP April 23, 2020 works with many missing widgets and proceeds past many errors in GIMP
            #from gimpfu.gui.gimp_controls_runner import GimpControlsRunner
            #was_canceled, guied_args = GimpControlsRunner.run(
            #    fuProcedure, gimpProcedure, config)    # , list_wrapped_args, guiable_formal_params)

            # assert results from dialog are primitives or unwrapped GIMP objects

            if not was_canceled :
                # config takes unwrapped guied args
                config.set_changed_settings(guied_args)

                wrapped_guied_args = Marshal.wrap_args(guied_args)
                wrapped_run_args = fuProcedure.join_nonguiable_to_guiable_args(nonguiable_actual_args, wrapped_guied_args)
                FuRunner.logger.info(f"Wrapped args to run_func, {wrapped_run_args}" )

                # !!! with args changed by user
                result = FuRunner._try_run_func(fuProcedure, function, wrapped_run_args)
            else:
                # Don't save changes to config i.e. settings
                result = None
                pass

        return was_canceled, result



    """
    The main exposed methods.

    These are registered with Gimp as the run_func of GimpFu procedures.
    These are callbacks from Gimp.

    These are GimpFu wrappers of the Authors "main" function, aka run_func.
    That is, Gimp calls these, and these call the Author's run_func, after mangling args.

    There are several variants, each specializing mangling of args.
    Mangle args to fit our generic runner: _run_procedure_in_mode

    The call tree for example is:
      Gimp
      run_imageprocedure or a variant
      _run_procedure_in_mode
      Author's run_func
    """

    '''
    Since 3.0, changed the signature of _run():
    - parameters not in one tuple
    - type of 'procedure' parameter is GimpImageProcedure, not str.
    v2, most parameters were in one tuple.

    XXXNow the first several are mandatory and do not need to be declared when registering.
    XXXIn other words, formerly their declarations were boilerplate, repeated often for little practical use.

    Since 3.0,
    when the plugin procedure is of type Gimp.ImageProcedure
    the parameter actual_args only contains arguments special to given plugin instance,
    and the first two args (image and drawable) are passed separately.

    !!! The args are always as declared when procedure created.
    It is only when they are passed to the procedure that they are grouped
    in different ways (some chunked into a Gimp.ValueArray)

    Also formerly the first argument was type str, name of proc.
    Now it is of C type GimpImageProcedure or Python type ImageProcedure

    !!! Args are Gimp types, not Python types
    '''

    '''
    Several versions, circa 2.99.6 the signature changed for multi-layer.
    OLD: single      ..., drawable, ...
    NEW: multiple    ..., count_drawables, drawables_array, ...  explicitly passing the count
    NEW2: multiple   ..., drawables_array, ...                   not passing the count


    Create the procedure registering one of these two run funcs.
    '''

    '''
    Note that PyGObject binding:
        makes drawables a list
        should eat count_drawables, but doesn't (unlike binding for Lua)
    '''

    @staticmethod
    def run_imageprocedure_multiple(procedure, run_mode, image, count_drawables, drawables, original_args, data):
        """
        Run procedure on multiple drawables
        """
        # For now, not implement multi-layer functionality
        if len(drawables) > 1 :
            FuResult.makeException(procedure, "GimpFu does not support multi-layer yet.")
        else:
            drawable = drawables[0]

        result = FuRunner.run_imageprocedure_on_drawable(procedure, run_mode, image, drawable, original_args, data)
        return result


    @staticmethod
    def run_imageprocedure_on_drawable(procedure, run_mode, image, drawable, original_args, data):
        ''' run procedure on a single drawable. '''
        FuRunner.logger.info(f"run_imageprocedure , {procedure}, {run_mode}, {image}, {drawable}, {original_args}")

        '''
        Create list of *most* args.
        *most* means (image, drawable, *original_args), but not run_mode!
        List elements are GValues, not wrapped yet!
        '''
        list_all_args = Marshal.prefix_image_drawable_to_run_args(original_args, image, drawable)

        result = FuRunner._run_procedure_in_mode(procedure, run_mode, image, list_all_args, original_args, data)
        return result


    @staticmethod
    def run_context_procedure(procedure, original_args, data):
        """ Mangle args for a procedure of type/signature Context

        For a procedure invoked from a context menu,
        operating on an instance of a "Gimp resource".
        Resource is "Gimp data" e.g. Vectors, Brush, ... OR a Drawable ???

        The signature is as defined by Gimp C code.
        (run mode, image, resource, ...)
        """
        FuRunner.logger.info(f"run_context_procedure , {procedure}, {original_args}, {data}")

        list_gvalues_all_args = Marshal.convert_gimpvaluearray_to_list_of_gvalue(original_args)
        # assert is (runmode, image, <Gimp data object>, guiable_args)
        FuRunner.logger.info(f"run_context_procedure, args: {list_gvalues_all_args}")

        # context procedures have a run-mode
        run_mode = list_gvalues_all_args[0]  #
        # move run mode arg out of passed GimpValueArray
        # We use the current run mode
        list_gvalues_all_args.pop(0)

        image = list_gvalues_all_args[0]
        assert ((image is None) or isinstance(image, Gimp.Image))

        # assert list_gvalues_all_args[1] is an instance or name of isinstance
        # that was selected by user from a context menu e.g. Vectors or Brush

        result = FuRunner._run_procedure_in_mode(procedure, run_mode, image, list_gvalues_all_args, original_args, data)
        return result


    @staticmethod
    def run_other_procedure(procedure, original_args, data):
       """ Mangle args for a procedure of type/signature Other """
       FuRunner.logger.info(f"run_other_procedure: {procedure}, {original_args}, {data}")

       list_gvalues_all_args = Marshal.convert_gimpvaluearray_to_list_of_gvalue(original_args)

       # Gimp passes run_mode to other procedures

       # remove run mode arg from passed GimpValueArray
       #list_gvalues_all_args.pop(0)

       # Always NONINTERACTIVE, run mode not passed by GIMP
       run_mode = Gimp.RunMode.NONINTERACTIVE
       image = None

       # No assertions about the the args, could be empty

       result = FuRunner._run_procedure_in_mode(procedure, run_mode, image, list_gvalues_all_args, original_args, data)
       return result




    @staticmethod
    def _run_procedure_in_mode(procedure, run_mode, image, list_all_args, original_args, data):
        '''
        Understands run_mode.
        Different ways to invoke procedure batch, or interactive.

        Hides run_mode from Authors.
        I.E. their run_func signature does not have run_mode.

        require procedure is-a Gimp.Procedure.
        require original_args is-a Gimp.ValueArray.
        require list_all_args is a list of GValues
        '''
        list_wrapped_args = Marshal.wrap_args(list_all_args)

        # To know the Python name of a Gimp.Procedure method (e.g. gimp_procedure_get_name)
        # see gimp/libgimp/gimpprocedure.h, and then remove the prefix gimp_procedure_
        name = procedure.get_name()

        FuRunner.logger.info(f"_run_procedure_in_mode: {name}, {run_mode}, {list_wrapped_args}")
        '''
        list_wrapped_args are one-to-one with formal params.
        list_wrapped_args may include some args that are not guiable (i.e. image, drawable)
        '''

        fuProcedure = FuProcedures.get_by_name(name)

        isBatch = (run_mode == Gimp.RunMode.NONINTERACTIVE)
        '''
        Else so-called interactive mode, with GUI dialog of params.
        Note that the v2 mode RUN_WITH_LAST_VALS is obsolete
        since Gimp 3 persists settings, i.e. actual arg values can be from last invocation.
        If not from last invocation, they are the formal parameter defaults.
        '''

        func = fuProcedure.get_authors_function()

        """
        The ProcedureConfig should have length equal to ????
        original_args is-a GimpValueArray
        """
        # config = FuProcedureConfig(procedure, len(list_wrapped_args)-2 )
        config = FuProcedureConfig(fuProcedure, procedure, original_args.length() )
        config.begin_run(image, run_mode, original_args)

        if isBatch:
           try:
               # invoke func with unpacked args.  Since Python3, apply() gone.
               # TODO is this the correct set of args? E.G. Gimp is handling RUN_WITH_LAST_VALS, etc. ???
               runfunc_result = func(*list_wrapped_args)
               final_result = FuResult.makeSuccess(procedure, runfunc_result)
           except Exception as err:
               # TODO print the Exception type
               err_message = f"In plugin: {name}, function: {func}, Exception: {err}"
               FuRunner.logger.warning(err_message)
               final_result = FuResult.makeException(procedure, err_message)
        else:
           '''
           Not enclosed in try:except: since then you don't get a good traceback.
           Any exceptions in showing a dialog are hard programming errors.
           Any exception in executing the run_func should be shown to user,
           either by calling our own dialog or by calling a Gimp.ErrorDialog (not exist)
           or by passing the exception string back to Gimp.
           '''
           was_canceled, runfunc_result = FuRunner._interact(procedure, list_wrapped_args, config)
           if was_canceled:
               final_result = FuResult.makeCancel(procedure)
               config.end_run(Gimp.PDBStatusType.CANCEL)
           else:
               final_result = FuResult.makeSuccess(procedure, runfunc_result)
               config.end_run(Gimp.PDBStatusType.SUCCESS)
           """
           OLD above was enclosed in try
           try:
           except Exception as err:
               '''
               Probably GimpFu module programming error (e.g. bad calls to GTK)
               According to GLib docs, should be a warning, since this is not recoverable.
               But it might be author programming code (e.g. invalid PARAMS)
               '''
               proceed(f"Exception opening plugin dialog: {err}")
               final_result = FuResult.make(Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())
           """

        '''
        Make visible any alterations to user created images.
        GimpFu promises to hide the need for this.
        '''
        Gimp.displays_flush()   # !!! Gimp, not gimp

        did_suggest_or_deprecate = Suggest.summarize()
        did_suggest_or_deprecate = did_suggest_or_deprecate or Deprecation.summarize()

        if did_suggest_or_deprecate:
            # TODO make this go to the status bar, not a dialog
            # Gimp.message("See console for suggestions and deprecations.")
            pass

        if summarize_proceed_errors():  # side effect is writing to console
            """ Gimpfu proceeded past earlier exceptions.
            Display GIMP dialog.
            """
            msg = "GimpFu detected errors.  See console for a summary."
            Gimp.message(msg)
            final_result = FuResult.makeException(procedure, msg)

            # Alternatively: raise Exception(msg) but that is confusing to Author

        FuRunner.logger.debug(f"Returning from: {name} with result:{final_result}")
        # ensure final_result is type GimpValueArray
        assert isinstance( final_result, Gimp.ValueArray)
        return final_result


    '''
    v2
    def _run(proc_name, params):
        run_mode = params[0]
        func = _registered_plugins_[proc_name][10]

        if run_mode == RUN_NONINTERACTIVE:
            return apply(func, params[1:])

        script_params = _registered_plugins_[proc_name][8]

        min_args = 0
        if len(params) > 1:
            for i in range(1, len(params)):
                param_type = _obj_mapping[script_params[i - 1][0]]
                if not isinstance(params[i], param_type):
                    break

            min_args = i

        if len(script_params) > min_args:
            start_params = params[:min_args + 1]

            if run_mode == RUN_WITH_LAST_VALS:
                default_params = _get_defaults(proc_name)
                params = start_params + default_params[min_args:]
            else:
                params = start_params
        else:
           run_mode = RUN_NONINTERACTIVE

        if run_mode == RUN_INTERACTIVE:
            try:
                res = _interact(proc_name, params[1:])
            except CancelError:
                return
        else:
            res = apply(func, params[1:])

        gimp.displays_flush()

        return res
    '''
