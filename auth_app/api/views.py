from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import RegistrationSerializer

class RegistrationAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        data = {}
        if serializer.is_valid():
            saved_account = serializer.save()
            data = {
                'detail': "User created successfully!"
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class LoginTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        access = response.data.get('access', None)
        refresh = response.data.get('refresh', None)

        response.set_cookie(
            key='access_token',
            value=access,
            httponly=True,
            secure=True,
            samesite='Lax'
        )

        response.set_cookie(
            key='refresh_token',
            value=refresh,
            httponly=True,
            secure=True,
            samesite='Lax'
        )

        user = User.objects.get(username=request.data.get('username'))

        response.data = {
            'detail': "Login successfully!",
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }

        return response
    

class AccessTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')

        if refresh_token is None:
            return Response(
                {'detail': 'Refresh token not provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data={'refresh': refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response(
                {'detail': 'Invalid refresh token.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        access_token = serializer.validated_data.get('access')

        response = Response({'detail': "Token refreshed", 'access': access_token}, status=status.HTTP_200_OK)

        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,
            samesite='Lax'
        )

        return response