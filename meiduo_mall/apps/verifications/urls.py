from django.urls import path
from apps.verifications import views

urlpatterns = [
    path('image_codes/<uuid:uuid>/', views.ImageCodeView.as_view()),
    path('sms_codes/<mobile:mobile>/', views.SmsCodeView.as_view()),
]
