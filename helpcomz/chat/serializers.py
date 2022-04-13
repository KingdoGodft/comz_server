# chat /serializers.py
from rest_framework import serializers
from .models import Chat
from .models import UserID


class UserIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserID
        fields = '__all__'

class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = '__all__'
        read_only_fields = ('created_at',)
