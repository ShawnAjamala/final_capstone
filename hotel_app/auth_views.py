from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework_simplejwt.tokens import RefreshToken
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
                'role': {'type': 'choice', 'choices': ['guest'], 'default': 'guest'}
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

        # Password length validation
        if len(password) < 6:
            return Response(
                {'error': 'Password must be at least 6 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Only allow guest registration (staff and admin are created by admin)
        if role in ['staff', 'admin']:
            return Response(
                {'error': 'Staff and Admin accounts can only be created by an administrator.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if username exists
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already taken. Please choose a different username.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if email exists
        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already registered. Please use a different email or login.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create user (only guests can register)
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(
            user=user, 
            role='guest', 
            is_approved=True,
            must_change_password=False
        )

        tokens = get_tokens_for_user(user)

        return Response({
            'message': 'Registration successful',
            'tokens': tokens,
            'user': {
                'id': user.id, 
                'username': user.username, 
                'email': user.email, 
                'role': 'guest',
                'must_change_password': False
            }
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

        # Check if username exists
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'Username not found. Please check your username or register.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Authenticate user
        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'error': 'Incorrect password. Please try again or reset your password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Check if user is approved (for staff)
        try:
            profile = UserProfile.objects.get(user=user)
            if profile.role in ['staff', 'admin'] and not profile.is_approved:
                return Response(
                    {'error': 'Your account is pending approval. Please wait for admin approval.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if password change is required
            must_change_password = profile.must_change_password
        except UserProfile.DoesNotExist:
            must_change_password = False

        tokens = get_tokens_for_user(user)
        role = user.profile.role if hasattr(user, 'profile') else 'guest'

        return Response({
            'message': 'Login successful',
            'tokens': tokens,
            'user': {
                'id': user.id, 
                'username': user.username, 
                'email': user.email, 
                'role': role,
                'must_change_password': must_change_password
            }
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
        must_change_password = user.profile.must_change_password if hasattr(user, 'profile') else False
        return Response({
            'user': {
                'id': user.id, 
                'username': user.username, 
                'email': user.email, 
                'role': role,
                'must_change_password': must_change_password
            }
        })


### ==================== CHANGE PASSWORD VIEW ====================
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'error': 'Current password and new password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_password) < 6:
            return Response(
                {'error': 'New password must be at least 6 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user

        # Check old password
        if not user.check_password(old_password):
            return Response(
                {'error': 'Current password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()

        # Clear the must_change_password flag
        try:
            profile = UserProfile.objects.get(user=user)
            profile.must_change_password = False
            profile.save()
        except UserProfile.DoesNotExist:
            pass

        return Response({
            'message': 'Password changed successfully',
            'password_updated': True
        })


### ==================== CHECK PASSWORD CHANGE REQUIRED ====================
class CheckForcePasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = UserProfile.objects.get(user=request.user)
            return Response({
                'must_change_password': profile.must_change_password
            })
        except UserProfile.DoesNotExist:
            return Response({'must_change_password': False})


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