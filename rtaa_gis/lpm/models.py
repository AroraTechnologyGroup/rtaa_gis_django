from django.db import models


# Create your models here.
class Agreement(models.Model):
    """This is the active Agreement Model"""
    def __str__(self):
        return "%s" % self.title

    class Meta:
        ordering = ('title',)
        app_label = 'lpm'

    id = models.CharField(max_length=255, primary_key=True)

    number = models.CharField(max_length=255, unique=True)

    title = models.CharField(max_length=255, blank=True)

    status = models.CharField(max_length=255, blank=True)

    type = models.CharField(max_length=255, blank=True)

    description = models.CharField(max_length=255, blank=True, null=True)

    annual_revenue = models.CharField(max_length=255, blank=True)

    contact1_name = models.CharField(max_length=255, blank=True)

    contact1_phone_number = models.CharField(max_length=255, blank=True)

    contact1_address = models.CharField(max_length=255, blank=True)

    contact2_name = models.CharField(max_length=255, blank=True)

    contact2_phone_number = models.CharField(max_length=255, blank=True)

    contact2_address = models.CharField(max_length=255, blank=True)

    start_date = models.DateField(null=True)

    end_date = models.DateField(null=True)



