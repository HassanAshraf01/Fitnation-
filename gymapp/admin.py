from django.contrib import admin
from .models import ContactMessage
from .models import MemberModels
from .models import Workout

class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'submitted_at')

# Register your models here.
admin.site.register(ContactMessage, ContactMessageAdmin)
class MemberModelAdmin(admin.ModelAdmin):
    list_display=('name', 'email', 'member_Ship_Type','join_date')
admin.site.register(MemberModels, MemberModelAdmin)

@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display=('title', 'muscle_group')