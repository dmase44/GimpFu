

import logging


class AdaptedProperty():
    '''
    Understands how to dynamically adapt properties.

    Properties on Adaptee must be called using call syntax (with parens)
    e.g. "foo = adaptee.get_property()" or "property()"
    In the statement dynamically generated by this class.

    Properties on AdaptedAdaptee use non-call syntax (without parens)
    e.g. "foo = adaptedAdaptee.property"
    In the Author's plugin source code.

    An access to an AdaptedProperty is intercepted by the Python __getattr__
    mechanism.

    AdaptedProperty's are defined in AdaptedAdaptee's
    by a property name like "Dynamic..."
    that is a tuple of names of Adaptee properties (sic) that can be
    dynamically adapted.

    Some Adaptee properties cannot be dynamically adapted,
    (because the syntax or semantic differences are too great to be automated.)
    and are instead 'manually' adapted by code in AdaptedAdaptee
    implemented as Python properties i.e. using "@property"
    '''

    '''
    Kinds of adapted properties:
      ReadOnly: get_<property>() defined by adaptee
      Writeable: set_ and get_<property>() defined by adaptee
      True:   <property>() defined by adaptee

    !!! An AdaptedProperty is NOT an access to a *field* of the adaptee, but a *method* of the adaptee.
    An AdaptedAdaptee may define properties that give r/w access to fields of property.
    But it is so rare (see GimpfuRGB) we don't do it programatically.
    '''

    '''
    Inheritance and AdaptedProperty(s)

    An Adaptee instance inherits from a chain of classes.
    When we ask whether a name is on an instance of adaptee,
    GI must search the chain.

    An AdaptedAdaptee (which defines dynamic properties)
    also inherits from a chain of classes.
    E.g. GimpfuLayer=>GimpfuDrawable=>GimpfuItem.
    Each class may define its own Dynamic... properties,
    but when asked, must return the totaled properties of
    its own class plus its inherited classes.

    (Alternatively we could traverse the MRO)
    '''

    logger = logging.getLogger("GimpFu.AdaptedProperty")

    @classmethod
    def is_dynamic_writeable_property_name(cls, instance, name):
        ''' is name a writeable dynamic property on instance? '''
        ''' !!! instance is-a AdaptedAdaptee, not an Adaptee '''

        # raises AttributeError if DynamicWriteableAdaptedProperties not defined by AdaptedAdaptee
        #OLD delegated_property_names = getattr(instance, 'DynamicWriteableAdaptedProperties')
        delegated_property_names = instance.DynamicWriteableAdaptedProperties()
        # ensure delegated_property_names is not None, but could be empty
        return name in delegated_property_names


    @classmethod
    def is_dynamic_readonly_property_name(cls, instance, name):
        # raises AttributeError if DynamicWriteableAdaptedProperties not defined by AdaptedAdaptee
        #OLD delegated_property_names = getattr(instance, 'DynamicReadOnlyAdaptedProperties')
        delegated_property_names = instance.DynamicReadOnlyAdaptedProperties()
        # ensure delegated_property_names is not None, but could be empty
        return name in delegated_property_names



    @classmethod
    def is_dynamic_true_property_name(cls, instance, name):
        ''' Is <name> accessed like <name>() ? '''
        delegated_property_names = instance.DynamicTrueAdaptedProperties()
        result = name in delegated_property_names
        AdaptedProperty.logger.debug(f"is_dynamic_true_property_name: {result} for name: {name} on instance: {instance}")
        return result



    @classmethod
    def is_dynamic_readable_property_name(cls, instance, name):
        ''' Is <name> accessed like get_<name>() ? '''
        return (cls.is_dynamic_readonly_property_name(instance, name)
            or cls.is_dynamic_writeable_property_name(instance, name)
            )

    '''
    !!! This does not mean that the callable has arguments.
    When the callable does not have args i.e. <name>(void)
    it is indistinguishable from what we might adapt as a property.

    !!! This is too weak.
    We should retrieve the attr and check that it is a gi.FunctionInfo,
    else the attribute is not a callable.
    Gimp and GI does have properties that are not callables?
    '''
    @classmethod
    def is_callable_name_on_instance(cls, instance, name):
        ''' Is <name> an attribute on instance, accessed like <name>() ? '''
        return hasattr(instance, name)





    # Private
    @classmethod
    def _eval_statement_on_adaptee(cls, adaptee, name, prefix = '', setting_value=None):
        '''
        Create and eval() a statement to access a method on adaptee
        that looks like a property i.e. has no args.
        '''

        assert prefix in ("get_", "set_", "")

        # FUTURE rather than trust that DynamicReadOnlyAdaptedProperties is correct,
        # preflight get_name on dictionary of adaptee
        # So we can use a more specific error than AttributeError, e.g. "is not a *property* name"


        # Method on adaptee is like "[get,set]_name"
        # Method on adaptee is a callable having no arguments
        # eval occurs in current context, so formal args are in scope
        if prefix == 'set_':
            # setStatement is a call with arg
            statement = 'adaptee.set_' + name + '(setting_value)'
        else:
            # is a get (prefix is 'get_') or a read (prefix is '')
            # getStatement is a call without arg
            statement = 'adaptee.' + prefix + name + '()'
        result = eval(statement)
        AdaptedProperty.logger.debug(f"eval {statement} result: {result}")
        return result


    @classmethod
    def get(cls, adaptee, method_name ):
        ''' Call method_name of adaptee to get a property value. '''
        unwrapped_result = cls._eval_statement_on_adaptee(adaptee, method_name, prefix = 'get_')
        # !!! result can be a container of wrappable types.  Usually a fundamental type.
        from gimpfu.adaption.marshal import Marshal
        result = Marshal.wrap_adaptee_results(unwrapped_result)
        return result

    @classmethod
    def set(cls, adaptee, method_name, value):
        ''' Call method_name of adaptee to set a property value. '''
        from gimpfu.adaption.marshal import Marshal
        unwrapped_value = Marshal.unwrap(value)
        return cls._eval_statement_on_adaptee(adaptee, method_name, prefix = 'set_', setting_value = unwrapped_value)

    @classmethod
    def read(cls, adaptee, method_name ):
        ''' Call method_name of adaptee to get a property value. '''
        # TODO marshal
        return cls._eval_statement_on_adaptee(adaptee, method_name, prefix = '')
