from django.db import models

class RecordedAudio(models.Model): 
    # name = models.CharField(max_length=200)
    file = models.BinaryField()