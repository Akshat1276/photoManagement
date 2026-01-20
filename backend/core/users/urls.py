from django.urls import path
from .views import (
	LoginView,
	OmniportCallbackView,
	OmniportLoginStartView,
	LogoutView,
	ProfileView,
	RegisterView,
	VerifyEmailView,
)
from .face_views import ReferenceSelfieUploadView, PhotosOfMeListView
urlpatterns = [
	path("register/", RegisterView.as_view(), name="auth-register"),
	path("login/", LoginView.as_view(), name="auth-login"),
	path("logout/", LogoutView.as_view(), name="auth-logout"),
	path("verify-email/", VerifyEmailView.as_view(), name="auth-verify-email"),
	path("omniport/login/", OmniportLoginStartView.as_view(), name="auth-omniport-login"),
	path("omniport/callback/", OmniportCallbackView.as_view(), name="auth-omniport-callback"),
	path("me/", ProfileView.as_view(), name="auth-profile"),
	path("face-profile/upload/", ReferenceSelfieUploadView.as_view(), name="face-profile-upload"),
		path("photos-of-me/", PhotosOfMeListView.as_view(), name="photos-of-me"),
]