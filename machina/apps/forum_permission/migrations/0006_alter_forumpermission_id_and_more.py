# Generated by Django 4.2.11 on 2024-04-14 18:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum_permission', '0005_userforumpermission_authenticated_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forumpermission',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='groupforumpermission',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='userforumpermission',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]