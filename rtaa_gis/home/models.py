from django.db import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import User


# Create your models here.
class App(models.Model):
    def __str__(self):
        return "%s" % self.name

    class Meta:
        ordering = ('name',)
        app_label = 'home'

    name = models.CharField(
            max_length=25,
            primary_key=True
    )

    public = models.BooleanField(
        default=False
    )

    groups = models.ManyToManyField(Group)


class ProxyUser(User):
    """django proxy model used to add method without modifying original table"""
    class Meta:
        proxy = True

    def get_apps(self):
        user_groups = [x.name for x in self.groups.all()]
        final_apps = []
        for app in sorted(App.objects.all(), key=lambda _app: _app.name):
            if app.public:
                final_apps.append(app.name)
            else:
                groups = [x.name for x in app.groups.all()]

                if len(groups):
                    for group in groups:
                        if group in user_groups:
                            final_apps.append(app.name)
                else:
                    # no groups are assigned to the app so don't show it.
                    pass

        return final_apps
