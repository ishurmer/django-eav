from django.core.exceptions import ImproperlyConfigured

from rest_framework import serializers
from rest_framework.fields import *

from measurement.fields import D
from eav import registry
from eav.models import EnumValue

class EAVModelSerializer(serializers.ModelSerializer):
    INCLUDE_EAV_DATA = True
    EAV_SEPARATE_DICT = False

    def full_clean(self, instance):
        super(EAVModelSerializer, self).full_clean(instance)

        eav = EAVModelSerializer._get_eav_object(instance)
        errors = {}
        if eav:
            try:
                eav.validate_attributes( )
            except ValidationError as e:
                sl = e.params.get('attr', None)
                if not sl:
                    errors['__all__'] = e.error_list
                else:
                    errors[sl.slug] = e.error_list

            if errors:
                self._errors = ValidationError(errors).message_dict
                return None

        return instance

    def restore_fields(self, data, files):
        self._eav_data = {}
        rev_data = super(EAVModelSerializer, self).restore_fields(data, files)
        eav =  EAVModelSerializer._get_eav_object(self.object)
        if eav:
            for k in eav.get_all_attribute_slugs( ):
                if data.get(k):
                    self._eav_data[k] = data[k]
                    del data[k]

        return rev_data

    def eav_values_dict_to_native(self, dct):
        add_fields = {}
        for k, v in list(dct.items( )):
            if isinstance(v, EnumValue):
                add_fields[k] = v.value
            elif isinstance(v, D):
                add_fields[k] = str(v)
                add_fields["%s_metres" % k] = v.m
        dct.update(add_fields)
        return dct

    @staticmethod
    def _get_eav_object(obj):
        c = None
        eav = None
        try:
            c = obj._eav_config_cls
        except AttributeError as aex:
            raise ImproperlyConfigured("%s %s is using " % (
                obj.__class__.__name__, obj
            )+" EAVModelSerializer but no _eav_config_cls attribute exists")

        try:
            eav = getattr(obj, c.eav_attr)
        except AttributeError as aex:
            raise ImproperlyConfigured("Invalid eav_attr %s.%s => %s." % (
                obj.__class__.__name__, obj, c.eav_attr))

        return eav

    def to_native(self, obj):
        dat = super(EAVModelSerializer, self).to_native(obj)
        if self.INCLUDE_EAV_DATA and obj:
            eav = EAVModelSerializer._get_eav_object(obj)
            vals = eav.get_values_dict( )
            dct = self.eav_values_dict_to_native(vals)
            if self.EAV_SEPARATE_DICT:
                dat['eav'] = dct
            else:
                dat.update(dct)

        return dat

    def restore_object(self, attrs, instance=None):
        obj = super(EAVModelSerializer, self).restore_object(attrs, instance)
        if self.INCLUDE_EAV_DATA:
            eav_data = getattr(self, '_eav_data', {})
            if eav_data:
                eav = EAVModelSerializer._get_eav_object(obj)
                for k, v in list(eav_data.items( )):
                    setattr(eav, k, v)
        return obj