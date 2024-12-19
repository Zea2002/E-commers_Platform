
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, PasswordChangeView, PasswordResetRequestView, PasswordResetConfirmView,UserProfileViewSet


router = DefaultRouter()
router.register(r'profile', UserProfileViewSet, basename='profile')


urlpatterns = [
    path('', include(router.urls)),

    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('change-password/', PasswordChangeView.as_view(), name='change-password'),
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
]
