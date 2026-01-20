from django.contrib.auth import authenticate
from rest_framework import serializers
from core.models import EmailVerificationCode, Profile, User


class RegisterSerializer(serializers.ModelSerializer):
	password = serializers.CharField(write_only=True, min_length=8)
	full_name = serializers.CharField(write_only=True, required=True)

	class Meta:
		model = User
		fields = ["email", "password", "full_name"]

	def create(self, validated_data):
		full_name = validated_data.pop("full_name")
		password = validated_data.pop("password")
		user = User.objects.create_user(email=validated_data["email"], password=password)
		# Profile.objects.create(user=user, full_name=full_name)
		return user


class LoginSerializer(serializers.Serializer):
	email = serializers.EmailField()
	password = serializers.CharField(write_only=True)

	def validate(self, attrs):
		email = attrs.get("email")
		password = attrs.get("password")
		user = authenticate(request=self.context.get("request"), email=email, password=password)
		if not user:
			raise serializers.ValidationError("Invalid email or password.")
		if not user.is_active:
			raise serializers.ValidationError("User account is disabled.")
		if not user.is_verified:
			raise serializers.ValidationError("Email address is not verified.")
		attrs["user"] = user
		return attrs


class ProfileSerializer(serializers.ModelSerializer):
	email = serializers.EmailField(source="user.email", read_only=True)

	is_admin = serializers.SerializerMethodField()


	def get_is_admin(self, obj):
		user = obj.user
		if not user or not user.is_authenticated:
			return False
		# Check if user has a role named 'Admin' (case-insensitive)
		return user.roles.filter(name__iexact="admin").exists()

	class Meta:
		model = Profile
		fields = [
			"email",
			"full_name",
			"bio",
			"batch",
			"department",
			"profile_pic_url",
			"is_admin",
		]
class EmailVerificationSerializer(serializers.Serializer):
	email = serializers.EmailField()
	code = serializers.CharField(max_length=6)

	def validate(self, attrs):
		email = attrs.get("email")
		code = attrs.get("code")
		try:
			user = User.objects.get(email=email)
		except User.DoesNotExist:
			raise serializers.ValidationError({"email": "User with this email does not exist."})

		otp_qs = (
			EmailVerificationCode.objects.filter(user=user, is_used=False)
			.order_by("-created_at")
		)
		otp = otp_qs.first()
		if not otp or otp.code != code:
			raise serializers.ValidationError({"code": "Invalid verification code."})
		if otp.is_expired():
			raise serializers.ValidationError({"code": "Verification code has expired."})

		attrs["user"] = user
		attrs["otp"] = otp
		return attrs