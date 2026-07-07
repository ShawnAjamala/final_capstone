#!/usr/bin/env bash

pip install -r requirements.txt

python manage.py migrate

python manage.py shell -c "
from django.contrib.auth import get_user_model
from hotel_app.models import UserProfile

User = get_user_model()

# Get the user
user = User.objects.get(username='Shawn_admin')
print(f'✅ Found user: {user.username}')

# Make them superuser and staff
user.is_superuser = True
user.is_staff = True
user.save()
print('✅ User is now superuser and staff')

# Update profile from guest to admin
profile = UserProfile.objects.get(user=user)
profile.role = 'admin'
profile.is_approved = True
profile.must_change_password = False
profile.save()
print(f'✅ User role changed from {profile.role} to admin!')

print(f'✅ {user.username} is now an admin!')
"

python manage.py collectstatic --no-input

echo "🎉 Build completed successfully!"