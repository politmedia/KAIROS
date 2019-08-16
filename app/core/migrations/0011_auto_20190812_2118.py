# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-08-12 21:18
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_auto_20190812_0339'),
    ]

    operations = [
        migrations.CreateModel(
            name='Constituency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='name')),
            ],
            options={
                'verbose_name': 'constituency',
                'verbose_name_plural': 'constituencies',
            },
        ),
        migrations.AddField(
            model_name='candidacy',
            name='constituency',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.Constituency', verbose_name='constituency'),
        ),
        migrations.AddField(
            model_name='mandate',
            name='constituency',
            field=models.ManyToManyField(to='core.Constituency', verbose_name='constituency'),
        ),
    ]