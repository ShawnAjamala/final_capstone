from rest_framework import serializers

### ==================== AUTH SERIALIZERS ====================

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, label='Username')
    email = serializers.EmailField(label='Email Address')
    password = serializers.CharField(
        min_length=6, write_only=True, style={'input_type': 'password'},
        label='Password'
    )
    role = serializers.ChoiceField(
        choices=[('guest', 'Guest'), ('staff', 'Staff'), ('admin', 'Admin')],
        default='guest', label='Account Role'
    )

    def validate_email(self, value):
        if not value.lower().endswith('@gmail.com'):
            raise serializers.ValidationError("Only Gmail addresses are allowed (@gmail.com)")
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(label='Username')
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password'}, label='Password'
    )

### ==================== END OF AUTH SERIALIZERS ====================