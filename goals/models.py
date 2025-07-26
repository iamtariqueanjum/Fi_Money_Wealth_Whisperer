from django.db import models
from users.models import User

# Create your models here.

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    goal = models.TextField()
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    primary_goal = models.CharField(max_length=100, null=True, blank=True)
    primary_goal_details = models.TextField(null=True, blank=True)
    secondary_goals = models.TextField(null=True, blank=True)  # Comma-separated
    secondary_goal_timeline = models.CharField(max_length=100, null=True, blank=True)
    risk_comfort = models.CharField(max_length=50, null=True, blank=True)
    investment_horizon = models.CharField(max_length=50, null=True, blank=True)
    major_life_events = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.goal[:30]}"
