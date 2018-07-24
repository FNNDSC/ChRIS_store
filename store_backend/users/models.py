from django.db import models

# Create your models here.


class UserOrganization(models.Model):
    name = models.CharField(max_length=32, unique=True)
    owner = models.ForeignKey('auth.User', on_delete=models.CASCADE,
                              related_name='organization')
    members = models.ManyToManyField('auth.User', related_name='organizations')

    class Meta:
        ordering = ('owner',)

    def __str__(self):
        return self.name