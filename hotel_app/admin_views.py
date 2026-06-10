from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile
from .permissions import IsAdmin


### ==================== ADMIN DASHBOARD ====================
class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({'message': 'Welcome to Admin Dashboard', 'user': request.user.username})


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
                'date_joined': u.date_joined,
            })
        return Response({'users': data, 'total': len(data)})


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