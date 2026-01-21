# models.py - COMPLETE UPDATED FILE
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('user', 'User'),
        ('student', 'Student'),
    )
    
    uid = models.CharField(max_length=50, unique=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    status = models.CharField(max_length=20, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} - {self.user_type}"

class Admission(models.Model):
    # Custom Admission ID Field
    admission_id = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="Admission ID")
    
    # Student Image Field
    student_image = models.ImageField(upload_to='student_images/', blank=True, null=True, verbose_name="Student Photo")
    
    student_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    mobile_number = models.CharField(max_length=15)
    address = models.TextField()
    adhaar_number = models.CharField(max_length=20)
    whatsapp_number = models.CharField(max_length=15)
    blood_group = models.CharField(max_length=5)
    category = models.CharField(max_length=50)
    
    # College details
    college_name = models.CharField(max_length=200)
    board_name = models.CharField(max_length=100)
    college_roll_no = models.CharField(max_length=50)
    batch = models.CharField(max_length=50)
    eleventh_year = models.CharField(max_length=10)
    twelfth_year = models.CharField(max_length=10)
    course = models.CharField(max_length=100)
    
    # Enrollment
    enrolled_for = models.CharField(max_length=100)
    sams_login_id = models.CharField(max_length=100, blank=True)
    sams_password = models.CharField(max_length=100, blank=True)
    pen_number = models.CharField(max_length=100, blank=True)
    apaar_id = models.CharField(max_length=100, blank=True)
    
    # Visitors
    visitor1_name = models.CharField(max_length=100, blank=True)
    visitor1_relation = models.CharField(max_length=100, blank=True)
    visitor1_contact = models.CharField(max_length=15, blank=True)
    visitor2_name = models.CharField(max_length=100, blank=True)
    visitor2_relation = models.CharField(max_length=100, blank=True)
    visitor2_contact = models.CharField(max_length=15, blank=True)
    
    # Fees and facilities
    hostel_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    academics_accommodation = models.TextField(blank=True)
    admitted_college_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    college_dress = models.CharField(max_length=100, blank=True)
    books = models.CharField(max_length=100, blank=True)
    college_transportation = models.CharField(max_length=100, blank=True)
    tms_dress = models.CharField(max_length=100, blank=True)
    
    # Installments
    installment1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    installment2 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    installment3 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    installment4 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    installment5 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    installment6 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    tms_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Signatures (in real app, these would be FileFields)
    guardian_signature = models.CharField(max_length=100, blank=True)
    student_signature = models.CharField(max_length=100, blank=True)
    tms_signature = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Generate custom admission ID if not already set
        if not self.admission_id:
            # Get the last admission to determine next number
            last_admission = Admission.objects.order_by('-id').first()
            if last_admission and last_admission.admission_id:
                try:
                    # Extract number from existing ID
                    last_number = int(last_admission.admission_id[4:])  # Extract after "TMIS"
                    next_number = last_number + 1
                except:
                    next_number = 1
            else:
                next_number = 1
            
            # Format: TMIS0001, TMIS0002, etc.
            self.admission_id = f"TMIS{next_number:04d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        admission_id_display = self.admission_id if self.admission_id else f"ID:{self.id}"
        return f"{admission_id_display} - {self.student_name} - {self.enrolled_for}"
    
    
    
class Expense(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='expenses')
    date=models.DateField()
    category = models.CharField(max_length=100, choices =[
        ('food', 'Fooding'),
        ('transport', 'Transportation'),
        ('hostel', 'Hostel Fee'),
        ('academic', 'Academic Material'),
        ('other', 'Other'),
    ])
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    added_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.admission.admission_id} - {self.category} - ₹{self.amount}"


class Payment(models.Model):
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='payments')
    date = models.DateField()
    payment_method = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('cheque', 'Cheque'),
        ('online', 'Online Transfer'),
        ('card', 'Card')
    ])
    payment_type = models.CharField(max_length=50, choices=[
        ('tuition', 'Tuition Fee'),
        ('hostel', 'Hostel Fee'),
        ('transport', 'Transportation'),
        ('library', 'Library'),
        ('other', 'Other')
    ])
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True, null=True)
    received_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Generate receipt number if not provided
        if not self.receipt_number:
            # Get the last payment to determine next number
            last_payment = Payment.objects.order_by('-id').first()
            if last_payment and last_payment.receipt_number:
                try:
                    # Extract number from existing receipt number
                    last_number = int(last_payment.receipt_number[5:])  # Extract after "RECPT"
                    next_number = last_number + 1
                except:
                    next_number = 1
            else:
                next_number = 1
            
            # Format: RECPT0001, RECPT0002, etc.
            self.receipt_number = f"RECPT{next_number:04d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.admission.admission_id} - ₹{self.amount} - {self.payment_type}"