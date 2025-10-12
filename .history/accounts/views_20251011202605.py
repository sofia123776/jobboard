from django.shortcuts import render, redirect
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout  # Import specific functions
from django.contrib import messages
from django.contrib.auth.decorators import login_required  # For decorators

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'accounts/login.html')

def register(request):
    if request.method == 'POST':
        # Get form data - use lowercase field names
        username = request.POST['username']
        email = request.POST['email']  # lowercase 'email', not 'Email'
        password = request.POST['password']  # 'password', not 'Email'
        password2 = request.POST['password2']  # if you have password confirmation
        
        # Check if passwords match
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return redirect('register')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken')
            return redirect('register')
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already registered')
            return redirect('register')
        
        # Create user
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')  # or wherever you want to redirect
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('register')
    
    else:
        return render(request, 'accounts/register.html')

def logout_view(request):
    auth.logout(request)
    return redirect('home')
