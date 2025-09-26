"""HTTP views for the helpful diary backend."""

from __future__ import annotations

import logging
from typing import Dict, List

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
"""Legacy Django views module.

The dedicated Mistral REST proxy has been removed because streaming_server.py now
forwards transcripts to the language model and returns replies over the same
WebSocket connection.
"""


def _build_headers() -> Dict[str, str]:
