from django.test import TestCase
from django.urls import reverse
from .models import Admission

class AdmissionModelTest(TestCase):
    def test_admission_creation(self):
        admission = Admission.objects.create(
            student_name="Test Student",
            email="test@example.com",
            phone="1234567890",
            course="Test Course",
            admission_id="TEST001"
        )
        self.assertEqual(admission.student_name, "Test Student")
        self.assertEqual(admission.admission_id, "TEST001")

class ViewTest(TestCase):
    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
