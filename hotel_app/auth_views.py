from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile
from .permissions import IsGuest, IsStaff


# Helper to generate JWT tokens
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    # Add custom claims
    refresh['role'] = user.profile.role if hasattr(user, 'profile') else 'guest'
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """Register new user with JWT tokens returned"""
    data = request.data

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'guest')

    if not username or not email or not password:
        return Response(
            {'error': 'username, email, and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)
    UserProfile.objects.create(user=user, role=role)

    tokens = get_tokens_for_user(user)

    return Response({
        'message': 'Registration successful',
        'tokens': tokens,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': role,
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    """Login and return JWT tokens"""
    data = request.data

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return Response(
            {'error': 'username and password required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Try normal auth first
    user = authenticate(username=username, password=password)

    # If normal auth fails, check staff with fixed password
    if user is None:
        try:
            user = User.objects.get(username=username)
            if hasattr(user, 'profile') and user.profile.role == 'staff' and password == '000000':
                user.backend = 'django.contrib.auth.backends.ModelBackend'
            else:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

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
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_user(request):
    """Blacklist refresh token"""
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logged out successfully'})
    except:
        return Response({'message': 'Logged out'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Get current user from JWT"""
    user = request.user
    role = user.profile.role if hasattr(user, 'profile') else 'guest'

    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': role,
        }
    })


# ==================== ROLE-PROTECTED TEST ENDPOINTS ====================

@api_view(['GET'])
@permission_classes([IsGuest])
def guest_dashboard(request):
    """Only guests can access"""
    return Response({
        'message': 'Welcome to Guest Dashboard',
        'user': request.user.username
    })


@api_view(['GET'])
@permission_classes([IsStaff])
def staff_dashboard(request):
    """Only staff can access"""
    return Response({
        'message': 'Welcome to Staff Dashboard',
        'user': request.user.username
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def any_dashboard(request):
    """Any authenticated user"""
    role = request.user.profile.role if hasattr(request.user, 'profile') else 'guest'
    return Response({
        'message': f'Welcome {request.user.username}',
        'role': role
    })