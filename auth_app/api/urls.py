from django.urls import path


from .views import RegistrationAPIView, LoginTokenObtainPairView, AccessTokenRefreshView

urlpatterns = [
    path('login/', LoginTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', AccessTokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegistrationAPIView.as_view(), name='register')
]