from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns=[
    path('',views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('register/', views.register_member, name='register_member'),
    path('signup/',views.signup_view,name='signup'),
    path('fpassword/', auth_views.PasswordResetView.as_view(
        template_name='gymapp/fpassword.html',
        email_template_name='gymapp/password_reset_email.html',
        success_url='/fpassword/done/'
    ), name='fpassword'),
    path('fpassword/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='gymapp/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='gymapp/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='gymapp/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('login/',auth_views.LoginView.as_view(template_name='gymapp/login.html'),name='login'),
    path('logout/',auth_views.LogoutView.as_view(next_page='home'),name='logout'),
    path('workout/', views.workout, name='workout'),
    path('api/save-profile/', views.save_profile, name='api_save_profile'),
    path('choose-workout/', views.choose_workout, name='choose_workout'),
    path('api/generate-plan/', views.api_generate_plan, name='api_generate_plan'),
    path('my-plans/', views.my_plans, name='my_plans'),
] 