from rest_framework import serializers
from . import models



class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ["email", "username", "first_name", "last_name", "password"]

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = super().create(validated_data)
        user.set_password(password)
        user.save()
        return user
    
class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(
        max_length=68, min_length=3, write_only=True)

    class Meta:
        model = models.User
        fields = ["email", "password"]