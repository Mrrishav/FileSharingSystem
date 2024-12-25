from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser, UploadedFile

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        user = authenticate(username=username, password=password)
        if user and user.is_active:
            data['user'] = user
        else:
            raise serializers.ValidationError("Invalid username or password.")
        return data

class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'user_type']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=validated_data['user_type']
        )
        user.is_active = False  # Set inactive until email verification
        user.save()
        return user

class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'name', 'file', 'upload_date', 'uuid', 'size', 'download_count', 'uploaded_by']
        read_only_fields = ['upload_date', 'uuid', 'size', 'download_count', 'uploaded_by']

    def validate_file(self, file):
        allowed_extensions = UploadedFile.ALLOWED_EXTENSIONS
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            raise serializers.ValidationError(f"Invalid file extension. Allowed: {', '.join(allowed_extensions)}")
        return file
