from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


### ==================== GET PROFILE ====================
class GetProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = user.profile if hasattr(user, 'profile') else None
        initials = user.username[:2].upper()

        return Response({
            'profile': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': profile.role if profile else 'guest',
                'is_approved': profile.is_approved if profile else False,
                'initials': initials,
                'date_joined': user.date_joined,
            }
        })


### ==================== UPDATE PASSWORD ====================
class UpdatePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({'error': 'current_password and new_password required'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 6:
            return Response({'error': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password updated successfully'})


### ==================== DELETE OWN ACCOUNT ====================
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        username = user.username
        user.delete()
        return Response({'message': f'Account {username} deleted permanently'})

    def post(self, request):
        return self.delete(request)