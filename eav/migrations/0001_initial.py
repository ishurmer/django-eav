# encoding: utf8
from django.db import models, migrations
import measurement.fields
import datetime
import eav.fields


class Migration(migrations.Migration):
    
    #TODO: Uncomment these when Django 1.7 comes with the required migrations.
    #dependencies = [('contenttypes', '0001_initial'), ('sites', '0001_initial')]
    dependencies = []

    operations = [
        migrations.CreateModel(
            name = 'EnumValue',
            bases = (models.Model,),
            fields = [('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True),), ('value', models.CharField(db_index=True, unique=True, max_length=50, verbose_name='value'),)],
            options = {},
        ),
        migrations.CreateModel(
            name = 'EnumGroup',
            bases = (models.Model,),
            fields = [('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True),), ('name', models.CharField(unique=True, verbose_name='name', max_length=100),)],
            options = {},
        ),
        migrations.CreateModel(
            name = 'Attribute',
            bases = (models.Model,),
            fields = [('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True),), ('order', models.PositiveIntegerField(db_index=True, default=0),), ('name', models.CharField(verbose_name='name', max_length=100, help_text='User-friendly attribute name'),), ('site', models.ForeignKey(to_field='id', to='sites.Site', verbose_name='site', default=1),), ('slug', eav.fields.EavSlugField(verbose_name='slug', help_text='Short unique attribute label'),), ('description', models.CharField(null=True, blank=True, verbose_name='description', max_length=256, help_text='Short description'),), ('enum_group', models.ForeignKey(to='eav.EnumGroup', verbose_name='choice group', null=True, to_field='id', blank=True),), ('type', models.CharField(null=True, blank=True, verbose_name='type', max_length=20),), ('_default_value', models.TextField(null=True, blank=True, verbose_name='default value'),), ('datatype', eav.fields.EavDatatypeField(choices=(('text', 'Text',), ('float', 'Float',), ('int', 'Integer',), ('date', 'Date',), ('bool', 'True / False',), ('object', 'Django Object',), ('enum', 'Multiple Choice',), ('dist', 'Distance Field',),), verbose_name='data type', max_length=6),), ('created', models.DateTimeField(default=datetime.datetime.now, editable=False, verbose_name='created'),), ('modified', models.DateTimeField(auto_now=True, verbose_name='modified'),), ('required', models.BooleanField(verbose_name='required', default=False),)],
            options = {'ordering': ['order', 'name'], 'unique_together': set(['site', 'slug'])},
        ),
        migrations.CreateModel(
            name = 'Value',
            bases = (models.Model,),
            fields = [('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True),), ('entity_ct', models.ForeignKey(to_field='id', to='contenttypes.ContentType'),), ('entity_id', models.IntegerField(),), ('value_text', models.TextField(null=True, blank=True),), ('value_float', models.FloatField(null=True, blank=True),), ('value_int', models.IntegerField(null=True, blank=True),), ('value_date', models.DateTimeField(null=True, blank=True),), ('value_bool', models.NullBooleanField(),), ('value_enum', models.ForeignKey(to='eav.EnumValue', to_field='id', blank=True, null=True),), ('value_dist', measurement.fields.DistanceField(null=True, blank=True),), ('distance_unit', models.CharField(null=True, blank=True, max_length=8),), ('generic_value_id', models.IntegerField(null=True, blank=True),), ('generic_value_ct', models.ForeignKey(to='contenttypes.ContentType', to_field='id', blank=True, null=True),), ('created', models.DateTimeField(verbose_name='created', default=datetime.datetime.now),), ('modified', models.DateTimeField(auto_now=True, verbose_name='modified'),), ('attribute', models.ForeignKey(to_field='id', to='eav.Attribute', verbose_name='attribute'),)],
            options = {},
        ),
    ]
