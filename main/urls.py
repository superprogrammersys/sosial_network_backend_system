from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.UserAPIView.as_view(), name='users'),
    path('users/create/', views.UserCreationAPIView.as_view(), name='create_user'),
    path('posts/', views.PostAPIView.as_view(), name='posts'),
    path('posts/<int:post_id>/', views.PostAPIView.as_view(), name='post_detail'),
    path('call/offer/', views.CallOfferAPIView.as_view(), name='offer'),
    path('call/answer/', views.CallAnswerAPIView.as_view(), name='answer_call'),
    path('call/ic_candidate/', views.IceCandidateAPIView.as_view(), name='ice_candidate'),
]
