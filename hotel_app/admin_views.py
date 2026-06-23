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
        try:
            user = User.objects.get(id=user_id)
            username = user.username
            user.delete()
            return Response({'message': f'User {username} deleted permanently'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, user_id):
        return self.delete(request, user_id)