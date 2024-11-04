from rest_framework import generics, filters, permissions, exceptions, response, status
from .models import User, Call, Post, Comment, Message, Settings
from . import socket_handler
from .serializers import UserSerializer, PostSerializer, CallSerializer, CommentSerializer, MessageSerializer, SettingsSerializer
import json
import asyncio

#create your Views here.

class UserAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
class UserCreationAPIView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
#class LoginAPIView(generics)
class PostAPIView(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    def get(self, request, post_id=None, *args, **kwargs):
        if post_id:
            try:
                p = Post.objects.get(post_id=post_id)
                serializer = self.get_serializer(p)
                return response.Response(serializer.data, status.HTTP_200_OK)
            except Post.DoesNotExist:
                return response.Response({'detail': 'The requested post was not found'}, status.HTTP_404_NOT_FOUND)
class PostCreationAPIView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class CommentAPIView(generics.ListAPIView):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
class CommentCreationAPIView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise exceptions.NotFound('The post was not found')
        serializer.save(user=self.request.user, post=post)

class MessageAPIView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(receiver=user).select_related('sender', 'receiver').order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

class TextMessageView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    async def send_message(self, message, sender, receiver):
        async with socket_handler.websockets.connect('ws://localhost:5000') as ws:
            await ws.send(json.dumps({
                'type': 'message',
                'message': message,
                'sender': sender.username,
                'receiver': receiver.username
            }))
            msg = Message(sender=sender, receiver=receiver, content=message)
            msg.save()
    def post(self, request, *args, **kwargs):
        message = request.data.get('message')
        receiver_username = request.data.get('receiver')
        if not message or not receiver_username:
            return response.Response({'error': 'Message and receiver must be provided'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            db_sender = request.user
            db_receiver = User.objects.get(username=receiver_username)
        except User.DoesNotExist:
            return response.Response({'error': 'The requested user was not found'}, status=status.HTTP_404_NOT_FOUND)
        asyncio.create_task(self.send_message(message, db_sender, db_receiver))
        return response.Response({'status': 'Message sent', 'receiver': receiver_username}, status=status.HTTP_201_CREATED)
class CallOfferAPIView(generics.CreateAPIView):
    permission_classes=[permissions.IsAuthenticated]
    serializer_class=CallSerializer
    def get_queryset(self):
        return Call.objects.filter(self.request.user).order_by('created_at')
    async def initiate_call(self, caller,receiver):
        async with socket_handler.websockets.connect('ws://localhost:5000/'+self.request.user.id) as ws:
            await ws.send(json.dumps({
                'type':'offer',
                'caller':caller.username,
                'receiver':receiver.username
            }))
    def post(self, request, *args, **kwargs):
        receiver_username = request.data.get('receiver')
        if not receiver_username:
            return response.Response({'error': 'Receiver must be provided'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            db_caller = request.user
            db_receiver = User.objects.get(username=receiver_username)
        except User.DoesNotExist:
            return response.Response({'error': 'The requested user was not found'}, status=status.HTTP_404_NOT_FOUND)
        asyncio.create_task(self.initiate_call(db_caller, db_receiver))
        return response.Response({'status': 'Call initiated', 'receiver': receiver_username}, status=status.HTTP_201_CREATED)
class CallAnswerAPIView(generics.CreateAPIView):
    serializer_class=CallSerializer
    permission_classes=[permissions.IsAuthenticated]
    async def answer_call(self,user,caller,sdp):
        async with socket_handler.websockets.connect('ws://localhost:5000/'+self.request.user.id) as ws:
            await ws.send(json.dumps({
                'type':'answer',
                'caller':caller.username,
                'receiver':user.username,
                'sdp':sdp
            }))
    def post(self, request, *args, **kwargs):
        caller_username = request.data.get('caller')
        sdp = request.data.get('sdp')
        
        if not caller_username or not sdp:
            return response.Response({'error': 'Caller and SDP must be provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            db_user = request.user
            db_caller = User.objects.get(username=caller_username)
        except User.DoesNotExist:
            return response.Response({'error': 'The requested user was not found'}, status=status.HTTP_404_NOT_FOUND)

        asyncio.create_task(self.answer_call(db_user, db_caller, sdp))
        return response.Response({'status': 'Call answered', 'caller': caller_username}, status=status.HTTP_201_CREATED)
class IceCandidateAPIView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    async def send_candidate(self, user_id, candidate):
        async with socket_handler.websockets.connect(f'ws://localhost:5000/{user_id}') as ws:
            await ws.send(json.dumps({
                'type': 'candidate',
                'candidate': candidate
            }))
    def post(self, request, *args, **kwargs):
        candidate = request.data.get('candidate')
        if not candidate:
            return response.Response({'error': 'Candidate data must be provided'}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.user.id  # أو استخدم أي معرف مستخدم آخر حسب الحاجة
        asyncio.create_task(self.send_candidate(user_id, candidate))
        return response.Response({'status': 'ICE candidate sent'}, status=status.HTTP_201_CREATED)