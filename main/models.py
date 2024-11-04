from django.db import models
from django.contrib.auth.models import AbstractUser
from taggit.managers import TaggableManager
# Create your models here.
class User(AbstractUser):
    bio=models.TextField(blank=True,null=True)
    profile_picture=models.ImageField(upload_to='profile_pictures/',blank=True,null=True)
class Call(models.Model):
    caller=models.ForeignKey(User,related_name='outgoing_calls',on_delete=models.CASCADE)
    receiver=models.ForeignKey(User,related_name='incoming_calls',on_delete=models.CASCADE)
    created_at=models.DateTimeField(auto_now_add=True)
    is_active=models.BooleanField(default=True)
    def __str__(self):
        return f'call from {self.caller} to {self.receiver}'
class Post(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    content=models.TextField()
    tags=TaggableManager()
    image=models.ImageField(upload_to='posts/',blank=True,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.content
class Comment(models.Model):
    post=models.ForeignKey(Post,on_delete=models.CASCADE,related_name='comments')
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='User_comment')
    content=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
class Message(models.Model):
    sender=models.ForeignKey(User,related_name='sent_messages',on_delete=models.CASCADE)
    receiver=models.ForeignKey(User,related_name='received_messages',on_delete=models.CASCADE)
    content=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    is_read=models.BooleanField(default=False)
class Settings(models.Model):
    user=models.OneToOneField(User,related_name='settings',on_delete=models.CASCADE)
    is_profile_public=models.BooleanField(default=True)