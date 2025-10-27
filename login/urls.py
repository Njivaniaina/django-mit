from django.urls import path
from . import views

urlpatterns = [
    path('' , views.home, name="home" ),
    path('login/' , views.login_views, name="login" ),
    path('sign_in/' , views.sign_in_views, name="sign_in" ),
    path('user_list/', views.user_list, name="user_list"),
    path('user_delete/<int:id>', views.user_delete, name="user_delete"),
    path('user_active/<int:id>', views.user_active, name="user_active"),
    path('logout/', views.logout, name="logout"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('user_modify/', views.user_modify, name="user_modify"),
    path('user_log/', views.user_log, name="user_log"),
    path('create_activity/', views.create_activity, name="create_activity"),
    path('activity_delete/<int:id>', views.activity_delete, name="activity_delete"),
    path('activity_list/', views.activity_list, name="activity_list"),
    path('activity_list_all/', views.activity_list_all, name="activity_list_all"),
]
