# Generated by Django 3.2.3 on 2024-04-15 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20240414_2253'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myuser',
            name='first_name',
            field=models.CharField(max_length=150, verbose_name='Имя'),
        ),
        migrations.AlterField(
            model_name='myuser',
            name='last_name',
            field=models.CharField(max_length=150, verbose_name='Фамилия'),
        ),
    ]
