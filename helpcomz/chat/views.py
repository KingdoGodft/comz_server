# Create your views here.
from dataclasses import dataclass
from re import M
import os
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
        
        # 유효성 검사 
        if chat_serializer.is_valid():
            # DB에 저장
            chat_serializer.save() 
            # 응답 생성 및 DB 저장
            self.create_answer(chat_serializer.data)
            # 지금까지 사용자가 입력했던 질문/응답 전체 리턴
            user_id = chat_serializer.data.get("user_id")
            chat_serializer = ChatSerializer(Chat.objects.filter(user_id=user_id), many=True)
            return Response(chat_serializer.data, status=status.HTTP_201_CREATED)
            # 생성된 
            # return Response(chat_serializer.data, status = status.HTTP_201_CREATED)
        else:
            return Response(chat_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    """
    create response and insert it to DB
    parameter:
        data: ChatSerializer
    """
    def create_answer(self, chat_data):
        # chat_data에서 user_id 가져옴
        user_id = chat_data.get("user_id")
        content = chat_data.get("content")

        # dialogflow로 답변 생성
        project_id = "comz-chat"
        session_id = "user_id"
        fulfillment_text = self.detect_intent_texts(project_id, session_id, [content], "ko-KR")

        # 답변 생성
        response_data = {
            "user_id": user_id,
            "chat_type":"answer",
            "content" : fulfillment_text,
        }

        # 답변 DB에 저장
        response_chat_serializer = ChatSerializer(data = response_data)
        if response_chat_serializer.is_valid():
            response_chat_serializer.save() 
            pass
        else:
            print(response_chat_serializer.errors)
            
    """
    google cloud api tutorial for dialogflow 
    https://cloud.google.com/dialogflow/es/docs/quick/api#detect-intent-text-drest
    """
    def detect_intent_texts(self, project_id, session_id, texts, language_code):
        """Returns the result of detect intent with texts as inputs.

        Using the same `session_id` between requests allows continuation
        of the conversation."""
        from google.cloud import dialogflow

        session_client = dialogflow.SessionsClient()

        session = session_client.session_path(project_id, session_id)
        print("Session path: {}\n".format(session))

        for text in texts:
            text_input = dialogflow.TextInput(text=text, language_code=language_code)

            query_input = dialogflow.QueryInput(text=text_input)

            response = session_client.detect_intent(
                request={"session": session, "query_input": query_input}
            )

            print("=" * 20)
            print("Query text: {}".format(response.query_result.query_text))
            print(
                "Detected intent: {} (confidence: {})\n".format(
                    response.query_result.intent.display_name,
                    response.query_result.intent_detection_confidence,
                )
            )
            print("Fulfillment text: {}\n".format(response.query_result.fulfillment_text))

            return response.query_result.fulfillment_text