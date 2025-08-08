from django.db import models

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
# Create your models here.
