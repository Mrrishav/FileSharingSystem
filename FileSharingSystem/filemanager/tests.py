from django.test import TestCase

# Create your tests here.
from django.core.mail import send_mail

send_mail('Test Email','This is a test email sent using python-dotenv.','choubeyrishav08@gmail.com',['rishabhchoubey70@gmail.com'],fail_silently=False,)