from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.urls import reverse
from .models import ContactMessage
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import MemberForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.mail import send_mail,BadHeaderError
from .forms import CustomUserCreationForm
from django.core.exceptions import ValidationError
def home(request):
    return render(request, 'gymapp/home.html')
def about(request):
    return render(request, 'gymapp/about.html')
def contact(request):
    if request.method =='POST':
        name=request.POST.get('name')
        message = request.POST.get('message')
        
        ContactMessage.objects.create(name=name, message=message)
        print(f"Name: {name}, Message: {message}")
        messages.success(request, "Form submission successful ✅")
        return HttpResponseRedirect(reverse('contact'))
    return render(request, 'gymapp/contact.html')
def signup_view(request):
    if request.method=='POST':
        form= CustomUserCreationForm(request.POST)
        if form.is_valid():
            
            email= form.cleaned_data.get('email')

            if User.objects.filter(email=email, is_superuser=True).exists():
                messages.error(request,"This email is reserved and cannot be used.")
                return render(request, 'gymapp/signup.html',{'form':form})
            user=form.save()
            print("User email ",user.email)
            try:
                send_mail(
                    subject= 'Account Created Successfully!',
                    message= 'Welcome! Your account has been created successfully.',
                    from_email= 'Fitnation <hassu003.lko@gmail.com>',
                    recipient_list=[user.email],
                    fail_silently=False,
                )
            except BadHeaderError:
                return HttpResponse('Invalid Header found')
            except Exception as e:
                print("Email sending failed ", e)  
            messages.success(request, "Form submission successful ✅, Redirecting to home page ..........")          
            return render(request,'gymapp/signup.html',{'form': CustomUserCreationForm(),'redirect':True})
    else:
        form=CustomUserCreationForm()
    return render(request, 'gymapp/signup.html',{'form':form})
@login_required
def register_member(request):
    if request.method=='POST':
        form =MemberForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member registration successful! ✅')
            return HttpResponseRedirect(reverse('register_member'))
    else:
        form =MemberForm()
    return render(request, 'gymapp/register_member.html',{'form':form})            
    
    
# Create your views here.
                