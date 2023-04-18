from django.db import models
from authentication import models as auth_model

class Category(models.Model):
    name = models.CharField(max_length=100)

    
class Room(models.Model):
    title = models.CharField(max_length=100)
    main_picture_path = models.CharField(max_length=255)
    room_type = models.PositiveSmallIntegerField(default=0)
    is_premium = models.PositiveSmallIntegerField(default=0)
    link = models.TextField()
    password = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    maximum_member_count = models.PositiveSmallIntegerField(default=10)
    open_status = models.PositiveSmallIntegerField(default=1)
    members = models.ManyToManyField(auth_model.User , through="Membership")
    categories = models.ManyToManyField(Category)
    


class Membership(models.Model):
    member = models.ForeignKey(auth_model.User , on_delete=models.CASCADE)
    room = models.ForeignKey(Room , on_delete=models.CASCADE)
    is_owner = models.BooleanField(default=False)  
    is_member = models.BooleanField(default=False)
    is_requested = models.BooleanField(default=False)
    ## 0 for pending , 1 for rejected , 2 for accepted , 3 for admin
    request_status = models.PositiveSmallIntegerField(default=0) 

class BriefPlan(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    picture = models.CharField(max_length=255)
    room = models.ForeignKey(Room , on_delete=models.CASCADE)

class Task(models.Model):
    title = models.CharField(max_length=100)
    priority = models.PositiveSmallIntegerField(default=0)
    room = models.ForeignKey(Room, on_delete=models.CASCADE , related_name='tasks')
    user = models.ForeignKey(auth_model.User , on_delete=models.CASCADE , related_name='tasks') 
    description = models.TextField(default="")