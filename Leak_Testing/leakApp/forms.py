from django import forms
from django.contrib.auth.forms import UserCreationForm
from . models import User
from .models import MasterData
from .models import Shift
from datetime import time


# leak project authentication system
class LoginForm(forms.Form):
    username = forms.CharField(
        widget= forms.TextInput(
           attrs={
               "class":'form-contr'
           } 
        )
    )
    password = forms.CharField(
        widget= forms.PasswordInput(
           attrs={
               "class":'form-contr'
           } 
        )
    )
    
class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    password2 = forms.CharField(
        label='Password confirmation',
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = User
        fields = ('is_admin', 'is_client', 'is_operator','username', 'password1' )
        labels = {
            'is_admin': 'TeamAT',
            'is_client': 'Admin',
            'is_operator': 'Users',
            'username': 'Username',
            
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username already exists. Please choose a different one.')
        return username

#  admin master  
class MasterDataForm(forms.ModelForm):
    class Meta:
        model = MasterData
        fields = '__all__'  # You can specify fields explicitly if needed


# class AddMasterDataForm(forms.ModelForm):
#     class Meta:
#         model = MasterData
#         fields = ['PartNumber',  'GreaterLess', 'Setpoint', 'Value']
#         labels = {
#             'PartNumber': 'Part Number',
#             # 'MultiFactor': 'MultiFactor',
#             'GreaterLess': 'Greater/Less',
#             'Setpoint': 'Setpoint',
#             'Value': 'Value',
#         }
       
   

class ClientMasterDataForm(forms.ModelForm):
    class Meta:
        model = MasterData
        fields = ['PartNumber',  'GreaterLess', 'Setpoint', 'Value']
        labels = {
            'PartNumber': 'Part Number',
            # 'MultiFactor': 'MultiFactor',
            'GreaterLess': 'Greater/Less',
            'Setpoint': 'Setpoint',
            'Value': 'Value',
        }

    def __init__(self, *args, **kwargs):
        super(ClientMasterDataForm, self).__init__(*args, **kwargs)

        # Set the fields as not required for the client
        # self.fields['MultiFactor'].required = False
        self.fields['GreaterLess'].required = False
        self.fields['Setpoint'].required = False
        self.fields['Value'].required = False

        # Set default values for these fields
        # self.fields['MultiFactor'].initial = 0.5
        self.fields['GreaterLess'].initial = 'Greater'
        self.fields['Setpoint'].initial = 18
        self.fields['Value'].initial = 1



# admin shift 
class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['Shift_name', 'Shift_From', 'Shift_To']
        widgets = {
            'Shift_From': forms.TimeInput(attrs={'type': 'time'}),
            'Shift_To': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        from_time = cleaned_data.get('Shift_From')
        to_time = cleaned_data.get('Shift_To')

        original_from_time = self.instance.Shift_From if self.instance else None
        original_to_time = self.instance.Shift_To if self.instance else None

        if (from_time != original_from_time or to_time != original_to_time) and from_time > to_time:
            to_time = time(23, 59, 59)  # Handle the case where a shift continues into the next day

        # If shift times have changed, perform validation
        if from_time != original_from_time or to_time != original_to_time:
            shifts = Shift.objects.all()
            for shift in shifts:
                if (
                    (shift.Shift_From <= from_time <= shift.Shift_To) or
                    (shift.Shift_From <= to_time <= shift.Shift_To) or
                    (from_time <= shift.Shift_From <= to_time)
                ):
                    if self.instance.pk != shift.pk:
                        raise forms.ValidationError('Shift time overlaps with an existing shift.')

        return cleaned_data
        

class MyPLCLogForm(forms.Form):
    prodstatus = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))


class ReportForm(forms.Form):
    PartNumber = forms.CharField(max_length=255) 
    Shift_name = forms.CharField(max_length=255)
    date_to = forms.DateField(label='Date To')
    date_from = forms.DateField(label='Date From')