

'''
Knows:

    which Gimp types are wrappable by Gimpfu and vice versa.
    which Gimp attributes are functions
    which Gimp types are subclasses of Drawable
'''


# Python idiom for string name of a type
# Gimp.Drawable returns a type, but its name is type.__name__
def get_type_name(instance):
    return get_name_of_type(type(instance))

def get_name_of_type(a_type):
    return a_type.__name__

'''
Keep these in correspondence with each other,
and with wrap() dispatch.
(unwrap is in the adapter)
I.E. to add a wrapper Foo:
 - add Foo.py in adapters/
 - add literals like 'Foo' in three places in this file.

wrap is symmetrical with unwrap.
We wrap Drawable, Item, etc. but the Author cannot create instances,
only instance of subclasses.
'''
def is_gimpfu_wrappable_name(name):
    return name in ('Image', 'Layer', 'Display', 'Vectors')

def is_gimpfu_unwrappable( instance):
    return get_type_name(instance) in ("GimpfuImage", "GimpfuLayer", "GimpfuDisplay", "GimpfuVectors")



# TODO rename is_instance_gimpfu_wrappable
def is_gimpfu_wrappable(instance):
    return is_gimpfu_wrappable_name(get_type_name(instance))




# TODO rename is_function
def is_wrapped_function(instance):
    ''' Is the instance a gi.FunctionInfo? '''
    '''
    Which means an error earlier in the author's source:
    accessing an attribute of adaptee as a property instead of a callable.
    Such an error is sometimes caught earlier by Python
    when author dereferenced the attribute
    (e.g. when used as an int, but not when used as a bool)
    but when first dereference is when passing to PDB, we catch it.
    '''
    return type(instance).__name__ in ('gi.FunctionInfo')


'''
Taken from "GIMP App Ref Manual>Class Hierarchy"
Note the names are not prefixed with "Gimp."

Technically, NoneType is a subclass of every type.
But we don't want that here, we deal with it elsewhere.
'''
DrawableTypeNames = (
    "Layer",
       "GroupLayer",
       "TextLayer"
    "Channel",
       "LayerMask",
       "Selection",
)

# Authors cannot instantiate Drawable so it does not need to be here
# Authors cannot instantiate Item.
# Drawable and Item are virtual base classes.
ItemTypeNames = (
    "Drawable",
    "Vectors"
)

def is_subclass_of_type(instance, super_type):
    # assert super_type is a Python type, having .__name__
    super_type_name = get_name_of_type(super_type)
    if  super_type_name == 'Drawable':
        result =  get_type_name(instance) in DrawableTypeNames
    elif super_type_name == 'Item':
        type_name = get_type_name(instance)
        result = type_name in ItemTypeNames or type_name in DrawableTypeNames
    print(f"is_subclass_of_type {super_type_name} returns {result}")
    return result
