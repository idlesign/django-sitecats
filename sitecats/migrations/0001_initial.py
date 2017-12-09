# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import sitecats.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(help_text='Category name.', max_length=250, verbose_name='Title')),
                ('alias', sitecats.models.CharFieldNullable(null=True, max_length=80, blank=True, help_text='Short name to address category from application code.', unique=True, verbose_name='Alias')),
                ('is_locked', models.BooleanField(default=False, help_text='Categories addressed from application code are locked, their aliases can not be changed. Such categories can be deleted from application code only.', verbose_name='Locked')),
                ('note', models.TextField(verbose_name='Note', blank=True)),
                ('status', models.IntegerField(db_index=True, null=True, verbose_name='Status', blank=True)),
                ('slug', sitecats.models.CharFieldNullable(max_length=250, unique=True, null=True, verbose_name='Slug', blank=True)),
                ('time_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('time_modified', models.DateTimeField(auto_now=True, verbose_name='Date modified')),
                ('sort_order', models.PositiveIntegerField(default=0, help_text='Item position among other categories under the same parent.', verbose_name='Sort order', db_index=True)),
                ('creator', models.ForeignKey(related_name='category_creators', verbose_name='Creator', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('parent', models.ForeignKey(related_name='category_parents', blank=True, to='sitecats.Category', help_text='Parent category.', null=True, verbose_name='Parent', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tie',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(verbose_name='Note', blank=True)),
                ('status', models.IntegerField(db_index=True, null=True, verbose_name='Status', blank=True)),
                ('time_created', models.DateTimeField(auto_now_add=True, verbose_name='Date created')),
                ('object_id', models.PositiveIntegerField(verbose_name='Object ID', db_index=True)),
                ('category', models.ForeignKey(related_name='tie_categories', verbose_name='Category', to='sitecats.Category', on_delete=models.CASCADE)),
                ('content_type', models.ForeignKey(related_name='sitecats_tie_tags', verbose_name='Content type', to='contenttypes.ContentType', on_delete=models.CASCADE)),
                ('creator', models.ForeignKey(related_name='tie_creators', verbose_name='Creator', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'Tie',
                'verbose_name_plural': 'Ties',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together=set([('title', 'parent')]),
        ),
    ]
