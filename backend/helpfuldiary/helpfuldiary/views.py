from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import RecordedAudio
from .serializers import RecordedAudioSerializer
from .audio_analysis import EmotionAnalyzer

@api_view(['POST'])
def upload_audio(request):
    if request.method == 'POST':
        # Assuming 'file' is the key for the uploaded file
        audio_file = request.FILES.get('file')
        # name = request.POST.get('name')
        print(request.FILES.get('file'))
        if audio_file:
            results = EmotionAnalyzer.analyze_audio(audio_file)
            # If the audio file exists, proceed with saving it
            serializer = RecordedAudioSerializer(data={'audioFile': audio_file})
            if serializer.is_valid():
                serializer.save()
                return Response(results, status=201)
            else:
                return Response(serializer.errors, status=400)
        else:
            # If no audio file is found in the request, return an error
            return Response({'error': 'No audio file data found in the request'}, status=400)
