from django.utils import timezone
from django.db import models
from django.contrib.auth.models import (PermissionsMixin , AbstractBaseUser ,  UserManager)

class MyUserManager(UserManager):
    def create_user(self, email, username, first_name, last_name, password, **extra_fields):
        if not email:
           raise ValueError('Email must be provided')
        
        email = self.normalize_email(email)
        user = self.model(email=email , username=username , first_name=first_name , last_name = last_name , **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email,username, first_name, last_name, password, **extra_fields):
        user = self.create_user(
            email,
            first_name=first_name,
            last_name=last_name,
            username=username,
            password=password,
            is_superuser=True,
            **extra_fields
        )
        user.is_admin = True
        user.save(using=self._db)
        return user
    
    
class User(AbstractBaseUser , PermissionsMixin):
    username = models.CharField(max_length=150 , blank=False , unique=True)
    first_name = models.CharField(max_length=150, blank=False)
    last_name = models.CharField(max_length=150, blank=False )
    email = models.EmailField(blank=False , unique=True)
    picture_path  = models.CharField(max_length=255 , blank=True)
    usertype = models.PositiveSmallIntegerField(default=0)
    bio = models.TextField(blank=True)
    date_joined = models.DateTimeField(default=timezone.now)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    

    objects = MyUserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username" ,"first_name" , "last_name"]