# Create your views here.
from dataclasses import dataclass
from re import M
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserID, Chat
from .serializers import UserIDSerializer, ChatSerializer
from rest_framework import status
import string
import random


class UserIDView(APIView):
    """
    GET
    """
    def get(self, request):
        # generate random string or length 64 which is user ID
        _LENGTH = 64
        string_pool = string.ascii_letters + string.digits
        user_id = ""
        for i in range(_LENGTH):
            user_id += random.choice(string_pool)

        # Serialize
        user_id_serializer = UserIDSerializer(data = {"user_id":user_id})
        if user_id_serializer.is_valid():
            return Response(user_id_serializer.data, status=200)
        else:
            return Response(user_id_serializer.errors, status=503)



class ChatView(APIView):
    """
    GET chat list  
    request parameters: {"userID": userID}

    """
    def get(self, request):
        user_id = request.GET.get('user_id',None)
        print(user_id)
        if user_id is None:
            chat_queryset = Chat.objects.all() # 모든 채팅 리스트 불러옴
            chat_queryset_serializer = ChatSerializer(chat_queryset, many = True)
            return Response(chat_queryset_serializer.data, status=status.HTTP_200_OK)
        else:
            chat_serializer = ChatSerializer(Chat.objects.filter(user_id=user_id), many=True) # 특정 ID의 사용자가 채팅한 리스트를 가져온다
            return Response(chat_serializer.data, status=status.HTTP_200_OK)

    """
    POST
    request parameters:: {"userID": userID, "content": content}
    """
    def post(self, request):
        data = request.data
        chat_serializer = ChatSerializer(data = request.data)
        
        # 유효성 검사 후 DB에 저장
        if chat_serializer.is_valid():
            chat_serializer.save() 
            return Response(chat_serializer.data, status = status.HTTP_201_CREATED)
        else:
            return Response(chat_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
