# Generated by Django 5.0.4 on 2024-04-07 05:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Type_Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('identifier', models.IntegerField(blank=True, null=True, unique=True)),
                ('product_hash', models.CharField(blank=True, max_length=32, null=True)),
                ('from_masterkala', models.BooleanField(blank=True, null=True)),
                ('commit', models.BooleanField(default=False)),
                ('deleted', models.BooleanField(default=False)),
                ('synced_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='db.type_product')),
            ],
        ),
    ]
