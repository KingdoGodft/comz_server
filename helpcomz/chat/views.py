# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import viewsets
from .serializers import PostSerializer
from .models import Post
from rest_framework import permissions

def hello(request):
    return HttpResponse("<h1>Hello, world!</h1>")

    
class PostView(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (permissions.IsAuthenticated,)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)