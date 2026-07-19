from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.core.mail import send_mail,BadHeaderError
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
import json

from .models import ContactMessage, Workout, UserProfile
from .forms import CustomUserCreationForm, MemberForm
from .services.gemini_service import GeminiService
from .services.youtube_service import YouTubeService
def home(request):
    plan_exists = False
    if request.user.is_authenticated:
        from .models import GeneratedPlan
        plan_exists = GeneratedPlan.objects.filter(user=request.user).exists()
    return render(request, 'gymapp/home.html', {'plan_exists': plan_exists})
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
@login_required
def workout(request):
    return redirect('register_member')
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
                from django.core.mail import get_connection
                smtp_conn = get_connection('django.core.mail.backends.smtp.EmailBackend')
                send_mail(
                    subject= 'Account Created Successfully!',
                    message= 'Welcome! Your account has been created successfully.',
                    from_email= 'Fitnation <hassu003.lko@gmail.com>',
                    recipient_list=[user.email],
                    fail_silently=False,
                    connection=smtp_conn,
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
    from .models import GeneratedPlan
    plan_exists = GeneratedPlan.objects.filter(user=request.user).exists()
    return render(request, 'gymapp/register_member.html', {'plan_exists': plan_exists})            
    

@csrf_exempt
@login_required
def save_profile(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            profile = UserProfile.objects.create(
                user=request.user,
                name=data.get('name'),
                age=int(data.get('age')),
                weight=float(data.get('weight')),
                height=float(data.get('height')),
                gender=data.get('gender'),
                goal=data.get('goal'),
                experience=data.get('experience'),
                workout_place=data.get('workout_place')
            )
            return JsonResponse({'status': 'success', 'profile_id': profile.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@login_required
def choose_workout(request):
    profile_id = request.GET.get('profile_id')
    return render(request, 'gymapp/choose_workout.html', {'profile_id': profile_id})


@csrf_exempt
@login_required
def api_generate_plan(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            profile_id = data.get('profile_id')
            categories = data.get('categories', [])
            
            if not profile_id:
                return JsonResponse({'status': 'error', 'message': 'Missing profile_id'}, status=400)
            if not categories:
                return JsonResponse({'status': 'error', 'message': 'At least one workout category must be selected'}, status=400)
                
            try:
                profile = UserProfile.objects.get(id=profile_id)
            except UserProfile.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'UserProfile does not exist'}, status=404)
            
            # 1. Get plan from Gemini Service
            gemini_plan = GeminiService.generate_fitness_plan(profile, categories)
            
            # 2. Extract exercise names to query YouTube
            exercises = []
            for cat in ["weight_training", "cardio", "yoga"]:
                if cat in gemini_plan:
                    cat_data = gemini_plan[cat]
                    if isinstance(cat_data, dict):
                        for day, items in cat_data.items():
                            if isinstance(items, list):
                                for item in items:
                                    ex_name = item.get("exercise")
                                    if ex_name:
                                        exercises.append(ex_name)
            
            # 3. Search and get YouTube videos
            videos_map = YouTubeService.get_exercise_videos(exercises)
            
            # 4. Merge YouTube video links back into gemini_plan
            for cat in ["weight_training", "cardio", "yoga"]:
                if cat in gemini_plan:
                    cat_data = gemini_plan[cat]
                    if isinstance(cat_data, dict):
                        for day, items in cat_data.items():
                            if isinstance(items, list):
                                for item in items:
                                    ex_name = item.get("exercise")
                                    if ex_name:
                                        ex_key = ex_name.lower()
                                        if ex_key in videos_map:
                                            item["video"] = videos_map[ex_key]
                                            
            # 5. Save generated plan to database
            from .models import GeneratedPlan
            GeneratedPlan.objects.filter(user=request.user).delete()
            GeneratedPlan.objects.create(
                user=request.user,
                profile=profile,
                plan_data=json.dumps(gemini_plan)
            )
                                            
            return JsonResponse(gemini_plan)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)


@login_required
def my_plans(request):
    from .models import GeneratedPlan
    plan = GeneratedPlan.objects.filter(user=request.user).order_by('-created_at').first()
    show = request.GET.get('show', 'all')
    
    plan_exists = False
    plan_json = "{}"
    if plan:
        plan_exists = True
        plan_json = plan.plan_data
        
    return render(request, 'gymapp/my_plans.html', {
        'plan_exists': plan_exists,
        'plan_json': plan_json,
        'show': show
    })
                