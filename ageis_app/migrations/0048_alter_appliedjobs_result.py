# Generated by Django 4.2.7 on 2024-08-29 13:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ageis_app", "0047_merge_20240826_1110"),
    ]

    operations = [
        migrations.AlterField(
            model_name="appliedjobs",
            name="result",
            field=models.CharField(
                choices=[
                    ("default", "Pending"),
                    ("selected", "Selected"),
                    ("rejected", "Rejected"),
                    ("offerletter_sent", "Offer letter sent"),
                    ("placed", "Placed"),
                    ("on_hold", "On Hold"),
                ],
                default="default",
                max_length=20,
            ),
        ),
    ]
