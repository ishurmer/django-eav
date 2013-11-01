#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 coding=utf-8
#
#    This software is derived from EAV-Django originally written and 
#    copyrighted by Andrey Mikhaylenko <http://pypi.python.org/pypi/eav-django>
#
#    This is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This software is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with EAV-Django.  If not, see <http://gnu.org/licenses/>.


from django.contrib import admin
from django.contrib.admin.options import (
    ModelAdmin, InlineModelAdmin, StackedInline, IS_POPUP_VAR
)

from django import forms
from django.forms.utils import ErrorList
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from .models import Attribute, Value, EnumValue, EnumGroup

import copy

class BaseEntityAdmin(ModelAdmin):
    def render_change_form(self, request, context, add=False, change=False,
        form_url='', obj=None):
        """
        Wrapper for ModelAdmin.render_change_form. Replaces standard static
        AdminForm with an EAV-friendly one. The point is that our form generates
        fields dynamically and fieldsets must be inferred from a prepared and
        validated form instance, not just the form class. Django does not seem
        to provide hooks for this purpose, so we simply wrap the view and
        substitute some data.
        """
        form = context['adminform'].form

        # infer correct data from the form
        fieldsets = self.fieldsets or [(None, {'fields': form.fields.keys()})]
        adminform = admin.helpers.AdminForm(form, fieldsets,
                                      self.prepopulated_fields)
        media = mark_safe(self.media + adminform.media)

        context.update(adminform=adminform, media=media)

        super_meth = super(BaseEntityAdmin, self).render_change_form
        return super_meth(request, context, add, change, form_url, obj)



class BaseEntityFieldsetAdmin(ModelAdmin):
    eav_fieldset_classes = []
    attribute_accessor_name = 'get_eav_attributes'
    standard_response_add_workflow = False


    def get_fieldset_attrs(self, attrs, request, obj=None, add=False,
                           change=False):
        return [(
            _('Fields'), {'fields': [ac.slug for ac in attrs],
                          'classes': []}
        )]

    def response_add(self, request, obj, post_url_continue=None):
        if self.standard_response_add_workflow:
            return super(BaseEntityFieldsetAdmin, self).response_add(request, 
                obj, post_url_continue)
        # Follow the workflow of Django Auth User admin, in that we want to
        # use "save and continue" functionality if "save and add another" is not
        # clicked, and we're not using a popup.
        if '_addanother' not in request.POST and (
            IS_POPUP_VAR not in request.POST):
            request.POST['_continue'] = 1
        return super(BaseEntityFieldsetAdmin, self).response_add(request, obj,
                                                           post_url_continue)
    def render_change_form(self, request, context, add=False, change=False,
        form_url='', obj=None):
        # Automatically add the relevant EAV fields to fieldsets, based on
        # their asset class. We have to do this here and not get_fieldsets,
        # as the EAV fields are not actually added to the form until it is
        # instantiated, which is too late for the get_form dynamic form method.
        form = context['adminform'].form
        fs = list(self.fieldsets or [(None, {'fields':
                                             list(form.fields.keys())})])
        if obj:
            remove_from = []
            all_acs = getattr(obj, self.attribute_accessor_name)( )
            fsets = self.get_fieldset_attrs(all_acs, request, obj, add, change)

            for fst in fsets:
                remove_from.extend(fst[1]['fields'])
                fst[1]['classes'] = list(fst[1]['classes'] or [])+copy.copy(
                    getattr(self, 'eav_fieldset_classes', []))
                fst[1]['classes'].append('fromAssetClass')
                fs.append(fst)

            for slug, dat in fs:
                if 'fromAssetClass' in dat.get('classes', []):
                    continue
                dat['fields']=[f for f in dat['fields'] if f not in remove_from]

        adminform = admin.helpers.AdminForm(form, fs, self.prepopulated_fields)
        media = mark_safe(self.media + adminform.media)
        context.update(adminform=adminform, media=media)
        super_meth = super(BaseEntityFieldsetAdmin, self).render_change_form
        return super_meth(request, context, add, change, form_url, obj)

class BaseEntityInlineFormSet(BaseInlineFormSet):
    """
    An inline formset that correctly initializes EAV forms.
    """
    def add_fields(self, form, index):
        if self.instance:
            setattr(form.instance, self.fk.name, self.instance)
            form._build_dynamic_fields()
        super(BaseEntityInlineFormSet, self).add_fields(form, index)


class BaseEntityInline(InlineModelAdmin):
    """
    Inline model admin that works correctly with EAV attributes. You should mix
    in the standard StackedInline or TabularInline classes in order to define
    formset representation, e.g.::

        class ItemInline(BaseEntityInline, StackedInline):
            model = Item
            form = forms.ItemForm

    .. warning: TabularInline does *not* work out of the box. There is,
        however, a patched template `admin/edit_inline/tabular.html` bundled
        with EAV-Django. You can copy or symlink the `admin` directory to your
        templates search path (see Django documentation).

    """
    formset = BaseEntityInlineFormSet

    def get_fieldsets(self, request, obj=None):
        if self.declared_fieldsets:
            return self.declared_fieldsets

        formset = self.get_formset(request)
        fk_name = self.fk_name or formset.fk.name
        kw = {fk_name: obj} if obj else {}
        instance = self.model(**kw)
        form = formset.form(request.POST, instance=instance)

        return [(None, {'fields': form.fields.keys()})]

class AttributeAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AttributeAdminForm, self).__init__(*args, **kwargs)
        self.fields['_default_value'].widget = forms.TextInput( )

    def clean(self):
        self.cleaned_data = super(AttributeAdminForm, self).clean()
        v = self.cleaned_data['_default_value']
        if v:
            try:
                self.instance.datatype = self.cleaned_data['datatype']
                self.instance.default_value = v
            except ValidationError, vex:
                self._errors['_default_value'] = ErrorList([vex.message])
        if v == '': 
            self.cleaned_data['_default_value'] = None
        return self.cleaned_data

class AttributeAdmin(ModelAdmin):
    form = AttributeAdminForm
    list_display = ('name', 'slug', 'datatype', 'description', '_default_value',
                    'site', 'type')
    list_filter = ['site']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (_('Main Fields'), {
            'fields': ('name', 'order', 'site', 'slug', 'required',
                       'description')
        }),
        (_('Type Field'), {
            'fields': ('datatype', 'type')
        }),
        (_('Choice Field'), {
            'fields': ('enum_group', )
        }),
        (_('Default Value'), {
            'fields': ('_default_value', )
        })
    )

admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Value)
admin.site.register(EnumValue)
admin.site.register(EnumGroup)

