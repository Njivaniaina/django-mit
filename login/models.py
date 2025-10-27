from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
    username = models.CharField(max_length=100, unique=True, blank=False)
    email = models.EmailField(blank=False)
    password = models.CharField(max_length=255, blank=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    image = models.ImageField(upload_to="users/", null=True, blank=False)
    embedding = models.JSONField(null=True, blank=True)

    # Encrypte the pass word
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    # Check the pass word
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.username

class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    username = models.CharField(max_length=150)  # utile même si User supprimé
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    mac_address = models.CharField(max_length=17, null=True, blank=True)  # format: AA:BB:CC:DD:EE:FF
    login_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=[("success", "Success"), ("failed", "Failed"), ("logout", "Logout")],
        default="failed"
    )

    def __str__(self):
        return f"{self.username} - {self.status} - {self.login_time}"

class Activity(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="activities/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="activities")

    def __str__(self):
        return self.title
