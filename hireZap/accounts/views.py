from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from accounts.serializers import RegisterSerializer, LoginSerializer, UserReadSerializer, VerifyEmailSerializer,ResetPasswordSerializer
from infrastructure.repositories.auth_repository import AuthUserRepository
from infrastructure.redis_client import redis_client
from infrastructure.repositories.otp_repository import OtpRepository
from core.use_cases.auth.register_user import RegisterUserUsecase
from core.use_cases.auth.login_user import LoginUserUsecase
from core.use_cases.auth.request_otp import RequestOtpUsecase
from core.use_cases.auth.verify_otp import VerifyOtpUsecase
from core.use_cases.auth.reset_password import ResetPasswordUseCase
from infrastructure.email.email_sender import EmailSender
from infrastructure.repositories.pending_reg_repository import PendingRegistraionRepository
from core.entities.user import UserEntity
from accounts.helpers import set_jwt_cookies, clear_jwt_cookies,get_tokens_for_user
from accounts.models import User
from django.conf import settings
import requests

email_sender = EmailSender()
otp_repo = OtpRepository(redis_client)
user_repo = AuthUserRepository()
reg_use_case = RegisterUserUsecase(user_repo, otp_repo)
login_use_case = LoginUserUsecase(user_repo)
request_otp_use_case = RequestOtpUsecase(otp_repo, email_sender)
verify_otp_use_case = VerifyOtpUsecase(otp_repo)
pending_reg_repo = PendingRegistraionRepository(redis_client)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CsrfCookieView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self,request):
        return Response({"detail": "CSRF cookie set"})
    
class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]  # allow any for login

    def post(self, request):
        id_token = request.data.get('id_token')
        role = request.data.get('role', 'candidate')  # default role

        if not id_token:
            return Response({'detail': 'id_token required'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Verify Google token
        google_check_url = f'https://oauth2.googleapis.com/tokeninfo?id_token={id_token}'
        r = requests.get(google_check_url)
        if r.status_code != 200:
            return Response({'detail': 'Invalid Google ID token'}, status=status.HTTP_400_BAD_REQUEST)

        payload = r.json()
        if payload.get('aud') != settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY:
            return Response({'detail': 'Token audience mismatch'}, status=status.HTTP_400_BAD_REQUEST)

        email = payload.get('email')
        name = payload.get('name') or (email.split('@')[0] if email else '')
        picture = payload.get('picture')

        if not email:
            return Response({'detail': 'Google account has no email'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Enforce role check
        user = User.objects.filter(email=email).first()
        if user:
            # already registered: block if role mismatch
            if user.role != role:
                return Response(
                    {"error": f"This email already registered as {user.role}. Please login as {user.role}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # update name/picture if changed
            changed = False
            if user.full_name != name:
                user.full_name = name; changed = True
            if user.profile_image_url != picture:
                user.profile_image_url = picture; changed = True
            if changed:
                user.save()
            created = False
        else:
            # create new user with given role
            user = User.objects.create(
                email=email,
                full_name=name,
                role=role,
                profile_image_url=picture
            )
            created = True

        # 3. Generate tokens and set cookies
        tokens = get_tokens_for_user(user)
        print(tokens)
        data = {
            'user': {
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'profile_image_url': user.profile_image_url,
            },
            'created': created
        }

        resp = Response(data, status=status.HTTP_200_OK)
        resp = set_jwt_cookies(resp, tokens['access'],tokens['refresh'])
        return resp


class GithubAuthView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get('code')
        role = request.data.get('role', 'candidate')  # default role

        if not code:
            return Response({'detail': 'code required'}, status=status.HTTP_400_BAD_REQUEST)

        # 1️⃣ Exchange code for access token
        token_url = 'https://github.com/login/oauth/access_token'
        payload = {
            'client_id': settings.SOCIAL_AUTH_GITHUB_CLIENT_ID,
            'client_secret': settings.SOCIAL_AUTH_GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': settings.GITHUB_REDIRECT_URI,
        }
        headers = {'Accept': 'application/json'}
        token_resp = requests.post(token_url, data=payload, headers=headers)
        if token_resp.status_code != 200:
            return Response({'detail': 'Failed to fetch GitHub access token'}, status=status.HTTP_400_BAD_REQUEST)
        token_data = token_resp.json()
        access_token = token_data.get('access_token')
        if not access_token:
            return Response({'detail': 'No access token received from GitHub'}, status=status.HTTP_400_BAD_REQUEST)

        # 2️⃣ Get user info from GitHub
        user_resp = requests.get('https://api.github.com/user', headers={'Authorization': f'token {access_token}'})
        if user_resp.status_code != 200:
            return Response({'detail': 'Failed to fetch GitHub user info'}, status=status.HTTP_400_BAD_REQUEST)

        gh_user = user_resp.json()
        email = gh_user.get('email')
        name = gh_user.get('name') or (email.split('@')[0] if email else '')
        avatar_url = gh_user.get('avatar_url')

        # GitHub emails can be null; fetch public emails if needed
        if not email:
            emails_resp = requests.get('https://api.github.com/user/emails', headers={'Authorization': f'token {access_token}'})
            if emails_resp.status_code == 200:
                emails = emails_resp.json()
                primary_email = next((e['email'] for e in emails if e.get('primary') and e.get('verified')), None)
                email = primary_email
        if not email:
            return Response({'detail': 'GitHub account has no verified email'}, status=status.HTTP_400_BAD_REQUEST)

        # 3️⃣ Check existing user or create new
        user = User.objects.filter(email=email).first()
        if user:
            if user.role != role:
                return Response(
                    {"error": f"This email already registered as {user.role}. Please login as {user.role}."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            changed = False
            if user.full_name != name:
                user.full_name = name; changed = True
            if user.profile_image_url != avatar_url:
                user.profile_image_url = avatar_url; changed = True
            if changed:
                user.save()
            created = False
        else:
            user = User.objects.create(
                email=email,
                full_name=name,
                role=role,
                profile_image_url=avatar_url
            )
            created = True

        # 4️⃣ Generate tokens & set cookies
        tokens = get_tokens_for_user(user)
        data = {
            'user': {
                'email': user.email,
                'full_name': user.full_name,
                'role': user.role,
                'profile_image_url': user.profile_image_url,
            },
            'created': created
        }

        resp = Response(data, status=status.HTTP_200_OK)
        resp = set_jwt_cookies(resp, tokens['access'],tokens['refresh'])
        return resp

    
class RequestOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self,request):
        email = request.data.get("email")
        action_type = request.data.get("action_type")
        result = request_otp_use_case.execute(email, action_type)
        return Response(result)
    
class ResendOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self,request):
        email = request.data.get("email")
        action_type = request.data.get("action_type")
        if not email or not action_type:
            return Response({"detail":"email and action_type required"}, status=status.HTTP_400_BAD_REQUEST)
        result = request_otp_use_case.execute(email,action_type, resend=True)
        return Response(result)
    
class VerifyOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self,request):
        email = request.data.get('email')
        code = request.data.get('code')
        action_type = request.data.get('action_type')
        verified = verify_otp_use_case.execute(email,code,action_type)
        return Response({'verified':verified})
    
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data= request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        pending_reg_repo.save(data['email'],{
            "name":data["name"],
            "password":data["password"],
            "role":data.get("role","candidate"),
            "phone":data.get("phone"),
            "profile_image_url":data.get("profile_image_url")
        })

        saved = pending_reg_repo.get(data['email'])

        # Requesting for otp
        request_otp_use_case.execute(data['email'],"registration")
        
        return Response(
            {'message':'OTP sent to your email. Please verify to complete the registration'},
            status= status.HTTP_200_OK
        )
class RegisterOtpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')
        if not email or not code:
            return Response({'detail':'Email and OTP are required'}, status= status.HTTP_400_BAD_REQUEST)
        
        
        verified = verify_otp_use_case.execute(email, code, 'registration')
        if not verified:
            return Response({'detail':'Invalid or expired OTP'}, status=status.HTTP_400_BAD_REQUEST)

        pending = pending_reg_repo.get(email)
        if not pending:
            return Response({'detail':"Registration data expired"},status=status.HTTP_400_BAD_REQUEST)
        user_entity = UserEntity(
            id = None,
            full_name= pending["name"],
            email= email,
            password= pending["password"],
            phone= pending.get("phone"),
            role= pending.get("role","candidate"),
            profile_image_url= pending.get("profile_image_url")
        )
        otp_entity = pending_reg_repo.get(email)
        otp_in_repo = verify_otp_use_case.otp_repo.get_otp(email, 'registration')

        try:
            created_user = reg_use_case.execute(user_entity)
        except ValueError as e:
            return Response({'detail': str(e)}, status= status.HTTP_400_BAD_REQUEST)
        
        pending_reg_repo.delete(email)
        
        #jwt token for the newly registered user    
        refresh = RefreshToken.for_user(created_user)
        access = refresh.access_token

        response = Response(UserReadSerializer(created_user).data, status = status.HTTP_201_CREATED)
        set_jwt_cookies(response,access, refresh, remember_me=False)

        return response
    
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    renderer_classes = [JSONRenderer]
    def post(self,request):
        serializer = LoginSerializer(data = request.data)
        serializer.is_valid(raise_exception= True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        remember_me = serializer.validated_data.get('remember_me', False)

        try:
            user = login_use_case.execute(email, password)
        except ValueError:
            return Response({'detail': 'invalid credentials'}, status= status.HTTP_401_UNAUTHORIZED)
        
        # CREATE TOKENS USING SIMPLE JWT
        refresh = RefreshToken.for_user(user)
        #optinally change the refresh expiration dynamicalluy
        access = refresh.access_token
        #update last_login
        user_repo.update_last_login(user.id)
        response = Response({"user":UserReadSerializer(user).data})
        set_jwt_cookies(response, access, refresh, remember_me= remember_me)
        return response
    

class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_cookie = request.COOKIES.get('refresh')
        if not refresh_cookie:
            return Response({"detail":"No refresh token"}, status= status.HTTP_401_UNAUTHORIZED)
        try:
            token = RefreshToken(refresh_cookie)
            user_id = token.get("user_id") or token.get("user") or token.get("user_id")
            if not user_id:
                return Response({"detail":"Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
            user = User.objects.get(id=user_id)

            #blacklist old token 
            try:
                token.blacklist()
            except Exception:
                pass
            # create new token
            new_refresh = RefreshToken.for_user(user)
            new_access = new_refresh.access_token
            response = Response({"detail":"refreshed"})
            set_jwt_cookies(response, new_access, new_refresh, remember_me= False)
            return response
        
        except TokenError:
            return Response({"detail":"Invalid refresh token"}, status= status.HTTP_401_UNAUTHORIZED)
        
class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_cookie = request.COOKIES.get("refresh")
        if refresh_cookie:
            try:
                token = RefreshToken(refresh_cookie)
                token.blacklist()
            except Exception:
                pass

        response = Response({"detail":"logged out"})
        clear_jwt_cookies(response)
        return response

class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self,request):
        serializer = VerifyEmailSerializer(data={"email":request.data.get("email")})
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data.get("role")
        action_type = serializer.validated_data.get("action_type")

        user = user_repo.get_by_email(email)
        if not user:
            return Response({"message":"Email is not registered"}, status=status.HTTP_404_NOT_FOUND)
        
        otp_result = request_otp_use_case.execute(email,action_type)

        return Response(
            {
                "message":"Verify otp sent to your email!",
                "role":role,
                "action_type":action_type,
                "code":otp_result,
            },status=status.HTTP_200_OK
        )
    
class ResetPasswordView(APIView):
    permission_classes =  [permissions.AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reset_password_use_case = ResetPasswordUseCase(user_repo)

    def post(self,request):
        serializer = ResetPasswordSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        res = self.reset_password_use_case.execute(email, password)
        if not res:
            return Response({"message":"user not found"},status= status.HTTP_404_NOT_FOUND)
        return Response({"message":"Reset password successful"},status=status.HTTP_200_OK)
        
class FetchUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self,request):
        serializer = UserReadSerializer(request.user)
        return Response(serializer.data)
    


    
