
#is_test = True
is_test = False


# !!! Can't import Marshal yet, circular
# See below, import Marshal selectively

from gimpfu.adaption.wrappable import *
from gimpfu.adaption.adapted_property import AdaptedProperty

from gimpfu.adapters.adapter_logger import AdapterLogger


'''
Adapter component of the Wrapper/Adapter pattern.
Wraps an Adaptee that is a Gimp object (usually some subclasses of Item e.g. Layer)
An Adapted object inherits this class.
(Adapted and Adaptee are metaclasses, no instance is-a Adapted or Adaptee.)

Collaborators:
    Marshal:  args to and from Adaptee must be marshalled (wrapped and unwrapped)
    AdaptedProperty: accesses to properties of Adaptee, defined by AdaptedAdaptee

Responsibilities:
    delegate a subset of attributes accesses on Adapted to Adaptee
        - property accesses on Adapted => Adaptee getter/setter functions
        - calls to undefined methods of Adapted => calls to Adaptee

    equality of Adapted instances
    copy Adapted instances

    expose the Adaptee instance  and its class_name to Adapted
    catch errors in attribute access

Note that an Adapted class can adapt methods that become calls on Adaptee.
Methods that the Adapted class adapts (specializes.)
The calls that the Adaptor class adapts are generally adapted.

see comments at adapters.image, somewhat similar re dynamic methods

Using the "object adapter" version of the pattern.
Whereby Adapter owns an instance of Adaptee (composition.)
class adapter vs object adapter
   Object adapter: does not inherit Gimp.Image, but owns an instance of it
   Class adapter: multiple inheritance, e.g. GimpfuLayer inherits Gimp.Layer
      I don't know how to wrap Gimp.Layer using metaprogramming dynamically?

TODO enumerate errors it detects

'''

class Adapter():

    def __init__(self, adaptee):
        # TODO can we log the subclass name here?
        AdapterLogger.logger.info(f"New instance of subclass of Adapter for {adaptee}")

        if is_gimpfu_wrappable(adaptee):
            self._adaptee = adaptee
            self._adaptee_callable = None
        else:
            raise Exception(f"Not wrappable: {adaptee}")


    def __repr__(self):
        return f"<{self.__class__} of {self.adaptee_class_name}>"




    """
    Adapter is a GimpFu class without a corresponding Gimp class.
    Therefore it defines no dynamic adapted properties or mapped methods itself,
    but defines the base implementation, which return an *empty* thing,
    a tuple of adapted properties or dictionary of mapped methods.
    Each subclass *may* have its own tuple of dynamic adapted properties,
    and MUST concatenate those with super's tuple.

    Similarly for dynamic mapped methods
    ??? TODO, see GimpfuImage, it seems that dynamic mapped methods is partially implemented.
    Maybe it is cruft?
    """
    @classmethod
    def DynamicWriteableAdaptedProperties(cls): return tuple()

    @classmethod
    def DynamicReadOnlyAdaptedProperties(cls):  return tuple()

    @classmethod
    def DynamicTrueAdaptedProperties(cls):      return tuple()

    @classmethod
    def DynamicMappedMethods(cls):              return dict()




    '''
    Expose adaptee and its class_name.
    '''
    def unwrap(self):
        ''' Return inner object, of a Gimp type, used when passing args back to Gimp'''
        AdapterLogger.logger.debug(f"unwrap, from: {self._adaptee}, to gtype: {self.adaptee_gtype}")
        return self._adaptee

    @property
    def adaptee_class_name(self):
        ''' Class name by which author knows adaptee class e.g. Gimp.Image '''
        return type(self._adaptee).__name__

    @property
    def adaptee_gtype(self):
        ''' gtype of adaptee e.g. Gimp.Layer.__gtype__ '''
        return self._adaptee.__gtype__



    '''
    Equality and copy
    '''
    def __eq__(self, other):
         '''
         Override equality operator.

         This emanates from an "==" in Authors code.
         GimpFu code usually does not compare adapted instances.

         Two Adapted instances are equal if:
         - both have same superclass of Adapter
         - AND their adaptee's are equal.

         Require self and other both inherit Adapter, ow exception.
         I.E. not general purpose equality such as: Layer instance == int instance
         '''

         # We know self is an Adaptor, check other
         try:
            unwrapped_other = other.unwrap()
         except AttributeError:
            message = f"Fail __eq__, failed to unwrap other: {other}"
            AdapterLogger.logger.info(message)
            raise Exception(message)

         try:
             # Compare ID's or names instead?
             # Could use public unwrap() for more generality
             AdapterLogger.logger.info(f"Adaptor.__eq__ between unwrapped: {self} and {unwrapped_other}")
             return self._adaptee == unwrapped_other
         except:
             # TODO define GimpFuException class of exceptions and do logging there
             message = f"Fail __eq__ between: {self}, {other}"
             AdapterLogger.logger.critical(message)
             raise Exception(message)



    '''
    copy() method on AdaptedAdaptee instance.
    Source code like: fooAdapted.copy().
    Copy() is deep, to copy the instance and its owned adaptee.

    This is NOT __copy__
     __copy__ is invoked by copy module i.e. copy.copy(foo)
    To allow authors to use the copy module,
    we should override __copy__ and __deepcopy__ also.
    Such MUST call gimp to copy the adaptee.
    TODO

    See SO "How to override the copy/deepcopy operations for a Python object?"
    This is a hack of that answer code.
    Gimp adaption:
    copy() was implemented in v2, but I am not sure it went through the __copy__ mechanism.

    TODO just Marshal.wrap() ??? Would work if self has no attributes not computed from adaptee
    '''

    def copy(self):
         """ Copy an Adapted instance. """

         # require Adaptee implements copy()

         # Marshal knows how to wrap self in AdaptedAdaptee, e.g. GimpfuLayer
         if is_test:
             from gimpfu.mock.marshal import Marshal
         else:
             from gimpfu.adaption.marshal import Marshal

         '''
         clone _adaptee
         v2 called run_procedure()
         Here we use Adaptee.copy() directly
         Exception if Adaptee does not implement copy()
         '''
         adaptee_clone = self._adaptee.copy()

         # Create Adapted instance
         result =  Marshal.wrap(adaptee_clone)

         AdapterLogger.logger.debug(f"Made wrapped copy: {result} of copied adaptee {adaptee_clone}")
         return result





    '''
    Private
    '''

    def _adapter_func(self, *args):
        ''' intercepts calls to previously accessed attribute '''

        # This must be improved: for an arg is-a list, raises "unhashable type"
        # Note that you can't unpack inside a fstring
        # AdapterLogger.logger.debug(f"_adapter_func called, args: { {*args} }")

        from gimpfu.adaption.marshal import Marshal

        # arg could be a wrapped type, convert to unwrapped type i.e. foreign type
        unwrapped_args = Marshal.unwrap_heterogenous_sequence(args)

        # call the callable
        # TODO Not sure why we need to use object.__...
        unwrapped_result = object.__getattribute__(self, "_adaptee_callable")(*unwrapped_args)

        # result could be a foreign type, convert to wrapped type, etc.
        result = Marshal.wrap_adaptee_results(unwrapped_result)

        # assert result is-a list of wrapped
        return result





    '''
    __getattr and __setattr that adapt attributes: delegate to adaptee
    '''

    '''
    !!! See the Python docs for __getattr__.
    Especially note that this is called when a property getter for an inheriting class
    fails and raises a first AttributeError.
    That first AttributeError is masked by the AttributeError raised below.
    So for this AttributeException, check:
    1) in Gimpfu code, a property <name> in the inheriting class accesses valid attributes
    2) OR in the Gimp API <name> is an attribute of the class <adaptee_class_name>
    '''

    def __getattr__(self, name):
        AdapterLogger.logger.debug(f"__getattr__ called for: {name}")

        '''
        Instance is AdaptedAdaptee (it inherits Adapter).
        Require class of instance implements virtual properties of ABC AdaptedAdaptee:
        i.e. defines class attributes Dynamic... that list properties
        '''

        ''
        """
        msg = f"Missing DynamicReadOnly... in Adapter for {self.adaptee_class_name} "
        AdapterLogger.logger.debug(type(self).__name__)
        AdapterLogger.logger.debug(dir(self))
        assert object.__getattribute__(self, 'DynamicReadOnlyAdaptedProperties'), msg
        msg = f"Missing DynamicWriteable... in Adapter for {self.adaptee_class_name} "
        assert object.__getattribute__(self, 'DynamicWriteableAdaptedProperties'), msg
        """

        # avoid infinite recursion
        adaptee = self.__dict__['_adaptee']

        '''
        Order is important:
        Only use a name as a callable after
        we determine that we are not adapting it as a true property.
        '''
        if AdaptedProperty.is_dynamic_true_property_name(self, name):
            result = AdaptedProperty.read(adaptee, name)
        elif AdaptedProperty.is_callable_name_on_instance(adaptee, name):
            adaptee_callable = getattr(self.__dict__['_adaptee'], name)
            # Prepare for subsequent call
            # avoid infinite recursion
            object.__setattr__(self, "_adaptee_callable", adaptee_callable)
            result = self._adapter_func
        elif self.is_mapped_callable_name_on_instance(adaptee, name):
            mapped_name = self.is_mapped_callable_name_on_instance(adaptee, name)
            # assert mapped_name is_attr(_adaptee)
            adaptee_callable = getattr(self.__dict__['_adaptee'], mapped_name)
            # get callable for mapped_name
            object.__setattr__(self, "_adaptee_callable", adaptee_callable)
            result = self._adapter_func
        elif AdaptedProperty.is_dynamic_readable_property_name(self, name):
            result = AdaptedProperty.get(adaptee, name)
        else:
            '''
            This error is hard to decipher.
            Not only name that is not an attribute,
            but possibly a programming error or runtime error
            in an implemented property of an AdaptedAdaptee class.
            '''
            msg = ( f"Name: {name} is not an attr of: {self.adaptee_class_name}"
                    f" OR error in property: {name} of: {type(self).__name__} ")
            raise AttributeError(msg)
        # assert result is a value, or the callable adapter_func
        return result



    def __setattr__(self, name, value):
        '''
        Attempt by Author to assign to name.
        I.E. source phrase like "name = bar"
        '''

        '''
        Special case: implementation of Adapter assigns to the few attributes of itself.
        '''
        if name in ('_adaptee', '_adaptee_callable'):
            object.__setattr__(self, name, value)
            return

        '''
        All other cases should be authors attempts to assign
        to attributes of an instance of Adapted(Adapter).
        '''

        # avoid calling __getattr__
        adaptee = self.__dict__['_adaptee']

        '''
        DynamicTrueAdaptedProperties are not settable
        since adaptee only defines a getter i.e. <name>().
        If adaptee defines <name>() and set_<name>()
        Gimpfu must adapt specially, outside of this mechanism.
        '''
        if AdaptedProperty.is_callable_name_on_instance(adaptee, name):
            # Adaptee's are Gimp objects, which have no assignable attributes, only callables ????
            raise AttributeError(f"Name {name} on {self.adaptee_class_name} is not assignable, only callable.")
        elif AdaptedProperty.is_dynamic_writeable_property_name(self, name):
            result = AdaptedProperty.set(adaptee, name, value)
        elif AdaptedProperty.is_dynamic_readonly_property_name(self, name):
            raise AttributeError(f"Attempt to assign to readonly attribute '{name}'")
        else:
            '''
            author is attempting to assign a new attribute
            to a class of the adaption mechanism (e.g. an instance that inherits Adaptor.)
            See above for the only internal attributes of Adaptor.
            This must be an error in author's code.
            They have instances of Gimpfu's subclasses of Adapter,
            but we disallow assigning attributes to them, they could do harm.
            Instead they should use local variables.
            '''
            raise AttributeError(f"Attempt to assign to attribute: {name} of Gimpfu Adaptor of: {self.adaptee_class_name})")
            """
            AdapterLogger.logger.debug("Assigned to Adapted(Adapter) class")
            AdapterLogger.logger.debug("Adapter.__setattr__", name)
            object.__setattr__(self, name, value)
            """

        # assert result is a value, or the callable adapter_func
        return result


    def is_mapped_callable_name_on_instance(self, instance, name):
        ''' Is map(<name>) an attribute on instance that is a callable?
        A callable foo is used like "foo()" i.e. in a construct ending in parens.

        Returns the mapped name, or None.
        '''
        name_map = self.DynamicMappedMethods()
        if name in name_map:
            result = name_map[name]
            # TODO we could check that result is an attribute of instance
            # but we rely on the map being accurate
        else:
            result = None
        return result
