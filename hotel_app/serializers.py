from rest_framework import serializers

### ==================== AUTH SERIALIZERS ====================

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, label='Username')
    email = serializers.EmailField(label='Email Address')
    password = serializers.CharField(
        min_length=6, write_only=True, style={'input_type': 'password'},
        help_text='Staff must use: 111111', label='Password'
    )
    role = serializers.ChoiceField(
        choices=[('guest', 'Guest'), ('staff', 'Staff')],
        default='guest', label='Account Role'
    )


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(label='Username')
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password'},
        help_text='Staff: 111111 | Admin: 000000', label='Password'
    )

### ==================== END OF AUTH SERIALIZERS ====================