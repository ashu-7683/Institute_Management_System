# views.py - UPDATE THE search_admission VIEW AND ADD HELPER FUNCTIONS

from django.shortcuts import render, redirect, get_object_or_404 
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.contrib import messages
from .models import *
from .forms import *
from django.db.models import Q, Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
import json
import re

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
@staff_member_required
def register_organization(request):
    if request.method == 'POST':
        # Handle form submission
        org_name = request.POST.get('org_name')
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        regd_no = request.POST.get('regd_no')
        
        # Handle logo upload
        if 'org_logo' in request.FILES:
            logo_file = request.FILES['org_logo']
            
            # Validate file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/svg+xml']
            if logo_file.content_type not in allowed_types:
                messages.error(request, 'Invalid file type. Please upload an image file.')
                return render(request, 'institute/register_organization.html')
            
            # Validate file size (5MB max)
            if logo_file.size > 5 * 1024 * 1024:
                messages.error(request, 'File size exceeds 5MB limit.')
                return render(request, 'institute/register_organization.html')
            
            # Save the file
            # fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'organization_logos'))
            # filename = fs.save(f"{regd_no.replace('/', '_')}_{logo_file.name}", logo_file)
            # logo_url = fs.url(filename)
            
            # Save logo URL to database or process it
            # Your logic here...
        
        # Save other form data to database
        # Your logic here...
        
        messages.success(request, 'Organization registered successfully!')
        return redirect('admin_dashboard')
    
    return render(request, 'institute/register_organization.html')



@login_required
def account_section(request):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    search_query = request.GET.get('search', '')
    admissions = Admission.objects.all()
    
    if search_query:
        admissions = admissions.filter(
            Q(student_name__icontains=search_query) |
            Q(admission_id__icontains=search_query) |
            Q(mobile_number__icontains=search_query)
        )
    
    # Calculate totals for each admission
    admission_data = []
    for admission in admissions:
        total_expenses = Expense.objects.filter(admission=admission).aggregate(Sum('amount'))['amount__sum'] or 0
        total_payments = Payment.objects.filter(admission=admission).aggregate(Sum('amount'))['amount__sum'] or 0
        balance = total_payments - total_expenses
        
        admission_data.append({
            'admission': admission,
            'total_expenses': total_expenses,
            'total_payments': total_payments,
            'balance': balance
        })
    
    context = {
        'admission_data': admission_data,
        'search_query': search_query,
    }
    return render(request, 'institute/account_section.html', context)

@login_required
def student_account(request, admission_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    admission = get_object_or_404(Admission, id=admission_id)
    expenses = Expense.objects.filter(admission=admission).order_by('-date')
    payments = Payment.objects.filter(admission=admission).order_by('-date')
    
    # Calculate totals
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    total_payments = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_payments - total_expenses
    
    # Expenses by category
    expenses_by_category = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    context = {
        'admission': admission,
        'expenses': expenses,
        'payments': payments,
        'total_expenses': total_expenses,
        'total_payments': total_payments,
        'balance': balance,
        'expenses_by_category': expenses_by_category,
    }
    return render(request, 'institute/student_account.html', context)

@login_required
def add_expense(request, admission_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    admission = get_object_or_404(Admission, id=admission_id)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.admission = admission
            expense.added_by = request.user
            expense.save()
            messages.success(request, f'Expense of ₹{expense.amount} added successfully!')
            return redirect('student_account', admission_id=admission_id)
    else:
        form = ExpenseForm()
    
    return render(request, 'institute/add_expense.html', {
        'form': form,
        'admission': admission
    })

@login_required
def add_payment(request, admission_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    admission = get_object_or_404(Admission, id=admission_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.admission = admission
            payment.received_by = request.user
            payment.save()
            messages.success(request, f'Payment of ₹{payment.amount} recorded successfully! Receipt: {payment.receipt_number}')
            return redirect('student_account', admission_id=admission_id)
    else:
        form = PaymentForm()
    
    return render(request, 'institute/add_payment.html', {
        'form': form,
        'admission': admission
    })

@login_required
def edit_expense(request, expense_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense updated successfully!')
            return redirect('student_account', admission_id=expense.admission.id)
    else:
        form = ExpenseForm(instance=expense)
    
    return render(request, 'institute/edit_expense.html', {
        'form': form,
        'expense': expense
    })

@login_required
def edit_payment(request, payment_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated successfully!')
            return redirect('student_account', admission_id=payment.admission.id)
    else:
        form = PaymentForm(instance=payment)
    
    return render(request, 'institute/edit_payment.html', {
        'form': form,
        'payment': payment
    })

@login_required
def delete_expense(request, expense_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Only admins can delete expenses.')
        return redirect('account_section')
    
    if request.method == 'POST':
        expense = get_object_or_404(Expense, id=expense_id)
        admission_id = expense.admission.id
        expense.delete()
        messages.success(request, 'Expense deleted successfully!')
        return redirect('student_account', admission_id=admission_id)
    
    return redirect('account_section')

@login_required
def delete_payment(request, payment_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Only admins can delete payments.')
        return redirect('account_section')
    
    if request.method == 'POST':
        payment = get_object_or_404(Payment, id=payment_id)
        admission_id = payment.admission.id
        payment.delete()
        messages.success(request, 'Payment deleted successfully!')
        return redirect('student_account', admission_id=admission_id)
    
    return redirect('account_section')

@login_required
def generate_receipt(request, payment_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    payment = get_object_or_404(Payment, id=payment_id)
    
    # Create PDF receipt
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Header
    elements.append(Paragraph("THE MOTHER INSTITUTE OF SCIENCE", styles['Title']))
    elements.append(Paragraph("Trilochanpada, Jajpur Town, Near Maa Biraja Temple", styles['Normal']))
    elements.append(Paragraph("Contact: +91 9439387324", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Receipt title
    elements.append(Paragraph("PAYMENT RECEIPT", styles['Heading1']))
    elements.append(Spacer(1, 20))
    
    # Receipt details
    receipt_data = [
        ['Receipt Number:', payment.receipt_number],
        ['Date:', payment.date.strftime('%d/%m/%Y')],
        ['Student Name:', payment.admission.student_name],
        ['Admission ID:', payment.admission.admission_id],
        ['Payment Type:', payment.get_payment_type_display()],
        ['Payment Method:', payment.get_payment_method_display()],
        ['Amount:', f'₹{payment.amount}'],
        ['Description:', payment.description],
        ['Received By:', payment.received_by.username if payment.received_by else ''],
    ]
    
    receipt_table = Table(receipt_data, colWidths=[150, 300])
    receipt_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(receipt_table)
    elements.append(Spacer(1, 30))
    
    # Signature
    elements.append(Paragraph("Authorized Signature", styles['Normal']))
    elements.append(Spacer(1, 50))
    elements.append(Paragraph("_________________________", styles['Normal']))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{payment.receipt_number}.pdf"'
    
    return response

@login_required
def account_report(request, admission_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    admission = get_object_or_404(Admission, id=admission_id)
    expenses = Expense.objects.filter(admission=admission).order_by('date')
    payments = Payment.objects.filter(admission=admission).order_by('date')
    
    # Calculate totals
    total_expenses = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    total_payments = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    balance = total_payments - total_expenses
    
    # Create PDF report
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Header
    elements.append(Paragraph("THE MOTHER INSTITUTE OF SCIENCE", styles['Title']))
    elements.append(Paragraph("Account Statement", styles['Heading1']))
    elements.append(Spacer(1, 20))
    
    # Student Info
    student_info = [
        ['Student Name:', admission.student_name],
        ['Admission ID:', admission.admission_id],
        ['Father\'s Name:', admission.father_name],
        ['Course:', admission.course],
        ['Mobile:', admission.mobile_number],
    ]
    
    info_table = Table(student_info, colWidths=[150, 300])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # Summary
    summary_data = [
        ['Total Expenses:', f'₹{total_expenses}'],
        ['Total Payments:', f'₹{total_payments}'],
        ['Balance:', f'₹{balance}']
    ]
    
    summary_table = Table(summary_data, colWidths=[150, 150])
    summary_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    
    elements.append(Paragraph("Account Summary", styles['Heading2']))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Expenses Table
    elements.append(Paragraph("Expenses Details", styles['Heading2']))
    expenses_data = [['Date', 'Category', 'Description', 'Amount']]
    
    for expense in expenses:
        expenses_data.append([
            expense.date.strftime('%d/%m/%Y'),
            expense.get_category_display(),
            expense.description,
            f'₹{expense.amount}'
        ])
    
    expenses_table = Table(expenses_data, colWidths=[80, 80, 200, 80])
    expenses_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(expenses_table)
    elements.append(Spacer(1, 20))
    
    # Payments Table
    elements.append(Paragraph("Payments Details", styles['Heading2']))
    payments_data = [['Date', 'Type', 'Method', 'Receipt No.', 'Amount']]
    
    for payment in payments:
        payments_data.append([
            payment.date.strftime('%d/%m/%Y'),
            payment.get_payment_type_display(),
            payment.get_payment_method_display(),
            payment.receipt_number,
            f'₹{payment.amount}'
        ])
    
    payments_table = Table(payments_data, colWidths=[80, 80, 80, 80, 80])
    payments_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    
    elements.append(payments_table)
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="account_report_{admission.admission_id}.pdf"'
    
    return response



@login_required
def admin_dashboard(request):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    total_users = CustomUser.objects.exclude(user_type='admin').count()
    total_students = CustomUser.objects.filter(user_type='student').count()
    total_admissions = Admission.objects.count()
    
    # Get admissions with pagination and search
    admissions_list = Admission.objects.all().order_by('-created_at')
    
    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        admissions_list = admissions_list.filter(
            Q(student_name__icontains=search_query) |
            Q(father_name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(adhaar_number__icontains=search_query) |
            Q(college_roll_no__icontains=search_query) |
            Q(admission_id__icontains=search_query)  # ADD THIS LINE
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(admissions_list, 10)  # Show 10 admissions per page
    
    try:
        admissions = paginator.page(page)
    except PageNotAnInteger:
        admissions = paginator.page(1)
    except EmptyPage:
        admissions = paginator.page(paginator.num_pages)
    
    context = {
        'total_users': total_users,
        'total_students': total_students,
        'total_admissions': total_admissions,
        'admissions': admissions,
        'search_query': search_query,
    }
    return render(request, 'institute/admin_dashboard.html', context)

@login_required
def manage_users(request):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    users = CustomUser.objects.all().order_by('id')
    return render(request, 'institute/manage_users.html', {'users': users})

@login_required
def edit_user(request, user_id):
    if request.user.user_type != 'admin':
        return redirect('home')
    
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Update user fields
        user.uid = request.POST.get('uid')
        user.username = request.POST.get('username')
        user.user_type = request.POST.get('user_type')
        user.status = request.POST.get('status')
        
        # Update password only if provided
        password = request.POST.get('password')
        if password and password.strip() != '':
            user.set_password(password)
        
        user.save()
        messages.success(request, f'User {user.username} updated successfully!')
    
    return redirect('manage_users')


# UPDATE THE delete_user FUNCTION IN views.py

@login_required
def delete_user(request, user_id):
    if request.user.user_type != 'admin':
        messages.error(request, 'Only admins can delete users.')
        return redirect('manage_users')
    
    if request.method == 'POST':
        try:
            user = get_object_or_404(CustomUser, id=user_id)
            username = user.username
            
            # Prevent deleting yourself
            if user == request.user:
                messages.error(request, 'You cannot delete your own account!')
                return redirect('manage_users')
            
            # Prevent deleting the last admin
            if user.user_type == 'admin':
                admin_count = CustomUser.objects.filter(user_type='admin').count()
                if admin_count <= 1:
                    messages.error(request, 'Cannot delete the last admin account!')
                    return redirect('manage_users')
            
            user.delete()
            messages.success(request, f'User "{username}" has been deleted successfully!')
            
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
    
    return redirect('manage_users')


def admission_form(request):
    if request.method == 'POST':
        form = AdmissionForm(request.POST, request.FILES)
        if form.is_valid():
            admission = form.save(commit=False)
            # Link to user if they are logged in
            if request.user.is_authenticated:
                admission.submitted_by = request.user
            admission.save()
            messages.success(request, f'Admission form submitted successfully! Admission ID: {admission.admission_id}')
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
    search_type = 'general'  # 'general', 'mobile', or 'admission_id'
    
    # Check if search is mobile number (digits only)
    if search_query:
        search_performed = True
        
        # Check if search is mobile number (10 digits)
        if search_query.isdigit() and len(search_query) == 10:
            search_type = 'mobile'
            admissions = Admission.objects.filter(mobile_number__icontains=search_query)
        # Check if search is admission ID (TMIS followed by numbers)
        elif search_query.upper().startswith('TMIS'):
            search_type = 'admission_id'
            admissions = Admission.objects.filter(admission_id__iexact=search_query.upper())
        else:
            # General search
            admissions = Admission.objects.filter(
                Q(student_name__icontains=search_query) |
                Q(father_name__icontains=search_query) |
                Q(mobile_number__icontains=search_query) |
                Q(adhaar_number__icontains=search_query) |
                Q(admission_id__icontains=search_query.upper())
            )
        
        if admissions.exists():
            # If multiple results, show first one
            admission = admissions.first()
        else:
            messages.warning(request, f"No admission found for: {search_query}")
    
    # Get recent admissions for the table
    recent_admissions = Admission.objects.all().order_by('-created_at')[:10]
    
    # Handle POST request (both create and update)
    if request.method == 'POST':
        admission_id = request.POST.get('admission_id')
        
        if admission_id:
            # UPDATE EXISTING ADMISSION
            try:
                admission = get_object_or_404(Admission, id=admission_id)
                
                # Update all fields from request.POST
                admission.student_name = request.POST.get('student_name', '')
                admission.father_name = request.POST.get('father_name', '')
                admission.mother_name = request.POST.get('mother_name', '')
                
                # Handle date of birth
                dob = request.POST.get('date_of_birth')
                if dob:
                    admission.date_of_birth = dob
                
                admission.mobile_number = request.POST.get('mobile_number', '')
                admission.address = request.POST.get('address', '')
                admission.adhaar_number = request.POST.get('adhaar_number', '')
                admission.whatsapp_number = request.POST.get('whatsapp_number', '')
                admission.blood_group = request.POST.get('blood_group', '')
                admission.category = request.POST.get('category', '')
                
                # College details
                admission.college_name = request.POST.get('college_name', '')
                admission.board_name = request.POST.get('board_name', '')
                admission.college_roll_no = request.POST.get('college_roll_no', '')
                admission.batch = request.POST.get('batch', '')
                admission.eleventh_year = request.POST.get('eleventh_year', '')
                admission.twelfth_year = request.POST.get('twelfth_year', '')
                admission.course = request.POST.get('course', '')
                
                # Visitors
                admission.visitor1_name = request.POST.get('visitor1_name', '')
                admission.visitor1_relation = request.POST.get('visitor1_relation', '')
                admission.visitor1_contact = request.POST.get('visitor1_contact', '')
                admission.visitor2_name = request.POST.get('visitor2_name', '')
                admission.visitor2_relation = request.POST.get('visitor2_relation', '')
                admission.visitor2_contact = request.POST.get('visitor2_contact', '')
                
                # Enrollment
                admission.enrolled_for = request.POST.get('enrolled_for', '')
                admission.sams_login_id = request.POST.get('sams_login_id', '')
                admission.sams_password = request.POST.get('sams_password', '')
                admission.apaar_id = request.POST.get('apaar_id', '')
                
                # Facilities
                hostel_fees = request.POST.get('hostel_fees', '0')
                admission.hostel_fees = float(hostel_fees) if hostel_fees else 0.0
                
                admission.academics_accommodation = request.POST.get('academics_accommodation', '')
                
                # Installments
                installment1 = request.POST.get('installment1', '0')
                installment2 = request.POST.get('installment2', '0')
                installment3 = request.POST.get('installment3', '0')
                installment4 = request.POST.get('installment4', '0')
                installment5 = request.POST.get('installment5', '0')
                installment6 = request.POST.get('installment6', '0')
                
                admission.installment1 = float(installment1) if installment1 else 0.0
                admission.installment2 = float(installment2) if installment2 else 0.0
                admission.installment3 = float(installment3) if installment3 else 0.0
                admission.installment4 = float(installment4) if installment4 else 0.0
                admission.installment5 = float(installment5) if installment5 else 0.0
                admission.installment6 = float(installment6) if installment6 else 0.0
                
                # Fees structure
                tms_fees = request.POST.get('tms_fees', '0')
                college_fees = request.POST.get('admitted_college_fees', '0')
                
                admission.tms_fees = float(tms_fees) if tms_fees else 0.0
                admission.admitted_college_fees = float(college_fees) if college_fees else 0.0
                admission.college_dress = request.POST.get('college_dress', '')
                admission.books = request.POST.get('books', '')
                admission.college_transportation = request.POST.get('college_transportation', '')
                admission.tms_dress = request.POST.get('tms_dress', '')
                
                # Signatures
                admission.guardian_signature = request.POST.get('guardian_signature', '')
                admission.student_signature = request.POST.get('student_signature', '')
                admission.tms_signature = request.POST.get('tms_signature', '')
                
                # Handle image upload
                if 'student_image' in request.FILES:
                    admission.student_image = request.FILES['student_image']
                
                admission.submitted_by = request.user
                admission.save()
                
                messages.success(request, f'Admission {admission.admission_id} for {admission.student_name} updated successfully!')
                return redirect('search_admission')
                
            except Exception as e:
                messages.error(request, f'Error updating admission: {str(e)}')
                # For debugging, you can print the error
                print(f"Update error: {e}")
        else:
            # CREATE NEW ADMISSION
            try:
                admission = Admission()
                
                # Set all fields from request.POST
                admission.student_name = request.POST.get('student_name', '')
                admission.father_name = request.POST.get('father_name', '')
                admission.mother_name = request.POST.get('mother_name', '')
                
                # Handle date of birth
                dob = request.POST.get('date_of_birth')
                if dob:
                    admission.date_of_birth = dob
                
                admission.mobile_number = request.POST.get('mobile_number', '')
                admission.address = request.POST.get('address', '')
                admission.adhaar_number = request.POST.get('adhaar_number', '')
                admission.whatsapp_number = request.POST.get('whatsapp_number', '')
                admission.blood_group = request.POST.get('blood_group', '')
                admission.category = request.POST.get('category', '')
                
                # College details
                admission.college_name = request.POST.get('college_name', '')
                admission.board_name = request.POST.get('board_name', '')
                admission.college_roll_no = request.POST.get('college_roll_no', '')
                admission.batch = request.POST.get('batch', '')
                admission.eleventh_year = request.POST.get('eleventh_year', '')
                admission.twelfth_year = request.POST.get('twelfth_year', '')
                admission.course = request.POST.get('course', '')
                
                # Visitors
                admission.visitor1_name = request.POST.get('visitor1_name', '')
                admission.visitor1_relation = request.POST.get('visitor1_relation', '')
                admission.visitor1_contact = request.POST.get('visitor1_contact', '')
                admission.visitor2_name = request.POST.get('visitor2_name', '')
                admission.visitor2_relation = request.POST.get('visitor2_relation', '')
                admission.visitor2_contact = request.POST.get('visitor2_contact', '')
                
                # Enrollment
                admission.enrolled_for = request.POST.get('enrolled_for', '')
                admission.sams_login_id = request.POST.get('sams_login_id', '')
                admission.sams_password = request.POST.get('sams_password', '')
                admission.apaar_id = request.POST.get('apaar_id', '')
                
                # Facilities
                hostel_fees = request.POST.get('hostel_fees', '0')
                admission.hostel_fees = float(hostel_fees) if hostel_fees else 0.0
                
                admission.academics_accommodation = request.POST.get('academics_accommodation', '')
                
                # Installments
                installment1 = request.POST.get('installment1', '0')
                installment2 = request.POST.get('installment2', '0')
                installment3 = request.POST.get('installment3', '0')
                installment4 = request.POST.get('installment4', '0')
                installment5 = request.POST.get('installment5', '0')
                installment6 = request.POST.get('installment6', '0')
                
                admission.installment1 = float(installment1) if installment1 else 0.0
                admission.installment2 = float(installment2) if installment2 else 0.0
                admission.installment3 = float(installment3) if installment3 else 0.0
                admission.installment4 = float(installment4) if installment4 else 0.0
                admission.installment5 = float(installment5) if installment5 else 0.0
                admission.installment6 = float(installment6) if installment6 else 0.0
                
                # Fees structure
                tms_fees = request.POST.get('tms_fees', '0')
                college_fees = request.POST.get('admitted_college_fees', '0')
                
                admission.tms_fees = float(tms_fees) if tms_fees else 0.0
                admission.admitted_college_fees = float(college_fees) if college_fees else 0.0
                admission.college_dress = request.POST.get('college_dress', '')
                admission.books = request.POST.get('books', '')
                admission.college_transportation = request.POST.get('college_transportation', '')
                admission.tms_dress = request.POST.get('tms_dress', '')
                
                # Signatures
                admission.guardian_signature = request.POST.get('guardian_signature', '')
                admission.student_signature = request.POST.get('student_signature', '')
                admission.tms_signature = request.POST.get('tms_signature', '')
                
                # Handle image upload
                if 'student_image' in request.FILES:
                    admission.student_image = request.FILES['student_image']
                
                admission.submitted_by = request.user
                admission.save()
                
                messages.success(request, f'New admission created successfully! Admission ID: {admission.admission_id}')
                return redirect('search_admission')
                
            except Exception as e:
                messages.error(request, f'Error creating admission: {str(e)}')
                # For debugging, you can print the error
                print(f"Create error: {e}")
    
    # For GET requests, prepare the form
    if admission:
        # If we found an admission from search, pre-fill the form
        form = AdmissionForm(instance=admission)
    else:
        # Otherwise, show empty form
        form = AdmissionForm()
    
    context = {
        'form': form,
        'admission': admission,
        'search_query': search_query,
        'search_performed': search_performed,
        'recent_admissions': recent_admissions,
        'search_type': search_type,
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