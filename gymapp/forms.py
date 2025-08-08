from django import forms
from .models import MemberModels
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class MemberForm(forms.ModelForm):
    class Meta:
        model =MemberModels
        fields =['name', 'email','age', 'phone','member_Ship_Type']
class CustomUserCreationForm(UserCreationForm):
    email= forms.EmailField(required=True)        

    class Meta:
        model =User
        fields= ['username', 'email','password1', 'password2']
    