from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CustomUser, Admission
from .forms import UserRegistrationForm, AdmissionForm, UserLoginForm
from django.db.models import Q

def home(request):
    return render(request, 'institute/index.html')

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.user_type == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('home')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = UserLoginForm()
    return render(request, 'institute/login.html', {'form': form})

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        # In a real application, you would send a password reset email here
        messages.success(request, 'Password reset link has been sent to your email')
        return redirect('login')
    return render(request, 'institute/forgot_password.html')

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required
def admin_dashboard(request):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    total_users = CustomUser.objects.exclude(user_type='admin').count()
    total_students = CustomUser.objects.filter(user_type='student').count()
    total_admissions = Admission.objects.count()
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_admissions': total_admissions,
    }
    return render(request, 'institute/admin_dashboard.html', context)

@login_required
def manage_users(request):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    users = CustomUser.objects.all().order_by('id')
    return render(request, 'institute/manage_users.html', {'users': users})

def admission_form(request):
    if request.method == 'POST':
        form = AdmissionForm(request.POST)
        if form.is_valid():
            admission = form.save(commit=False)
            # Link to user if they are logged in
            if request.user.is_authenticated:
                admission.submitted_by = request.user
            admission.save()
            messages.success(request, 'Admission form submitted successfully!')
            return redirect('admission_form')
    else:
        form = AdmissionForm()
    
    return render(request, 'institute/admission_form.html', {'form': form})

@login_required
def search_admission(request):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    search_query = request.GET.get('search', '')
    admission = None
    search_performed = False
    
    if search_query:
        search_performed = True
        # Search by student name, mobile, or admission ID
        admissions = Admission.objects.filter(
            Q(student_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(father_name__icontains=search_query) |
            Q(adhaar_number__icontains=search_query)
        )
        
        if admissions.exists():
            # If multiple results, show first one
            admission = admissions.first()
        else:
            messages.warning(request, f"No admission found for: {search_query}")
    
    if request.method == 'POST':
        # Handle form update
        admission_id = request.POST.get('admission_id')
        if admission_id:
            admission = get_object_or_404(Admission, id=admission_id)
            form = AdmissionForm(request.POST, instance=admission)
            if form.is_valid():
                form.save()
                messages.success(request, 'Admission updated successfully!')
                return redirect('search_admission')
        else:
            # Create new admission
            form = AdmissionForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'New admission created successfully!')
                return redirect('search_admission')
    else:
        # If we have an admission from search, pre-fill the form
        if admission:
            form = AdmissionForm(instance=admission)
        else:
            form = AdmissionForm()
    
    context = {
        'form': form,
        'admission': admission,
        'search_query': search_query,
        'search_performed': search_performed,
    }
    return render(request, 'institute/search_admission.html', context)


def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'User registered successfully!')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'institute/register.html', {'form': form})