from django.urls import path
from . import views

urlpatterns = [
    path('submit-response/', views.submit_response, name='submit-response'), 
    path('get-leaderboard/', views.get_leaderboard_data, name='get_leaderboard')
]
