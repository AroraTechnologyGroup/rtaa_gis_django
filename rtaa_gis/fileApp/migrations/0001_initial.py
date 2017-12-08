# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-08 01:46
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DisciplineModel',
            fields=[
                ('name', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='DocumentTypeModel',
            fields=[
                ('name', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='EngineeringAssignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('base_name', models.CharField(blank=True, max_length=50)),
                ('date_assigned', models.DateField(auto_now_add=True, null=True)),
                ('comment', models.CharField(blank=True, max_length=255)),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EngineeringFileModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_path', models.CharField(max_length=255, unique=True)),
                ('base_name', models.CharField(max_length=255)),
                ('file_type', models.CharField(choices=[('pdf', 'PDF'), ('odt', 'Open Office doc'), ('doc', 'MS Word doc'), ('docx', 'MS Word docx'), ('odp', 'Open Office Presentation'), ('txt', 'Text'), ('ods', 'Open Office Sheet'), ('xls', 'MS Excel xls'), ('xlsx', 'MS Excel xlsx'), ('csv', 'CSV Spreadsheet'), ('png', 'PNG Image'), ('jpg', 'JPEG Image'), ('img', 'IMG Image'), ('tiff', 'TIFF Image'), ('dwg', 'AutoCad dwg'), ('lyr', 'ESRI Layer File'), ('mpk', 'ESRI Map Package'), ('mxd', 'ESRI Map Document')], max_length=25)),
                ('mime', models.CharField(max_length=255)),
                ('size', models.CharField(max_length=25)),
                ('date_added', models.DateField(auto_now_add=True)),
                ('last_edited_date', models.DateField(auto_now=True)),
                ('comment', models.CharField(blank=True, max_length=255)),
                ('project_title', models.CharField(blank=True, max_length=255, null=True)),
                ('project_description', models.CharField(blank=True, max_length=255, null=True)),
                ('project_date', models.DateField(null=True)),
                ('sheet_title', models.CharField(blank=True, max_length=255, null=True)),
                ('sheet_description', models.CharField(blank=True, max_length=255)),
                ('vendor', models.CharField(blank=True, max_length=255, null=True)),
                ('airport', models.CharField(blank=True, choices=[('rno', 'Reno-Tahoe International Airport'), ('rts', 'Reno/Stead Airport')], max_length=125)),
                ('funding_type', models.CharField(blank=True, max_length=255, null=True)),
                ('grant_number', models.CharField(blank=True, max_length=255, null=True)),
                ('discipline', models.ManyToManyField(default=['unk'], to='fileApp.DisciplineModel')),
                ('document_type', models.ManyToManyField(default=['unk'], to='fileApp.DocumentTypeModel')),
            ],
            options={
                'ordering': ('project_title', 'project_date', 'sheet_title', 'vendor'),
            },
        ),
        migrations.CreateModel(
            name='GridCell',
            fields=[
                ('name', models.CharField(max_length=25, primary_key=True, serialize=False)),
            ],
            options={
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='SheetTypeModel',
            fields=[
                ('name', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('label', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='engineeringfilemodel',
            name='grid_cells',
            field=models.ManyToManyField(through='fileApp.EngineeringAssignment', to='fileApp.GridCell'),
        ),
        migrations.AddField(
            model_name='engineeringfilemodel',
            name='last_edited_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='engineeringfilemodel',
            name='sheet_type',
            field=models.ManyToManyField(default=['unk'], to='fileApp.SheetTypeModel'),
        ),
        migrations.AddField(
            model_name='engineeringassignment',
            name='file',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fileApp.EngineeringFileModel'),
        ),
        migrations.AddField(
            model_name='engineeringassignment',
            name='grid_cell',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fileApp.GridCell'),
        ),
        migrations.AlterUniqueTogether(
            name='engineeringassignment',
            unique_together=set([('file', 'grid_cell')]),
        ),
    ]
