# chat /serializers.py
from rest_framework import serializers
from .models import Chat
from .models import UserID
from .models import PCParts

class UserIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserID
        fields = '__all__'


class PCPartsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PCParts
        fields = '__all__'
        read_only_fields = ('created_at',)


class ChatSerializer(serializers.ModelSerializer):
    parts = PCPartsSerializer(many=True, read_only = True)
    class Meta:
        model = Chat
        fields = '__all__'
        read_only_fields = ('created_at',)