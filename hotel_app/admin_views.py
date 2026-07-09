from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.mail import send_mail
from django.conf import settings
from .models import UserProfile
from .permissions import IsAdmin
import random
import string


### ==================== ADMIN DASHBOARD ====================
class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({'message': 'Welcome to Admin Dashboard', 'user': request.user.username})


### ==================== CREATE ADMIN (FIRST TIME ONLY) ====================
class CreateAdminView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Check if admin already exists
        if UserProfile.objects.filter(role='admin').exists():
            return Response(
                {'error': 'An admin already exists. Only one admin is allowed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        if not all([username, email, password]):
            return Response(
                {'error': 'Username, email, and password required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(password) < 6:
            return Response(
                {'error': 'Password must be at least 6 characters long'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Create profile with admin role
        profile = UserProfile.objects.create(
            user=user,
            role='admin',
            is_approved=True,
            must_change_password=False
        )

        return Response({
            'message': 'Admin account created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': profile.role
            }
        }, status=status.HTTP_201_CREATED)


### ==================== ADMIN CREATE STAFF ====================
class AdminCreateStaffView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        role = request.data.get('role', 'staff')

        if not username or not email:
            return Response(
                {'error': 'Username and email are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user exists
        if User.objects.filter(username=username).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate random password
        password = ''.join(random.choices(
            string.ascii_letters + string.digits + '!@#$%^&*',
            k=10
        ))

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Create profile with must_change_password=True
        profile = UserProfile.objects.create(
            user=user,
            role=role,
            is_approved=True,
            must_change_password=True  # Force password change on first login
        )

        # Send email with credentials
        try:
            send_mail(
                subject='Welcome to Grand Horizon Hotel - Your Staff Account',
                message=f"""
Hello {username},

Your staff account has been created for Grand Horizon Hotel.

Login Credentials:
Username: {username}
Password: {password}

IMPORTANT: You will be required to change your password upon first login.

Login URL: https://hotel-frontend-dun.vercel.app/login

If you have any issues, please contact your administrator.

Thank you,
Grand Horizon Hotel Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            
            return Response({
                'message': f'Staff account created for {username}. Credentials sent to {email}.',
                'username': username,
                'email': email,
                'role': role,
                'password': password
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'message': 'Staff created but email sending failed',
                'error': str(e),
                'username': username,
                'password': password,
                'email': email,
                'role': role
            }, status=status.HTTP_201_CREATED)


### ==================== ADMIN CHANGE STAFF PASSWORD ====================
class AdminChangeStaffPasswordView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile if hasattr(user, 'profile') else None
            
            if not profile:
                return Response(
                    {'error': 'User profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Only allow changing password for staff and admin users
            if profile.role not in ['staff', 'admin']:
                return Response(
                    {'error': 'Can only change password for staff or admin users'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            new_password = request.data.get('new_password')
            
            if not new_password:
                return Response(
                    {'error': 'New password is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(new_password) < 6:
                return Response(
                    {'error': 'Password must be at least 6 characters long'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(new_password)
            user.save()
            
            # Set must_change_password flag to True so staff changes it on next login
            profile.must_change_password = True
            profile.save()
            
            return Response({
                'message': f'Password for {user.username} updated successfully',
                'username': user.username,
                'role': profile.role,
                'must_change_password': True
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )


### ==================== LIST ALL USERS ====================
class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        users = User.objects.all().select_related('profile')
        data = []
        for u in users:
            data.append({
                'id': u.id,
                'username': u.username,
                'email': u.email,
                'role': u.profile.role if hasattr(u, 'profile') else 'guest',
                'is_approved': u.profile.is_approved if hasattr(u, 'profile') else False,
                'must_change_password': u.profile.must_change_password if hasattr(u, 'profile') else False,
                'date_joined': u.date_joined,
            })
        return Response({'users': data, 'total': len(data)})


### ==================== LIST GUESTS ONLY ====================
class ListGuestsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        guests = UserProfile.objects.filter(role='guest').select_related('user')
        data = []
        for p in guests:
            data.append({
                'id': p.user.id,
                'username': p.user.username,
                'email': p.user.email,
                'role': p.role,
                'date_joined': p.user.date_joined,
            })
        return Response({'guests': data, 'total': len(data)})


### ==================== LIST STAFF ONLY ====================
class ListStaffView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        staff = UserProfile.objects.filter(role='staff').select_related('user')
        data = []
        for p in staff:
            data.append({
                'id': p.user.id,
                'username': p.user.username,
                'email': p.user.email,
                'role': p.role,
                'is_approved': p.is_approved,
                'must_change_password': p.must_change_password,
                'date_joined': p.user.date_joined,
            })
        return Response({'staff': data, 'total': len(data)})


### ==================== LIST ADMINS ONLY ====================
class ListAdminsView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        admins = UserProfile.objects.filter(role='admin').select_related('user')
        data = []
        for p in admins:
            data.append({
                'id': p.user.id,
                'username': p.user.username,
                'email': p.user.email,
                'role': p.role,
                'date_joined': p.user.date_joined,
            })
        return Response({'admins': data, 'total': len(data)})


### ==================== PENDING STAFF APPROVALS ====================
class PendingStaffView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        pending = UserProfile.objects.filter(role='staff', is_approved=False)
        data = []
        for p in pending:
            data.append({
                'id': p.user.id,
                'username': p.user.username,
                'email': p.user.email,
                'is_approved': p.is_approved,
            })
        return Response({'pending_staff': data, 'total': len(data)})


### ==================== APPROVE STAFF ====================
class ApproveStaffView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = UserProfile.objects.get(user_id=user_id, role='staff')
            profile.is_approved = True
            profile.save()
            return Response({'message': f'Staff {profile.user.username} approved'})
        except UserProfile.DoesNotExist:
            return Response({'error': 'Staff user not found'}, status=status.HTTP_404_NOT_FOUND)


### ==================== UNAPPROVE STAFF ====================
class UnapproveStaffView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            profile = UserProfile.objects.get(user_id=user_id, role='staff')
            profile.is_approved = False
            profile.save()
            return Response({'message': f'Staff {profile.user.username} unapproved'})
        except UserProfile.DoesNotExist:
            return Response({'error': 'Staff user not found'}, status=status.HTTP_404_NOT_FOUND)


### ==================== REJECT/DELETE STAFF ====================
class RejectStaffView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=user_id)
            username = user.username
            user.delete()
            return Response({'message': f'Staff {username} rejected and removed'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


### ==================== DELETE USER PERMANENTLY ====================
class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, user_id):
        # Prevent deleting the last admin
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile if hasattr(user, 'profile') else None
            
            if profile and profile.role == 'admin':
                admin_count = UserProfile.objects.filter(role='admin').count()
                if admin_count <= 1:
                    return Response(
                        {'error': 'Cannot delete the only admin account'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            username = user.username
            user.delete()
            return Response({'message': f'User {username} deleted permanently'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, user_id):
        return self.delete(request, user_id)


### ==================== UPDATE USER ROLE ====================
class UpdateUserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile if hasattr(user, 'profile') else None
            
            if not profile:
                return Response({'error': 'User profile not found'}, status=status.HTTP_404_NOT_FOUND)
            
            new_role = request.data.get('role')
            
            # Prevent setting role to admin if one already exists
            if new_role == 'admin':
                if UserProfile.objects.filter(role='admin').exclude(id=profile.id).exists():
                    return Response(
                        {'error': 'An admin already exists. Only one admin is allowed.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Prevent demoting the only admin
            if profile.role == 'admin' and new_role != 'admin':
                admin_count = UserProfile.objects.filter(role='admin').count()
                if admin_count <= 1:
                    return Response(
                        {'error': 'Cannot demote the only admin account'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            profile.role = new_role
            profile.save()
            
            return Response({
                'message': f'User {user.username} role updated to {new_role}',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': profile.role
                }
            })
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)