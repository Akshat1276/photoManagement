import secrets
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework import generics, permissions, response, status
from rest_framework.views import APIView
from core.models import EmailVerificationCode, Profile, User
from .serializers import (
	EmailVerificationSerializer,
	LoginSerializer,
	ProfileSerializer,
	RegisterSerializer,
)

class RegisterView(generics.CreateAPIView):
	serializer_class = RegisterSerializer
	permission_classes = [permissions.AllowAny]

	def perform_create(self, serializer):
		user = serializer.save()
		otp_code = get_random_string(length=6, allowed_chars="0123456789")
		code = EmailVerificationCode.objects.create(
			user=user,
			code=otp_code,
		)
		message = f"Your verification code is: {otp_code}"
		send_mail(
			"Verify your email",
			message,
			settings.DEFAULT_FROM_EMAIL,
			[user.email],
			fail_silently=True,
		)

class LoginView(APIView):
	permission_classes = [permissions.AllowAny]
	def post(self, request, *args, **kwargs):
		serializer = LoginSerializer(data=request.data, context={"request": request})
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data["user"]
		
		from django.contrib.auth import login

		login(request, user)
		return response.Response({"detail": "Logged in successfully."}, status=status.HTTP_200_OK)

class LogoutView(APIView):
	permission_classes = [permissions.IsAuthenticated]
	def post(self, request, *args, **kwargs):
		from django.contrib.auth import logout
		logout(request)
		return response.Response(
			{"detail": "Logged out successfully."},
			status=status.HTTP_200_OK,
		)

class VerifyEmailView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request, *args, **kwargs):
		serializer = EmailVerificationSerializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.validated_data["user"]
		otp = serializer.validated_data["otp"]
		otp.is_used = True
		otp.save(update_fields=["is_used"])
		if not user.is_verified:
			user.is_verified = True
			user.save(update_fields=["is_verified"])
		return response.Response(
			{"detail": "Email verified successfully."},
			status=status.HTTP_200_OK,
		)

class OmniportLoginStartView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request, *args, **kwargs):
		base = settings.OMNIPORT_BASE_URL
		client_id = settings.OMNIPORT_CLIENT_ID
		redirect_uri = settings.OMNIPORT_REDIRECT_URI
		if not (base and client_id and redirect_uri):
			return response.Response(
				{"detail": "Omniport OAuth is not configured."},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)
		state = secrets.token_urlsafe(16)
		request.session["omniport_oauth_state"] = state
		authorise_url = f"{base}/oauth/authorise/"
		params = {
			"client_id": client_id,
			"redirect_uri": redirect_uri,
			"state": state,
		}
		from urllib.parse import urlencode

		full_url = f"{authorise_url}?{urlencode(params)}"
		return response.Response({"authorization_url": full_url})

class OmniportCallbackView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request, *args, **kwargs):
		code = request.query_params.get("code")
		state = request.query_params.get("state")
		expected_state = request.session.get("omniport_oauth_state")
		if not code or (expected_state and state != expected_state):
			return response.Response(
				{"detail": "Invalid Omniport callback."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		base = settings.OMNIPORT_BASE_URL
		client_id = settings.OMNIPORT_CLIENT_ID
		client_secret = settings.OMNIPORT_CLIENT_SECRET
		redirect_uri = settings.OMNIPORT_REDIRECT_URI
		try:
			token_resp = requests.post(
				f"{base}/open_auth/token/",
				data={
					"client_id": client_id,
					"client_secret": client_secret,
					"grant_type": "authorization_code",
					"redirect_uri": redirect_uri,
					"code": code,
				},
				timeout=10,
			)
			token_resp.raise_for_status()
			tokens = token_resp.json()
			access_token = tokens.get("access_token")
			if not access_token:
				return response.Response(
					{"detail": "Failed to obtain access token from Omniport."},
					status=status.HTTP_502_BAD_GATEWAY,
				)
		except Exception:
			return response.Response(
				{"detail": "Error while contacting Omniport token endpoint."},
				status=status.HTTP_502_BAD_GATEWAY,
			)

		try:
			user_resp = requests.get(
				f"{base}/open_auth/get_user_data/",
				headers={"Authorization": f"Bearer {access_token}"},
				timeout=10,
			)
			user_resp.raise_for_status()
			data = user_resp.json()
		except Exception:
			return response.Response(
				{"detail": "Error while fetching user data from Omniport."},
				status=status.HTTP_502_BAD_GATEWAY,
			)

		person = data.get("person", {}) or {}
		contact = data.get("contact_information") or data.get("contactInformation") or {}
		student = data.get("student", {}) or {}
		full_name = (
			person.get("full_name")
			or person.get("short_name")
			or person.get("fullName")
			or person.get("shortName")
			or "Omniport User"
		)
		profile_pic_url = person.get("display_picture") or person.get("displayPicture")
		email = (
			contact.get("email_address")
			or contact.get("institute_webmail_address")
			or contact.get("primaryEmailAddress")
			or contact.get("instituteWebmailAddress")
		)

		username_fallback = data.get("username") or str(data.get("userId") or "user")
		if not email:
			email = f"{username_fallback}@example.com"

		branch = student.get("branch", {}) or {}
		department_obj = branch.get("department", {}) or {}
		department = (
			department_obj.get("name")
			or branch.get("department_name")
			or branch.get("name")
		)
		end_date = student.get("end_date") or student.get("endDate")
		batch = None
		if isinstance(end_date, str) and len(end_date) >= 4:
			batch = end_date[:4]

		user, _created = User.objects.get_or_create(
			email=email,
			defaults={"is_verified": True},
		)
		if not user.is_verified:
			user.is_verified = True
			user.save(update_fields=["is_verified"])

		profile, profile_created = Profile.objects.get_or_create(user=user)
		profile_updated = False
		if full_name and (profile_created or not profile.full_name):
			profile.full_name = full_name
			profile_updated = True
		if profile_pic_url and (profile_created or not profile.profile_pic_url):
			profile.profile_pic_url = profile_pic_url
			profile_updated = True
		if department and (profile_created or not profile.department):
			profile.department = department
			profile_updated = True
		if batch and (profile_created or not profile.batch):
			profile.batch = batch
			profile_updated = True
		if profile_updated:
			profile.save()
		from django.contrib.auth import login
		login(request, user)
		return response.Response(
			{"detail": "Logged in with Omniport.", "email": user.email},
			status=status.HTTP_200_OK,
		)
class ProfileView(generics.RetrieveUpdateAPIView):
	serializer_class = ProfileSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_object(self):
		return Profile.objects.get(user=self.request.user)