from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.register_user, name='register'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage-users/', views.manage_users, name='manage_users'),
    path('admission-form/', views.admission_form, name='admission_form'),
    path('search-admission/', views.search_admission, name='search_admission'),
]