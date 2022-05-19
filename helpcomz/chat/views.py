# Create your views here.
from dataclasses import dataclass
from re import M
import os
import sys 
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from venv import create
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserID, Chat
from .serializers import UserIDSerializer, ChatSerializer, PCPartsSerializer
from rest_framework import status
import string
from .algorithm import algorithm
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
            response_count = self.create_answer(chat_serializer.data)
            # 생성된 응답 리턴
            user_id = chat_serializer.data.get("user_id")
            chat_queryset = Chat.objects.filter(user_id=user_id).order_by('-id')[:response_count][::-1]
            chat_serializer = ChatSerializer(chat_queryset, many=True)
            return Response(chat_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(chat_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    """
    create answer response and insert it to DB
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
        
        dialogflow_response =  self.detect_intent_texts(project_id, session_id, [content], "ko-KR")


        
        fulfillment_messages = dialogflow_response.query_result.fulfillment_messages
        is_finished = dialogflow_response.query_result.all_required_params_present
        is_intent_ask_pc = dialogflow_response.query_result.intent.display_name == "ask_pc_game"
        output_contexts =  dialogflow_response.query_result.parameters

        # https://stackoverflow.com/questions/71256960/how-to-access-infos-in-protobuf-response-from-dialogflow-api
        # cannot extract parameters directly. convert it to json
        from google.protobuf.json_format import MessageToDict
        dialogflow_response_dict = MessageToDict(dialogflow_response._pb)
        if is_intent_ask_pc:
            parameters =  dialogflow_response_dict['queryResult']['parameters']
        else:
            parameters = {}

        # 리턴되는 메시지 리스트 각각에 대해 답변 생성
        for idx, text in enumerate(fulfillment_messages):
            answer_text = text.text.text[0]
            
            # 마지막 답변 (사용자에게 재시작을 묻는 경우) 확인
            is_last_answer = is_finished and idx == len(fulfillment_messages) -1  and is_intent_ask_pc
            
            # 챗봇에서 모든 정보가 수집되었을 경우 마지막 답변 형식을 parts로 지정
            chat_type = "answer"
            if is_last_answer:
                chat_type = "parts"

            # 답변 생성
            response_data = {
                "user_id": user_id,
                "chat_type":chat_type,
                "content" : answer_text,
                "parameters" : parameters
            }

            # 답변 저장
            response_chat_serializer = ChatSerializer(data = response_data)
            if response_chat_serializer.is_valid():
                response_chat_serializer.save() 
                pass
            else:
                print(response_chat_serializer.errors)

            # 모든 정보가 수집되었을 경우 PC 부품 리스트 생성
            if is_last_answer:
                self.create_parts(response_chat_serializer.data, parameters )
        
        # 총 답변 개수 리턴
        return len(fulfillment_messages)
            
    """
    google cloud api for dialogflow 
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
            #print("Fulfillment text: {}\n".format(response.query_result.fulfillment_text))
            #print("fulfillment_messages: {}\n".format(response.query_result.fulfillment_messages))

            return response

    '''
    create parts response and insert it to DB
    parameter:
        data: ChatSerializer
    '''
    def create_parts(self, chat_data, parameter):
        # chat_data에서 chat_id 가져옴
        chat_id = chat_data.get("id")

        alg = algorithm()

        computer = alg.run(parameter["pc_budget"],parameter["pc_games"],parameter["pc_game_quality"])

        if computer is None:

            # 부품 더미데이터
            pc_parts_info = [
                {
                "part_type" : "cpu",
                "part_name" : "인텔 코어i7-12세대 12700K (엘더레이크)",
                "price" : "533960",
                "shop_link" : "http://prod.danawa.com/info/?pcode=15594638&cate=112747",
                "thumbnail" : "http://img.danawa.com/prod_img/500000/638/594/img/15594638_1.jpg?shrink=130:130",
                },
                {
                "part_type" : "gpu",
                "part_name" : "갤럭시 GALAX 지포스 RTX 3060 V2 D6 12GB ",
                "price" : "539720",
                "shop_link" : "http://prod.danawa.com/info/?pcode=14448719&cate=112753",
                "thumbnail" : "http://img.danawa.com/prod_img/500000/719/448/img/14448719_1.jpg?shrink=130:130",
                },
                {
                "part_type" : "mainboard",
                "part_name" : "ASUS PRIME B660M-K D4 인텍앤컴퍼니",
                "price" : "159510",
                "shop_link" : "http://prod.danawa.com/info/?pcode=16084070&cate=11341244",
                "thumbnail" : "http://img.danawa.com/prod_img/500000/070/084/img/16084070_1.jpg?shrink=130:130",
                },
                {
                "part_type" : "ram",
                "part_name" : "삼성전자 DDR4-3200",
                "price" : "147080",
                "shop_link" : "http://prod.danawa.com/info/?pcode=11541857&cate=112752",
                "thumbnail" : "http://img.danawa.com/prod_img/500000/857/541/img/11541857_1.jpg?shrink=130:130&_v=20211119130530",
                },
                {
                "part_type" : "powersupply",
                "part_name" : "마이크로닉스 Classic II 풀체인지 600W 80PLUS 230V EU",
                "price" : "57000",
                "shop_link" : "http://prod.danawa.com/info/?pcode=14677028&cate=112777",
                "thumbnail" : "http://img.danawa.com/prod_img/500000/028/677/img/14677028_1.jpg?shrink=130:130",
                },
                {
                "part_type" : "disk",
                "part_name" : "Seagate 파이어쿠다 530 M.2 NVMe (1TB)",
                "price" : "229000",
                "shop_link" : "http://prod.danawa.com/info/?pcode=14803520&cate=112760#",
                "thumbnail" : "http://img.danawa.com/prod_img/500000/520/803/img/14803520_1.jpg?shrink=130:130",
                },
                {
                "part_type" : "case",
                "part_name" : "앱코 NCORE G30 트루포스 (블랙)",
                "price" : "38900",
                "shop_link" : "http://prod.danawa.com/info/?pcode=14705840&cate=112775",
                "thumbnail" : "http://img.danawa.com/prod_img/500000/840/705/img/14705840_1.jpg?shrink=130:130",
                },
            ]
        else:
            print("Computer is not None")
            print(computer["data"])
            pc_parts_info = computer["data"]

        # PC 부품 정보 입력
        for pc_part_info in pc_parts_info:
            pc_part_info['chat_id'] = chat_id
            pc_part_serializer = PCPartsSerializer(data = pc_part_info)
            if(pc_part_serializer.is_valid()):
                pc_part_serializer.save()
            else:
                print(pc_part_serializer.errors)
