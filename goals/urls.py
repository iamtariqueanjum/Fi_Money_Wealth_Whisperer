from django.urls import path
from . import views

urlpatterns = [
    path('<str:username>/goals/', views.goal_list, name='goal_list'),
    path('<str:username>/goals/create/', views.goal_create, name='goal_create'),
    path('<str:username>/goals/<int:goal_id>/edit/', views.goal_update, name='goal_update'),
    path('<str:username>/goals/<int:goal_id>/delete/', views.goal_delete, name='goal_delete'),
    path('<str:username>/generate-context/', views.generate_context, name='generate_context'),
    path('<str:username>/generate-recommendations/', views.generate_recommendations, name='generate_recommendations'),
] 