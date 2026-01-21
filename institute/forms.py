from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import * 

class UserRegistrationForm(UserCreationForm):
    user_type = forms.ChoiceField(choices=CustomUser.USER_TYPE_CHOICES, required=True)
    uid = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'password1', 'password2', 'uid', 'user_type']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remove help text ONLY for username field
        self.fields['username'].help_text = ''
        
        # Remove help text from uid field if you want
        self.fields['uid'].help_text = ''
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.uid = self.cleaned_data['uid']
        user.user_type = self.cleaned_data['user_type']
        if commit:
            user.save()
        return user

class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    


class AdmissionForm(forms.ModelForm):
    class Meta:
        model = Admission
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'academics_accommodation': forms.Textarea(attrs={'rows': 3}),
            'student_image': forms.FileInput(attrs={'accept': 'image/*'}),
            'admission_id': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
        }
        
        
class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'category', 'description', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['date', 'payment_method', 'payment_type', 'description', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }