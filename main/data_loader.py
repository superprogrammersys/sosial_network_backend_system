from .models import *
class Data:
    def __init__(self):
        self.users=[]
        self.calls=[]
        self.posts=[]
        self.messages=[]
        self.load_users()
        self.load_posts()
        self.load_calls()
        self.load_messages()
    def load_users(self):
        self.users=list(User.objects.all())
    def save_users(self):
        count=0
        for user in self.users:
            user.save()
            count+=1
        return f'there {count} users has been saved'
    def save_user(self,user):
        for query in self.users:
            if user==query:
                user.save()
            print('user saved')
            return
        return None
    def find_user(self,name=None,id=None,email=None):
        for user in self.users:
            if (id is not None and user.id == id) or            (email is not None and user.email == email) or (name is not None and user.name == name):
                return user
        return None
    def add_user(self,*args,**kwargs):
        user=User.objects.create_user(*args,**kwargs)
        self.users.append(user)
        return True
    def remove_user(self,user):
        if user in self.users:
            user.delete()
            self.users.remove(user)
            return True
        return False
    def load_calls(self):
        self.calls=list(Call.objects.all())
        return True
    def load_posts(self):
        self.posts=list(Post.objects.all())
        return True