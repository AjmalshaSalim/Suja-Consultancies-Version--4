# Generated by Django 4.2.7 on 2024-08-24 16:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ageis_app", "0041_jobcategories_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="extendedusermodel",
            name="country",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="extendedusermodel",
            name="district",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="extendedusermodel",
            name="state",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterUniqueTogether(
            name="experience",
            unique_together={("user", "company", "position", "start_date")},
        ),
        migrations.AlterUniqueTogether(
            name="qualification",
            unique_together={("user", "degree", "institution")},
        ),
    ]
