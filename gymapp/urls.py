from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns=[
    path('',views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('register/', views.register_member, name='register_member'),
    path('signup/',views.signup_view,name='signup'),
    path('login/',auth_views.LoginView.as_view(template_name='gymapp/login.html'),name='login'),
] 