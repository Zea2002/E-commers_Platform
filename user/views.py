
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.conf import settings
from django.template.loader import render_to_string
from rest_framework import serializers
from django.contrib.auth import validate_password
from rest_framework import viewsets


from .serializers import RegisterSerializer, PasswordChangeSerializer, UserSerializer

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()  # Get all users
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]  # Ensure the user is authenticated

    # Optionally, we can limit the queryset to the authenticated user
    def get_queryset(self):
        return get_user_model().objects.filter(id=self.request.user.id)
    

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, email=email, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'token_type': 'Bearer',
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

class PasswordChangeView(APIView):
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"detail": "Old password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = get_user_model().objects.get(email=email)
            uidb64 = urlsafe_base64_encode(str(user.pk).encode())
            token = default_token_generator.make_token(user)
            reset_link = f"http://{request.get_host()}/reset/{uidb64}/{token}/"

            subject = "Password Reset Request"
            message = render_to_string('password_reset_email.html', {
                'user': user,
                'reset_link': reset_link,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

            return Response({"message": "Password reset email has been sent."}, status=status.HTTP_200_OK)
        except get_user_model().DoesNotExist:
            return Response({"error": "No user found with this email."}, status=status.HTTP_404_NOT_FOUND)

class PasswordResetConfirmView(APIView):
    class PasswordResetSerializer(serializers.Serializer):
        new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
        confirm_password = serializers.CharField(required=True, write_only=True)

        def validate(self, data):
            if data['new_password'] != data['confirm_password']:
                raise serializers.ValidationError("Passwords do not match.")
            return data

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = get_user_model().objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                serializer = self.PasswordResetSerializer(data=request.data)
                if serializer.is_valid():
                    user.set_password(serializer.validated_data['new_password'])
                    user.save()
                    return Response({"message": "Password successfully reset."}, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
