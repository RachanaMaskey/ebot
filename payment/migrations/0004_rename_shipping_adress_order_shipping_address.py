# Generated by Django 5.1.3 on 2024-12-08 13:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0003_order_orderitem'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='shipping_adress',
            new_name='shipping_address',
        ),
    ]