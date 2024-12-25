from django.urls import path
from .views import SignUpView, LoginView, VerifyEmailView,UploadFileView,ListFilesView,DownloadFileView,GenerateDownloadLink

from rest_framework_swagger.views import get_swagger_view

schema_view = get_swagger_view(title='Pastebin API')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('upload/', UploadFileView.as_view(), name='upload-file'),
    path('files/', ListFilesView.as_view(), name='list-files'),
    # path('files/<uuid:uuid>/download/', DownloadFileView.as_view(), name='download-file'),
    path('files/<uuid:uuid>/download/', GenerateDownloadLink.as_view(), name='download-file'),
    path('download-file/<str:signed_url>/', DownloadFileView.as_view(), name='download-file'),
    # path('swagger/', schema_view.with_ui('swagger',cache_timeout=0), name='schema-swagger-ui'),
]

