from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import FeedbackForm, FeedbackQuestion, FeedbackResponse

class Feed360ModelTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(username='hod', password='test')
        self.form = FeedbackForm.objects.create(title='Test Form', created_by=self.user, department='CSE', year=3, section='A')

    def test_model_creation(self):
        self.assertEqual(FeedbackForm.objects.count(), 1)
        q = FeedbackQuestion.objects.create(form=self.form, text='How was the class?', answer_type='stars')
        self.assertEqual(FeedbackQuestion.objects.count(), 1)

    def test_student_submission_saves(self):
        # Minimal test, assumes Student/Staff exist
        from core.models import Student, Staff
        student = Student.objects.create(name='Test Student', roll='123', department='CSE', year=3, section='A')
        staff = Staff.objects.create(name='Test Staff', department='CSE')
        q = FeedbackQuestion.objects.create(form=self.form, text='How was the class?', answer_type='stars')
        resp = FeedbackResponse.objects.create(form=self.form, question=q, student=student, staff=staff, rating=4)
        self.assertEqual(FeedbackResponse.objects.count(), 1)
