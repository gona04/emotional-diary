from rest_framework import serializers
from .models import RecordedAudio

class RecordedAudioSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecordedAudio
        fields = ['id', 'file']
