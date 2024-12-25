from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings
from .models import CustomUser, UploadedFile, Profile
from .serializers import (
    LoginSerializer, SignUpSerializer, UploadedFileSerializer
)
from itsdangerous import URLSafeTimedSerializer
import os
from rest_framework_simplejwt.tokens import RefreshToken
from .permissions import IsOpsUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.core.signing import Signer, BadSignature
from django.urls import reverse



# URLSafeTimedSerializer for Email Verification
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def generate_verification_token(email, username):
    # Combine email and username in the token payload
    data = {"email": email, "username": username}
    return serializer.dumps(data, salt=settings.SECRET_KEY)

def confirm_verification_token(token):
    try:
        # Load and unpack the token payload
        data = serializer.loads(token, salt=settings.SECRET_KEY, max_age=3600)  # Token valid for 1 hour
        email = data.get("email")
        username = data.get("username")
        return email, username
    except Exception as e:
        print(f"Token validation error: {e}")
        return None, None
    
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Login successful",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SignUpView(APIView):
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = generate_verification_token(user.email,user.username)
            verification_link = f"{request.build_absolute_uri('/api/verify-email/')}?token={token}"
            send_mail(
                "Verify Your Email",
                f"Click the link to verify your email: {verification_link}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
            return Response({"message": "User created. Please verify your email."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    def get(self, request):
        token = request.query_params.get('token')
        email,username = confirm_verification_token(token)
        if not email:
            return Response({"message": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = CustomUser.objects.get(username=username,email=email)
            user.is_active = True
            user.save()
            return Response({"message": "Email verified successfully."})
        except CustomUser.DoesNotExist:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class UploadFileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'ops':
            return Response({"message": "Only Ops Users can upload files."}, status=status.HTTP_403_FORBIDDEN)
        serializer = UploadedFileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(uploaded_by=request.user)
            return Response({"message": "File uploaded successfully."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListFilesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.user_type == 'ops':
            return Response({"message": "Only client Users can view files."}, status=status.HTTP_403_FORBIDDEN)
        files = UploadedFile.objects.filter(is_active=True)
        serializer = UploadedFileSerializer(files, many=True)
        return Response(serializer.data)
    
    
class GenerateDownloadLink(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, uuid):
        if request.user.user_type == 'ops':
            return Response({"message": "Only client Users can GenerateDownloadLink."}, status=status.HTTP_403_FORBIDDEN)
        try:
            file = UploadedFile.objects.get(uuid=uuid, is_active=True)
            
            # Encrypt the assignment ID using Django's signing module
            signer = Signer()
            signed_url = signer.sign(uuid)  # Signed URL to be used for downloading
            
            # Construct the download URL
            download_link = request.build_absolute_uri(f"/api/download-file/{signed_url}/")
            
            return Response({
                "download-link": download_link,
                "message": "success"
            }, status=status.HTTP_200_OK)
        
        except UploadedFile.DoesNotExist:
            return Response({"message": "File not found."}, status=status.HTTP_404_NOT_FOUND)
        

class DownloadFileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, signed_url):
        if request.user.user_type == 'ops':
            return Response({"message": "Only client Users can DownloadFileView."}, status=status.HTTP_403_FORBIDDEN)
        try:
            # Verify the signed URL
            signer = Signer()
            assignment_id = signer.unsign(signed_url)  # Unsigned to get the original ID
            
            # Retrieve the file object based on the assignment ID
            file = UploadedFile.objects.get(uuid=assignment_id, is_active=True)

            # Increment download count
            file.download_count += 1
            file.save()

            # Get the file's absolute path
            file_path = file.file.path

            # Ensure the file exists
            if not os.path.exists(file_path):
                return Response({"message": "File not found."}, status=status.HTTP_404_NOT_FOUND)

            # Serve the file as an attachment
            response = HttpResponse(
                open(file_path, 'rb').read(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        
        except (UploadedFile.DoesNotExist, BadSignature):
            return Response({"message": "Invalid or expired download link."}, status=status.HTTP_400_BAD_REQUEST)