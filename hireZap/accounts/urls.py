from django.urls import path
from . views import CsrfCookieView, RegisterView, LoginView, RefreshView, LogoutView, RegisterOtpView,RequestOtpView,ResendOtpView, VerifyOtpView, ForgotPasswordView,ResetPasswordView,FetchUserView,GoogleAuthView,GithubAuthView 
urlpatterns = [
    path('auth/me/', FetchUserView.as_view(), name='auth_me'),
    path('auth/csrf-cookie/',CsrfCookieView.as_view(),name='csrf-cookie'),
    path('auth/register/',RegisterView.as_view(),name='register'),
    path('auth/register-otp/',RegisterOtpView.as_view(), name='register-otp'),
    path('auth/request-otp/',RequestOtpView.as_view(),name='request-otp'),
    path('auth/resend-otp/',ResendOtpView.as_view(),name='resend-otp'),
    path('auth/verify-otp/',VerifyOtpView.as_view(),name='verify-otp'),
    path('auth/forgot-password/',ForgotPasswordView.as_view(),name='forgot-password'),
    path('auth/reset-password/',ResetPasswordView.as_view(),name="reset-password"),
    path('auth/login/',LoginView.as_view(),name='login'),
    path('auth/fetch-user/',FetchUserView.as_view(),name='fetch-user'),
    path('auth/token/refresh/',RefreshView.as_view(),name='refresh'),
    path('auth/logout/',LogoutView.as_view(),name='logout'),
    path('auth/google/', GoogleAuthView.as_view(), name='social_google'),
    path('auth/github/',GithubAuthView.as_view(), name='social_google'),
]
 