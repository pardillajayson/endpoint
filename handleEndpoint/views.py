from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
import json
import logging


@csrf_exempt
def submit_contact(request):
	"""Accept POSTed contact data (form-encoded or JSON) and email it to site owner.

	Handles OPTIONS preflight for simple CORS support during development.
	Expected fields: name, email, message
	Returns JSON: {ok: true} on success or {error: '...'} on failure.
	"""

	# Support CORS preflight requests (browsers send OPTIONS before POST when needed)
	if request.method == 'OPTIONS':
		resp = JsonResponse({'ok': True})
		resp['Access-Control-Allow-Origin'] = '*'
		resp['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
		resp['Access-Control-Allow-Headers'] = 'Content-Type'
		return resp

	if request.method != 'POST':
		resp = JsonResponse({'error': 'POST required'}, status=405)
		resp['Access-Control-Allow-Origin'] = '*'
		return resp

	try:
		if request.content_type and 'application/json' in request.content_type:
			data = json.loads(request.body.decode('utf-8') or '{}')
		else:
			data = request.POST

		name = data.get('name')
		email = data.get('email')
		message = data.get('message')

		if not (name and email and message):
			resp = JsonResponse({'error': 'Missing required fields'}, status=400)
			resp['Access-Control-Allow-Origin'] = '*'
			return resp

		subject = f'Portfolio contact from {name}'
		body = f'Name: {name}\nEmail: {email}\n\nMessage:\n{message}'
		recipient_list = [settings.EMAIL_HOST_USER]

		# Basic guard: ensure sender/recipient are configured
		if not settings.EMAIL_HOST_USER or not settings.DEFAULT_FROM_EMAIL:
			logging.error('Email settings missing: EMAIL_HOST_USER=%r DEFAULT_FROM_EMAIL=%r', settings.EMAIL_HOST_USER, settings.DEFAULT_FROM_EMAIL)
			resp = JsonResponse({'error': 'Email sender not configured'}, status=500)
			resp['Access-Control-Allow-Origin'] = '*'
			return resp

		send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=False)
		resp = JsonResponse({'ok': True})
		resp['Access-Control-Allow-Origin'] = '*'
		return resp

	except BadHeaderError:
		resp = JsonResponse({'error': 'Invalid header'}, status=400)
		resp['Access-Control-Allow-Origin'] = '*'
		return resp
	except Exception as exc:
		logging.exception('Unhandled exception in submit_contact')
		resp = JsonResponse({'error': 'Internal server error'}, status=500)
		resp['Access-Control-Allow-Origin'] = '*'
		return resp
