from django.db import models
import uuid
import os
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USER_TYPES = (
        ('ops', 'Ops User'),
        ('client', 'Client User'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='client')

class UploadedFile(models.Model):
    ALLOWED_EXTENSIONS = ['pptx', 'docx', 'xlsx']

    name = models.CharField(max_length=255)
    upload_date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='documents/')
    file_extension = models.CharField(max_length=10, blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='documents')
    is_active = models.BooleanField(default=True)
    size = models.PositiveIntegerField(blank=True, null=True, help_text="Size of the file in bytes.")
    download_count = models.PositiveIntegerField(default=0, help_text="Number of times the file has been downloaded.")

    def clean(self):
        if self.file:
            self.file_extension = os.path.splitext(self.file.name)[-1][1:].lower()
            if self.file_extension not in self.ALLOWED_EXTENSIONS:
                raise ValidationError(f"Invalid file extension: {self.file_extension}. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}")

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure clean is called for validation
        self.size = self.file.size if self.file else None
        super().save(*args, **kwargs)

class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    verification_token = models.CharField(max_length=50, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
