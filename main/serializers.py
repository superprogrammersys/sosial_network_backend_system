from rest_framework import serializers
from .models import User,Post,Call,Comment,Message,Settings
class UserSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True)
    class Meta:
        model=User
        fields=['id','username','email','password','first_name','last_name','bio','profile_picture']
    def create(self, validated_data):
        user=User.objects.create_user(
            validated_data['username'],
            validated_data['email'],
            validated_data['password'],
        )
        return user
class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model=Post
        fields=['id','user','content','image','created_at']
        read_only_fields=['user','created_at']
    def create(self, validated_data):
        post=Post.objects.create(validated_data)
        return post
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Comment
        fields=['id','Post','user_comment','content','created_at']
class CallSerializer(serializers.ModelSerializer):
    class Meta:
        model=Call
        fields=['encoming_calls','outgoing_calls','created_at','is_active']
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model=Message
        fields=['id','sent_messages','received_messages','content','created_at','is_read']
class SettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Settings
        fields=['is_profile_public']