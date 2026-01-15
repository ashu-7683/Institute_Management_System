from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Admission

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'uid', 'user_type', 'status', 'is_active')
    list_filter = ('user_type', 'status', 'is_active')
    search_fields = ('username', 'email', 'uid', 'mobile')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'uid', 'mobile')}),
        ('Type and Status', {'fields': ('user_type',  'status')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

class AdmissionAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'father_name', 'mobile_number', 'enrolled_for', 'created_at')
    list_filter = ('enrolled_for', 'batch', 'created_at')
    search_fields = ('student_name', 'father_name', 'mobile_number', 'adhaar_number')
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Admission, AdmissionAdmin)