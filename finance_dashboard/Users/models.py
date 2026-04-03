from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
 
class Role(models.TextChoices):
    VIEWER   = 'viewer',   'Viewer'
    ANALYST  = 'analyst',  'Analyst'
    ADMIN    = 'admin',    'Admin'
 
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
 
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', Role.ADMIN)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not password:
            raise ValueError("Superusers must have a password.")
        return self.create_user(email, password, **extra_fields)
 
 
class User(AbstractBaseUser, PermissionsMixin):
    """
    Authentication is email-based.
    Role drives all permission checks across the system.
    """
    email      = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    role       = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
 
    objects = UserManager()
 
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
 
    class Meta:
        ordering = ['-date_joined']
 
    def __str__(self):
        return f'{self.full_name} <{self.email}> [{self.role}]'
 
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()
 
    @property
    def is_admin(self):
        return self.role == Role.ADMIN
 
    @property
    def is_analyst(self):
        return self.role in (Role.ANALYST, Role.ADMIN)
 
    @property
    def is_viewer(self):
        return True  # every role can view
 