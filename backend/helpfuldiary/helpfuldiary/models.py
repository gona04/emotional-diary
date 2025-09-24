"""
Recording model removed.
Server should not persist or accept audio recordings — clients must use browser Web Speech API.
This file is intentionally left minimal to avoid migrations related to RecordedAudio.
"""

from django.db import models

# No models related to audio recordings remain.