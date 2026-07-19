from django.db import models
from django.contrib.auth.models import User

class Workout(models.Model):
    MUSCLE_GROUP = [
        ('chest', 'Chest'),
        ('back', 'Back'),
        ('legs', 'Legs'),
        ('shoulders', 'Shoulders'),
        ('arms', 'Arms'),
        ('abs', 'Abs'),
    ]
    title = models.CharField(max_length=100)
    muscle_group = models.CharField(max_length=20, choices= MUSCLE_GROUP)
    video_file = models.FileField(upload_to='gymapp/videos/', null=True, blank=True)
    thumbnail_file= models.ImageField(upload_to='gymapp/thumbnails/', null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title
class ContactMessage(models.Model):
    name=models.CharField(max_length=100)
    message=models.TextField()
    submitted_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"
class MemberModels(models.Model):
    Membership_Choices=[
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Yearly','Yearly')
    ] 
    name= models.CharField(max_length=100)
    email=models.EmailField()
    age=models.PositiveIntegerField()
    phone=models.CharField(max_length=15)   
    member_Ship_Type=models.CharField(max_length=20 , choices=Membership_Choices)
    join_date=models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.member_Ship_Type})"

class UserProfile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    weight = models.FloatField()
    height = models.FloatField()
    gender = models.CharField(max_length=20)
    goal = models.CharField(max_length=50) # Fat Loss, weight gain, Weight maintanence
    experience = models.CharField(max_length=50) # beginner, intermediate, advanced
    workout_place = models.CharField(max_length=50) # Gym, home
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.name} - {self.goal}"


class GeneratedPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    plan_data = models.TextField() # Stored JSON representation of the fitness plan
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Plan for {self.user.username} - {self.profile.goal} ({self.created_at})"


