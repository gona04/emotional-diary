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
from rest_framework.response import Response

LOG = logging.getLogger(__name__)

MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"


def _build_headers() -> Dict[str, str]:
	api_key = getattr(settings, "MISTRAL_API_KEY", "")
	if not api_key:
		raise RuntimeError("MISTRAL_API_KEY is not configured in the backend environment.")
	return {
		"Authorization": f"Bearer {api_key}",
		"Content-Type": "application/json",
	}


def _build_messages(user_prompt: str) -> List[Dict[str, str]]:
	system_prompt = getattr(settings, "MISTRAL_SYSTEM_PROMPT", "")
	messages: List[Dict[str, str]] = []
	if system_prompt:
		messages.append({"role": "system", "content": system_prompt})
	messages.append({"role": "user", "content": user_prompt})
	return messages


@api_view(["POST"])
@permission_classes([AllowAny])
def mistral_chat(request: Request) -> Response:
	"""Proxy chat completion requests to the Mistral API."""

	prompt = (request.data.get("prompt") or "").strip()
	if not prompt:
		return Response({"error": "prompt_required"}, status=status.HTTP_400_BAD_REQUEST)

	prompt_preview = prompt if len(prompt) <= 500 else f"{prompt[:500]}…"
	LOG.info("Received transcript prompt: %s", prompt_preview)

	payload = {
		"model": getattr(settings, "MISTRAL_MODEL", "mistral-small-latest"),
		"messages": _build_messages(prompt),
	}

	timeout = float(getattr(settings, "MISTRAL_TIMEOUT", 30))

	try:
		response = requests.post(
			MISTRAL_CHAT_URL,
			headers=_build_headers(),
			json=payload,
			timeout=timeout,
		)
	except requests.RequestException as exc:  # pragma: no cover - network failure
		LOG.exception("Mistral chat request failed")
		return Response(
			{"error": "upstream_unreachable", "detail": str(exc)},
			status=status.HTTP_502_BAD_GATEWAY,
		)

	if response.status_code >= 400:
		LOG.warning("Mistral chat error %s: %s", response.status_code, response.text)
		return Response(
			{
				"error": "upstream_error",
				"status_code": response.status_code,
				"detail": response.text,
			},
			status=status.HTTP_502_BAD_GATEWAY,
		)

	try:
		data = response.json()
	except ValueError:
		LOG.error("Mistral chat returned non-JSON payload: %s", response.text[:200])
		return Response({"error": "invalid_upstream_response"}, status=status.HTTP_502_BAD_GATEWAY)

	choices = data.get("choices") or []
	message = choices[0].get("message") if choices else None
	content = (message or {}).get("content", "").strip()

	if not content:
		content = "I'm here and listening."

	reply_preview = content if len(content) <= 500 else f"{content[:500]}…"
	LOG.info("Mistral assistant reply: %s", reply_preview)

	return Response({"text": content})

