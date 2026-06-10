from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework_simplejwt.tokens import RefreshToken
from decouple import config
from .models import UserProfile
from .permissions import IsGuest, IsStaff, IsAdmin
from .serializers import RegisterSerializer, LoginSerializer


### ==================== JWT TOKEN HELPER ====================
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['role'] = user.profile.role if hasattr(user, 'profile') else 'guest'
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


### ==================== REGISTER VIEW ====================
class RegisterView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request):
        return Response({
            'fields': {
                'username': {'type': 'string', 'required': True},
                'email': {'type': 'email', 'required': True},
                'password': {'type': 'password', 'required': True},
                'role': {'type': 'choice', 'choices': ['guest', 'staff', 'admin'], 'default': 'guest'}
            }
        })

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        role = serializer.validated_data.get('role', 'guest')

        # Load fixed passwords from .env
        STAFF_PASSWORD = config('STAFF_PASSWORD', default='111111')
        ADMIN_PASSWORD = config('ADMIN_PASSWORD', default='000000')

        # Staff password check
        if role == 'staff' and password != STAFF_PASSWORD:
            return Response({'error': 'Incorrect staff password'}, status=status.HTTP_400_BAD_REQUEST)

        # Admin password check
        if role == 'admin' and password != ADMIN_PASSWORD:
            return Response({'error': 'Incorrect admin password'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        is_approved = True if role in ['guest', 'admin'] else False
        UserProfile.objects.create(user=user, role=role, is_approved=is_approved)

        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Registration successful',
            'tokens': tokens,
            'user': {'id': user.id, 'username': user.username, 'email': user.email, 'role': role}
        }, status=status.HTTP_201_CREATED)


### ==================== LOGIN VIEW ====================
class LoginView(APIView):
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get(self, request):
        return Response({
            'fields': {
                'username': {'type': 'string', 'required': True},
                'password': {'type': 'password', 'required': True}
            }
        })

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        STAFF_PASSWORD = config('STAFF_PASSWORD', default='111111')
        ADMIN_PASSWORD = config('ADMIN_PASSWORD', default='000000')

        user = authenticate(username=username, password=password)

        if user is None:
            try:
                user = User.objects.get(username=username)
                if hasattr(user, 'profile'):
                    if user.profile.role == 'staff' and password == STAFF_PASSWORD:
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                    elif user.profile.role == 'admin' and password == ADMIN_PASSWORD:
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                    else:
                        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
                else:
                    return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        tokens = get_tokens_for_user(user)
        role = user.profile.role if hasattr(user, 'profile') else 'guest'

        return Response({
            'message': 'Login successful',
            'tokens': tokens,
            'user': {'id': user.id, 'username': user.username, 'email': user.email, 'role': role}
        })


### ==================== LOGOUT VIEW ====================
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({'message': 'Logged out successfully'})


### ==================== CURRENT USER VIEW ====================
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        role = user.profile.role if hasattr(user, 'profile') else 'guest'
        return Response({
            'user': {'id': user.id, 'username': user.username, 'email': user.email, 'role': role}
        })


### ==================== GUEST DASHBOARD ====================
class GuestDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsGuest]

    def get(self, request):
        return Response({'message': 'Welcome to Guest Dashboard', 'user': request.user.username})


### ==================== STAFF DASHBOARD ====================
class StaffDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsStaff]

    def get(self, request):
        return Response({'message': 'Welcome to Staff Dashboard', 'user': request.user.username})