from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer, TokenSerializer
)
from .models import ApplicationUser


# Create your views here.
def say_hello(request):
    return HttpResponse("Hello, world!")


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        operation_id='auth_register',
        summary='Register a new user',
        description='Create a new user account with email and password',
        request=UserRegistrationSerializer,
        responses={
            201: OpenApiResponse(
                response=TokenSerializer,
                description='User successfully registered and logged in'
            ),
            400: OpenApiResponse(description='Bad request - validation errors')
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    @extend_schema(
        operation_id='auth_login',
        summary='Login user',
        description='Authenticate user and return JWT tokens',
        request=UserLoginSerializer,
        responses={
            200: OpenApiResponse(
                response=TokenSerializer,
                description='User successfully authenticated'
            ),
            400: OpenApiResponse(description='Bad request - invalid credentials')
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        operation_id='auth_logout',
        summary='Logout user',
        description='Blacklist the refresh token to logout user',
        request={'refresh': 'string'},
        responses={
            200: OpenApiResponse(description='Successfully logged out'),
            400: OpenApiResponse(description='Bad request - invalid token')
        },
        tags=['Authentication']
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        operation_id='auth_profile',
        summary='Get user profile',
        description='Get the current authenticated user profile',
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description='User profile data'
            ),
            401: OpenApiResponse(description='Unauthorized')
        },
        tags=['Authentication']
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @extend_schema(
        operation_id='auth_profile_update',
        summary='Update user profile',
        description='Update the current authenticated user profile',
        request=UserProfileSerializer,
        responses={
            200: OpenApiResponse(
                response=UserProfileSerializer,
                description='User profile updated successfully'
            ),
            400: OpenApiResponse(description='Bad request - validation errors'),
            401: OpenApiResponse(description='Unauthorized')
        },
        tags=['Authentication']
    )
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenRefreshView(TokenRefreshView):
    @extend_schema(
        operation_id='auth_token_refresh',
        summary='Refresh access token',
        description='Get a new access token using refresh token',
        tags=['Authentication']
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


