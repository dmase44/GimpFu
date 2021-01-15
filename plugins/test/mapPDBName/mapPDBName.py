
'''
GimpFu plugin
that:
- has one parameter
- maps deprecated names
'''

from gimpfu import *

"""
map is generated by scripts in testGimpPDB.git in the testPDB gimp_directory

There are two kinds of deprecations here:
- MUST be mapped
  The old name still exists but with a signature changed.
  If not mapped, later get an error: "wrong arguments"
- COULD be mapped
  The old name exists (usually) and with the same signature.
  If not mapped, the old name will still work
  (the procedure having the old name is usually a "compatibility" procedure,
  i.e. just a thin wrapper on the new name.)

Author SHOULD change their scripts.
In the future, both kinds of deprecations could become obsoletions.
That is, this mapping could be emptied, and the "compatibility" procedures deleted.
"""

map = {
"gimp-brightness-contrast"               : "gimp-drawable-brightness-contrast"      ,
"gimp-brushes-get-brush"                 : "gimp-context-get-brush"                 ,
"gimp-drawable-is-channel"               : "gimp-item-id-is-channel"                ,
"gimp-drawable-is-layer"                 : "gimp-item-id-is-layer"                  ,
"gimp-drawable-is-layer-mask"            : "gimp-item-id-is-layer-mask"             ,
"gimp-drawable-is-text-layer"            : "gimp-item-id-is-text-layer"             ,
"gimp-drawable-is-valid"                 : "gimp-item-id-is-valid"                  ,
"gimp-drawable-transform-2d"             : "gimp-item-transform-2d"                 ,
"gimp-drawable-transform-flip"           : "gimp-item-transform-flip"               ,
"gimp-drawable-transform-flip-simple"    : "gimp-item-transform-flip-simple"        ,
"gimp-drawable-transform-matrix"         : "gimp-item-transform-matrix"             ,
"gimp-drawable-transform-perspective"    : "gimp-item-transform-perspective"        ,
"gimp-drawable-transform-rotate"         : "gimp-item-transform-rotate"             ,
"gimp-drawable-transform-rotate-simple"  : "gimp-item-transform-rotate-simple"      ,
"gimp-drawable-transform-scale"          : "gimp-item-transform-scale"              ,
"gimp-drawable-transform-shear"          : "gimp-item-transform-shear"              ,
"gimp-display-is-valid"                  : "gimp-display-id-is-valid"               ,
"gimp-image-is-valid"                    : "gimp-image-id-is-valid"                 ,
"gimp-item-is-channel"                   : "gimp-item-id-is-channel"                ,
"gimp-item-is-drawable"                  : "gimp-item-id-is-drawable"               ,
"gimp-item-is-layer"                     : "gimp-item-id-is-layer"                  ,
"gimp-item-is-layer-mask"                : "gimp-item-id-is-layer-mask"             ,
"gimp-item-is-selection"                 : "gimp-item-id-is-selection"              ,
"gimp-item-is-text-layer"                : "gimp-item-id-is-text-layer"             ,
"gimp-item-is-valid"                     : "gimp-item-id-is-valid"                  ,
"gimp-item-is-vectors"                   : "gimp-item-id-is-vectors"                ,
"gimp-procedural-db-dump"                : "gimp-pdb-dump"                          ,
"gimp-procedural-db-get-data"            : "gimp-pdb-get-data"                      ,
"gimp-procedural-db-set-data"            : "gimp-pdb-set-data"                      ,
"gimp-procedural-db-get-data-size"       : "gimp-pdb-get-data-size"                 ,
"gimp-procedural-db-proc-arg"            : "gimp-pdb-get-proc-argument"             ,
"gimp-procedural-db-proc-info"           : "gimp-pdb-get-proc-info"                 ,
"gimp-procedural-db-proc-val"            : "gimp-pdb-get-proc-return-value"         ,
"gimp-procedural-db-proc-exists"         : "gimp-pdb-proc-exists"                   ,
"gimp-procedural-db-query"               : "gimp-pdb-query"                         ,
"gimp-procedural-db-temp-name"           : "gimp-pdb-temp-name"                     ,
"gimp-image-get-exported-uri"            : "gimp-image-get-exported-file"           ,
"gimp-image-get-imported-uri"            : "gimp-image-get-imported-file"           ,
"gimp-image-get-xcf-uri"                 : "gimp-image-get-xcf-file"                ,
"gimp-image-get-filename"                : "gimp-image-get-file"                    ,
"gimp-image-set-filename"                : "gimp-image-set-file"                    ,
"gimp-plugin-menu-register"              : "gimp-pdb-add-proc-menu-path"            ,
"gimp-plugin-domain-register"            : "gimp-plug-in-domain-register"           ,
"gimp-plugin-get-pdb-error-handler"      : "gimp-plug-in-get-pdb-error-handler"     ,
"gimp-plugin-help-register"              : "gimp-plug-in-help-register"             ,
"gimp-plugin-menu-branch-register"       : "gimp-plug-in-menu-branch-register"      ,
"gimp-plugin-set-pdb-error-handler"      : "gimp-plug-in-set-pdb-error-handler"     ,
"gimp-plugins-query"                     : "gimp-plug-ins-query"                    ,
"file-gtm-save"                          : "file-html-table-save"                   ,
"python-fu-histogram-export"             : "histogram-export"                       ,
"python-fu-gradient-save-as-css"         : "gradient-save-as-css"                   ,
}

def plugin_func(testedName):
    print(f"python-fu-map-pdb-name: {testedName}")

    try:
        result = map[testedName]
    except KeyError:
        result = testedName
    return result

def plugin_func2(image, drawable, testedName):

    # A name not deprecated
    print ( f"Mapped name: {pdb.python_fu_map_pdb_name('foo')[0]}")
    # Note always returns a list, but why does it have a trailing empty string?
    # Expect print "foo"

    # A deprecated name
    print ( f"Mapped name: {pdb.python_fu_map_pdb_name('gimp-image-is-valid')[0]}")
    # Expect print "barbar"





""" A utility procedure, no menu """
register(
      "python-fu-map-pdb-name",
      "Map a deprecated PDB procedure name to the new name",
      "Used internally by ScriptFu for backward compatibility.",
      "author",
      "copyright",
      "year",
      "",   # No menu item
      "",   # No image types
      [ (PF_STRING, "testedName", "Possibly deprecated name to map", ""), ],
      [ (PF_STRING, "mappedName", "Mapped name (deprecated name or unchanged name", ""), ],
      plugin_func,
      menu="")  # Not appear in menus

""" A procedure to test the utility procedure """
register(
      "python-fu-test-map-pdb-name",
      "Map a deprecated PDB procedure name to the new name",
      "Used internally by ScriptFu for backward compatibility.",
      "author",
      "copyright",
      "year",
      "Test map PDB name",
      "",   # No image types
      # GimpFu will fix up missing image, drawable
      [ (PF_STRING, "testedName", "Possibly deprecated name to map", ""), ],
      [],   # void result
      plugin_func2,
      menu="<Image>/Test")
main()
