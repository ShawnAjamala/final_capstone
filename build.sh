#!/usr/bin/env bash

pip install -r requirements.txt

python manage.py migrate

python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='Shawn_admin').exists():
    User.objects.create_superuser('Shawn_admin', 'shawnajamala1@gmail.com', 'Shawn@1234')
"

python manage.py collectstatic --no-input