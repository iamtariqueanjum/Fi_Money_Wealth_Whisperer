from django.db import models

# Create your models here.

class User(models.Model):
    userid = models.AutoField(primary_key=True)
    username = models.CharField(max_length=150, unique=True)

    def __str__(self):
        return self.username
