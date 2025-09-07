from django.urls import path
from . views import CsrfCookieView, RegisterView, LoginView, RefreshView, LogoutView, RegisterOtpView,RequestOtpView,ResendOtpView, VerifyOtpView
urlpatterns = [
    path('auth/csrf_cookie/',CsrfCookieView.as_view(),name='csrf_cookie'),
    path('auth/register/',RegisterView.as_view(),name='register'),
    path('auth/register_otp/',RegisterOtpView.as_view(), name='register_otp'),
    path('auth/request_otp/',RequestOtpView.as_view(),name='request_otp'),
    path('auth/resend_otp/',ResendOtpView.as_view(),name='resend_otp'),
    path('auth/verify_otp/',VerifyOtpView.as_view(),name='verify_otp'),
    path('auth/login/',LoginView.as_view(),name='login'),
    path('auth/token/refresh/',RefreshView.as_view(),name='refresh'),
    path('auth/logout/',LogoutView.as_view(),name='logout'),
]
