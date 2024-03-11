from django.contrib import admin
from . models import User
from . models import MasterData,Shift,test



# Register your models here.
admin.site.register(User)
admin.site.register(MasterData)
admin.site.register(Shift)
admin.site.register(test)

