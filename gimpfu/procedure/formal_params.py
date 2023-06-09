
from gimpfu.procedure.formal_param import FuFormalParam
from gimpfu.procedure.type import FuProcedureType

from gimpfu.enums.gimpfu_enums import *  # PF_ enums

from gimpfu.message.deprecation import Deprecation
from gimpfu.message.proceed import proceed

import logging


class FuFormalParams():
    '''
    A set of FuFormalParams.

    Distinct from the other metadata.

    Responsibilities:
    - keep a list of FuFormalParams
    - fixups on self
    - convey self to Gimp

    A thin wrapper around a list of FuFormalParam
    '''

    # Constant class data
    # These are GimpFu instance representing required formal params of the PDB procedure
    file_params = [FuFormalParam(PF_STRING, "filename", "The name of the file", ""),
                   FuFormalParam(PF_STRING, "raw-filename", "The name of the file", "")]
    image_param = FuFormalParam(PF_IMAGE, "image", "Input image", None)
    drawable_param = FuFormalParam(PF_DRAWABLE, "drawable", "Input drawable", None)

    logger = logging.getLogger("GimpFu.FuFormalParams")



    def __init__(self, owner_name):
        self.owner_name = owner_name
        self.PARAMS= []


    # Iterator protocol: delegated to owned list
    def __iter__(self):
        return self

    def __next__(self):
        # Python 3, use builtin next(iterator), except Python list is not an iterator
        return next(iter(self.PARAMS))



    def append(self, *args):
        self.PARAMS.append(FuFormalParam(*args))


    def sanity_test(self, metadata):
        unique_names = []
        """
        # TODO: this doesn't work because GimpFu allows user to declare or not declare args that Gimp always passes.
        # since we are using the names to convey properties to Gimp,
        # disallow names already used by Gimp for properties
        unique_names.append("image")
        unique_names.append("drawable")
        """
        for param in self.PARAMS:
            """
            TODO
            if len(ent) < 4:
                raise Exception( ("parameter definition must contain at least 4 "
                              "elements (%s given: %s)" % (len(ent), ent)) )
            """

            if not isinstance(param.PF_TYPE, int):
                # TODO check in range
                exception_str = f"Plugin parameter type {param.PF_TYPE} not a valid PF_ enum"
                raise Exception(exception_str)


            # Fixup common mistake is a space in the LABEL
            param.LABEL = param.LABEL.replace( ' ' , '_')

            if not metadata.letterCheck(param.LABEL, metadata.param_name_allowed):
                # Not fatal since we don't use it, args are a sequence, not by keyword
                # But Gimp may yet complain.
                # TODO transliterate space to underbar
                proceed(f"parameter name '{param.LABEL}' contains illegal characters")

            # Check for unique names.  To convey to Gimp, must be unique.
            # Names do NOT need to match the formal params of the run_func
            if param.LABEL in unique_names:
                proceed(f"parameter name '{param.LABEL}' is not unique")
            else:
                unique_names.append(param.LABEL)



    def deriveMissingParams(self, metadata):
        """ FBC Add missing params according to plugin type.
        Returns True when insert params.
        """

        '''
        FBC.
        In the distant past, an author could specify menu like <Load>
        and not provide a label
        and not provide the first two params,
        in which case GimpFu inserts two params.
        Similarly for other cases.
        '''

        result = False

        # v2 if self.did_fix_menu and plugin_type == PLUGIN:
        # require _deriveMissingMenu called earlier
        if metadata.is_new_style_registration:
            # specified params are explict, requires no fix
            pass
        elif metadata.type == FuProcedureType.Load :
            # insert into slice
            self.PARAMS[0:0] = FuFormalParams.file_params
            Deprecation.say(" Fixing two file params for Load plugin")
            result = True
        elif ( metadata.type == FuProcedureType.Image
             or metadata.type == FuProcedureType.Save) :
            self.PARAMS.insert(0, FuFormalParams.image_param)
            self.PARAMS.insert(1, FuFormalParams.drawable_param)
            Deprecation.say(" Fixing two image params for Image or Save plugin")
            if metadata.type == FuProcedureType.Save:
                self.PARAMS[2:2] = file_params
                Deprecation.say(" Fixing two file params for Save plugin")
            result = True
        #print(self.PARAMS)
        return result


    def deriveMissingImageParams(self, metadata):
        '''
        Some plugins declare they are <Image> plugins,
        but don't have first two params equal to (image, drawable),
        and have imagetype == "" (menu item enabled even if no image is open).
        And then Gimp refuses to create procedure
        (but does create an item in pluginrc!)
        E.G. sphere.py

        So we diverge the signature of the plugin from the signature of the run_func.
        The author might be unaware, unless they explore,
        or try to call the PDB procedure from another PDB procedure.

        TODO after we are done, the count of args to run_func
        and the count of formal parameters (PARAMS) should be the same.
        Can we count the formal parameters of run_func?
        '''

        result = False
        # if missing params (never there, or not fixed by earlier patch)
        # TODO if params are missing altogether
        if ( metadata.type == FuProcedureType.Image ) :
            # fix missing image declaration
            if ( (len(self.PARAMS) > 0)
                and self.PARAMS[0].PF_TYPE != PF_IMAGE
                ) :
                # FuFormalParams.logger
                Deprecation.say(f"Missing image param for Image type plugin {self.owner_name}")
                self.PARAMS.insert(0, FuFormalParams.image_param)
                result = True
            if ( (len(self.PARAMS) > 1)
                and self.PARAMS[1].PF_TYPE != PF_DRAWABLE
                ) :
                Deprecation.say("Missing drawable param for Image plugin")
                self.PARAMS.insert(1, FuFormalParams.drawable_param)
                result = True
        return result


    def convey_to_gimp(self, procedure, count_omitted_leading_args, is_in_arg):
        ''' Convey  to Gimp a formal declaration of args to/from the procedure.
        when is_in_arg, convey args to
        else convey return args
        Returns count of conveyed args.
        '''

        count = 0
        for i in range(count_omitted_leading_args, len(self.PARAMS)):
            # FuFormalParams.logger.debug(f"Convey arg type {self.PARAMS[i]}")
            self.PARAMS[i].convey_to_gimp(procedure, i, is_in_arg)
            count += 1
        FuFormalParams.logger.debug(f"convey_to_gimp, conveyed count: {count}")
        return count
