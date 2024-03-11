from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone



class User(AbstractUser):
    is_admin = models.BooleanField('is_admin',default=False)
    is_client = models.BooleanField('is_client',default=False)
    is_operator = models.BooleanField('is_operator',default=False)
    


class MasterData(models.Model):
    PartNumber = models.CharField(max_length=255)
    # MultiFactor = models.FloatField()
    GreaterLess = models.CharField(max_length=10)
    Setpoint = models.IntegerField()
    Value = models.FloatField()
    
class Shift(models.Model):
    Shift_name = models.CharField(max_length=255)
    Shift_From = models.TimeField(max_length=8)
    Shift_To = models.TimeField()

class MyPLCLog(models.Model):
    prodstatus = models.BooleanField()
    selected_part = models.CharField(max_length=255,null=True, default="")

    
    class Meta:
        db_table = 'myplclog'


class Result_tbl(models.Model):
    BatchCounter = models.IntegerField()
    PartNumber = models.CharField(max_length=255)
    Filter_Values = models.FloatField(max_length=255)
    FilterNo = models.CharField(max_length=255)
    result = models.CharField(max_length=255)
    Shift = models.CharField(max_length=50,null=True,default="")

class test(models.Model):
    PartNumber = models.CharField(max_length=255, null=True, default="")
    BatchCounter = models.IntegerField()
    FilterNo = models.CharField(max_length=255)
    Filter_Values = models.FloatField()

class Show_report(models.Model):
    BatchCounter = models.IntegerField()
    PartNumber = models.CharField(max_length=255)
    FilterNo = models.CharField(max_length=255)
    result = models.CharField(max_length=255)
    Shift = models.CharField(max_length=50,null=True,default="")
    Highest_value = models.CharField(max_length=100, default="")










    

      
    
        
    
    
