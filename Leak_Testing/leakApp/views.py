from django.shortcuts import render,redirect,get_object_or_404,HttpResponse
from . forms import CustomUserCreationForm,LoginForm
from django.contrib.auth import authenticate,login,logout
from .models import MasterData , Shift,Result_tbl
from .forms import MasterDataForm , ShiftForm,ClientMasterDataForm,ReportForm
from django.db.models import Q
from django.utils.timezone import make_aware 
from datetime import time, datetime, timedelta
from django.core.exceptions import ValidationError
from .forms import MyPLCLogForm
from .models import MyPLCLog
from .models import test
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.db.models.functions import ExtractMonth, ExtractYear
from datetime import datetime
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Value, IntegerField
from django.db.models.functions import Cast
from django.db.models import Max, F
from django.http import JsonResponse
from .models import test, Result_tbl,Show_report
from django.db import connections
from datetime import date

def register(request):
    msg = None
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            msg = 'User created'
            # Log the user in after registration
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
            return redirect('login_view')
        else:
            msg = 'Form is not valid'
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form, 'msg': msg})
           
def login_view(request):
    form = LoginForm(request.POST or None)
    msg = None
    
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_admin:
                    login(request, user)
                    return redirect('adminpage')
                elif user.is_client:
                    login(request, user)
                    return redirect('client')
                elif user.is_operator:
                    login(request, user)
                    return redirect('operator')
            else:
                msg = 'Invalid credentials'
        else:
            msg = 'Error validating form'
    
    return render(request, 'login.html', {'form': form, 'msg': msg})

def  admin(request):
    return render(request,'admin_master_template.html')       

def  client(request):
    return render(request,'client_master_template.html')       

def  operator(request):
    return render(request,'operator_test_template.html')      


# Admin Master page Views

def admin_master(request):
    data = MasterData.objects.all().order_by('-id')
    form = MasterDataForm()

    if request.method == 'POST':
        form = MasterDataForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_master')

    return render(request, 'admin_master_template.html', {'form': form, 'data': data})
    
    return render(request, 'admin_master_template.html', {'form': form, 'data': data})

def admin_edit_record(request, pk):
    record = get_object_or_404(MasterData, pk=pk)

    if request.method == 'POST':
        form = MasterDataForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('admin_master')
    else:
        form = MasterDataForm(instance=record)
    
    return render(request, 'admin_master_template.html', {'form': form, 'record': record})
        
def admin_delete_record(request, pk):
    record = get_object_or_404(MasterData, pk=pk)
    record.delete()
    return redirect('admin_master')




# Admin test page views.

def get_current_shift():
    now = datetime.now().time()
    current_date = date.today()

    # Retrieve current shift
    current_shift = Shift.objects.filter(Shift_From__lte=now, Shift_To__gte=now).first()

    if current_shift:
        shift_start = datetime.combine(current_date, current_shift.Shift_From)
        shift_end = datetime.combine(current_date, current_shift.Shift_To)

        # Raw SQL query to get max BatchCounter within shift timeframe
        query = f"SELECT MAX(BatchCounter) FROM leakapp_result_tbl WHERE Date_Field BETWEEN '{shift_start}' AND '{shift_end}' AND FilterNo = 'AI{{filter_no}}'"

        with connection.cursor() as cursor:
            cursor.execute(query)
            max_batch_counter = cursor.fetchone()[0]

        return max_batch_counter if max_batch_counter else 0

    return None  # Shift not found for the current time

def reset_batch_counter():
    current_batch_counter = get_current_shift()

    if current_batch_counter is not None:
        current_date = date.today()
        current_shift = Shift.objects.filter(Shift_From__lte=datetime.now().time(), Shift_To__gte=datetime.now().time()).first()

        if current_shift:
            shift_start = datetime.combine(current_date, current_shift.Shift_From)
            shift_end = datetime.combine(current_date, current_shift.Shift_To)

            # Raw SQL query to reset BatchCounter in leakapp_test within shift timeframe
            reset_query = f"UPDATE leakapp_test SET BatchCounter = 0 WHERE Date_Field BETWEEN '{shift_start}' AND '{shift_end}'"

            with connection.cursor() as cursor:
                cursor.execute(reset_query)

def update_batch_result_highest():
    reset_batch_counter()

    # Retrieve the highest Filter_Values
    highest_filter_value = test.objects.aggregate(highest_value=Max('Filter_Values'))['highest_value']

    # Filter items based on the condition
    items_to_update = test.objects.filter(Filter_Values__gt=0, Filter_Values__lt=1)

    initial_filter_values = {}

    for item in items_to_update:
        # Check if the filter number exists in the dictionary
        if item.FilterNo not in initial_filter_values:
            initial_filter_values[item.FilterNo] = item.Filter_Values
            item.BatchCounter += 1
            item.save()
        else:
            # Check if the initial value for this filter is between 0 and 1
            initial_value = initial_filter_values.get(item.FilterNo)
            if initial_value and 0 < initial_value < 1:
                # Check if the current value falls within the range and is different from the initial value
                if 0 < item.Filter_Values < 1 and item.Filter_Values != initial_value:
                    # Increment BatchCounter
                    item.BatchCounter += 1
                    item.save()

    return JsonResponse({'message': 'Data updated and inserted successfully.'})

def admin_test(request):
    myplclog = MyPLCLog.objects.first()
    parts_in_production = MyPLCLog.objects.filter(prodstatus=True)

    message = ""
    form = MyPLCLogForm(initial={'prodstatus': myplclog.prodstatus if myplclog else False})

    # Fetch data for test_screen
    filter_data = test.objects.all()

    new_filter_values = None  # Default value for the updated filter value

    if request.method == 'POST':
        action = request.POST.get('action')

        if parts_in_production and action == 'start':
            message = "Production for another part is in progress. Cannot start a new one."
        else:
            selected_part = request.POST.get('partNumber')
            if myplclog is not None:
                if action == 'start':
                    # insert_highest_values(request) 
                    myplclog.prodstatus = True
                    myplclog.selected_part = selected_part
                    myplclog.save()
                    return redirect('admin_test')
                    
                elif action == 'stop':
                    myplclog.prodstatus = False
                    myplclog.selected_part = ""
                    myplclog.save()
                    return redirect('admin_test')

                # Update filter value directly in the template
                new_filter_values = {}  # Define dictionary for new filter values
                for filter_item in filter_data:
                    # Logic to fetch updated filter value for each filter item
                    new_value = test.objects.get(FilterNo=filter_item.FilterNo).Filter_Values
                    new_filter_values[filter_item.FilterNo] = new_value
            else:
                if action == 'start':
                    MyPLCLog.objects.create(
                        prodstatus=True,
                        selected_part=selected_part,
                    )
                elif action == 'stop':
                    MyPLCLog.objects.create(
                        prodstatus=False,
                        selected_part=""
                    )
                message = f"Selected part number '{selected_part}' {action}ed."

    part_numbers = MasterData.objects.values_list('PartNumber', flat=True).distinct()

    selected_part = myplclog.selected_part if myplclog else None
     
    # update_batch_result_highest()
    # distinct_batch_counters = get_distinct_batch_counters()
    # highest_values = get_highest_filter_values(distinct_batch_counters)

    return render(request, 'admin_test_template.html', {
        'form': form,
        'part_numbers': part_numbers,
        'message': message,
        'selected_part': selected_part,
        'Filter': filter_data,  # Pass the data from test_screen to the template
        'new_filter_values': new_filter_values,
          # Pass the updated filter values to the template
    })

def ShowDetails(request):
    filter_data = test.objects.all()
    update_batch_result_highest()
    new_filter_values = {}
    
    for filter_item in filter_data:
        # Logic to fetch and update the filter value for each filter item
        new_value = test.objects.get(FilterNo=filter_item.FilterNo).Filter_Values
        new_filter_values[filter_item.FilterNo] = new_value


    return JsonResponse(new_filter_values)

def get_setpoint(request):
    setpoint_value = MasterData.objects.values_list('Setpoint', flat=True).first()
    return JsonResponse({'setpoint': setpoint_value})

@csrf_exempt
def update_result(request):
    if request.method == 'POST':
        batch_counter = request.POST.get('BatchCounter')
        result_value = request.POST.get('result')

        # Check if the record already exists in Result_tbl
        existing_record = Result_tbl.objects.filter(BatchCounter=batch_counter).exists()

        # If the record doesn't exist, insert a new record in Result_tbl
        if not existing_record:
            Result_tbl.objects.create(BatchCounter=batch_counter, result=result_value)
            return JsonResponse({'message': 'Result inserted successfully.'})
        else:
            # Update the existing record with the new result value
            record = Result_tbl.objects.get(BatchCounter=batch_counter)
            record.result = result_value
            record.save()
            return JsonResponse({'message': 'Result updated successfully.'})

    return JsonResponse({'message': 'Invalid request method.'})
    



# def get_last_5_nok_filters(request):
#     # Fetch the last 5 NOK filters from the 'test' model
#     nok_filters = test.objects.filter(Filter_Values__gt=18).order_by('-id')[:5]

#     # Create a dictionary to hold the filter details
#     nok_filters_data = {}
#     for filter_item in nok_filters:
#         nok_filters_data[filter_item.FilterNo] = {
#             'Filter_Values': filter_item.Filter_Values,
            
#             # Add other details you need from the 'test' model
#             # Example: 'Other_Detail': filter_item.Other_Detail,
#         }

#     return JsonResponse(nok_filters_data)





# Adimin Shift page views.

def admin_shift(request):
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_shift')
    else:
        form = ShiftForm()

    shifts = Shift.objects.all()

    return render(request, 'admin_shift_template.html', {'form': form, 'shifts': shifts})



def admin_edit_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)

    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            new_shift = form.save(commit=False)
            from_time = new_shift.Shift_From
            to_time = new_shift.Shift_To

            if from_time > to_time:
                to_time = time(23, 59, 59)  # Handle the case where a shift continues into the next day

            if from_time != shift.Shift_From or to_time != shift.Shift_To:
                existing_shifts = Shift.objects.exclude(pk=new_shift.pk)

                # Check for time overlap with existing shifts, disallow shifts with small gaps
                for existing_shift in existing_shifts:
                    if (
                        (existing_shift.Shift_From <= from_time <= existing_shift.Shift_To) or
                        (existing_shift.Shift_From <= to_time <= existing_shift.Shift_To) or
                        (from_time <= existing_shift.Shift_From <= to_time) or
                        (
                            (datetime.combine(datetime.today(), existing_shift.Shift_To) + timedelta(minutes=30) >= datetime.combine(datetime.today(), from_time) and existing_shift.Shift_To < to_time) or
                            (datetime.combine(datetime.today(), existing_shift.Shift_From) - timedelta(minutes=30) <= datetime.combine(datetime.today(), to_time) and existing_shift.Shift_From > from_time)
                        )
                    ):
                        form.add_error(None, 'Shift time overlaps with an existing shift or has a small gap between shifts.')
                        break
                else:
                    new_shift.save()
                    return redirect('client_shift')
            else:
                new_shift.save()
                return redirect('client_shift')
    else:
        form = ShiftForm(instance=shift)

    shifts = Shift.objects.all()

    return render(request, 'admin_shift_template.html', {'form': form, 'shifts': shifts})

    
def admin_delete_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    shift.delete()
    return redirect('admin_shift')




def admin_report(request):
    part_numbers = MasterData.objects.values('PartNumber')
    shifts = Shift.objects.values('Shift_name')
    results = None

    if request.method == 'GET':
        selected_part_number = request.GET.get('partNumber')
        selected_shift = request.GET.get('Shift')
        Date_From = request.GET.get('dateFrom')
        Date_To = request.GET.get('dateTo')

        if selected_part_number:
            results = Show_report.objects.filter(PartNumber=selected_part_number)
        
        if selected_shift:
            results = Show_report.objects.filter(Shift=selected_shift)

        if Date_From and Date_To:
            date_from = datetime.strptime(Date_From, '%Y-%m-%d').strftime('%Y-%m-%d')
            date_to = datetime.strptime(Date_To, '%Y-%m-%d').strftime('%Y-%m-%d')

            with connections['default'].cursor() as cursor:
                query = """
                    SELECT * FROM leakapp_show_report
                    WHERE Date_Field >= %s AND Date_Field <= %s
                """
                cursor.execute(query, [date_from, date_to])

                # Fetch column names
                columns = [col[0] for col in cursor.description]

                # Fetch data as list of dictionaries
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'admin_report_template.html', {
        'part_numbers': part_numbers,
        'shifts': shifts,
        'results': results
    })

def get_highest_values():
    current_date = date.today()

    distinct_batch_counters_query = f"""
        SELECT DISTINCT BatchCounter FROM leakapp_result_tbl WHERE Date_Field > '{current_date}'
    """

    with connection.cursor() as cursor:
        cursor.execute(distinct_batch_counters_query)
        distinct_batch_counters = [row[0] for row in cursor.fetchall()]

    highest_values = {}

    for batch_counter in distinct_batch_counters:
        highest_values[batch_counter] = {}

        for filter_no in range(1, 17):
            highest_filter_value_query = f"""
                SELECT Filter_Values, Shift, result, PartNumber,Date_Field 
                FROM leakapp_result_tbl 
                WHERE Date_Field > '{current_date}' 
                AND BatchCounter = {batch_counter} 
                AND FilterNo = 'AI{filter_no}'
                ORDER BY Filter_Values DESC
                LIMIT 1
            """

            with connection.cursor() as cursor:
                cursor.execute(highest_filter_value_query)
                row = cursor.fetchone()

                if row:  # Check if row exists
                    highest_values[batch_counter][filter_no] = {
                        'Filter_Values': row[0],
                        'Shift': row[1],
                        'result': row[2],
                        'PartNumber': row[3],
                        'Date_Field': row[4]
                    }
                else:
                    # Handle the case where no row is fetched for this filter_no
                    highest_values[batch_counter][filter_no] = {
                        'Filter_Values': None,
                        'Shift': None,
                        'result': None,
                        'PartNumber': None,
                        'Date_Field': None
                    }

    return highest_values


def insert_highest_values(request=None):
    if request and request.method == 'POST':
        highest_values = get_highest_values()

        for batch_counter, filter_values in highest_values.items():
            for filter_no, highest_value in filter_values.items():
                # Create a new instance in ShowReport table with the highest value if it doesn't already exist
                result_value = highest_value['result'] if highest_value['result'] is not None else 'Unknown'
                part_number = highest_value['PartNumber'] if highest_value['PartNumber'] else 'Unknown'

                # Check if the record already exists before creating a new one
                existing_record = Show_report.objects.filter(
                    BatchCounter=batch_counter,
                    FilterNo=f'AI{filter_no}',
                    Highest_value=highest_value['Filter_Values'],
                    Shift=highest_value['Shift'],
                    result=result_value,
                    PartNumber=part_number  # Replace date_field with the correct value
                ).exists()

                if not existing_record:
                    try:
                        Show_report.objects.create(
                            BatchCounter=batch_counter,
                            FilterNo=f'AI{filter_no}',
                            Highest_value=highest_value['Filter_Values'],
                            Shift=highest_value['Shift'],
                            result=result_value,
                            PartNumber=part_number # Replace date_field with the correct value
                        )
                    except IntegrityError as e:
                        # Handle any integrity error if necessary
                        print(f"Integrity error occurred: {e}")
                        pass

        return JsonResponse({'message': 'Data updated and inserted successfully.'})

    return JsonResponse({'message': 'No data inserted.'})

def admin_manual(request):
    return render(request, 'admin_manual_template.html')












# Client master page Views

def client_master(request):
    data = MasterData.objects.all().order_by('-id')

    if request.method == 'POST':
        form = ClientMasterDataForm(request.POST)
        if form.is_valid():
            # Create an instance of the object without saving to the database yet
            instance = form.save(commit=False)

            # Assign a value to the 'PartNumber' field
            instance.PartNumber = form.cleaned_data['PartNumber']
            # # Set a default value for 'MultiFactor'
            # instance.MultiFactor = 0.5
            # Set a default value for 'GreaterLess'
            instance.GreaterLess = 'Greater'
            # Set a default value for 'Setpoint'
            instance.Setpoint = 18
            # Set a default value for 'Value'
            instance.Value = 1

            try:
                instance.save()
            except IntegrityError:
                # Handle any database integrity errors here
                pass

            return HttpResponseRedirect(request.path)

    else:
        form = ClientMasterDataForm()

    return render(request, 'client_master_template.html', {'form': form, 'data': data})


def client_edit_part_number(request, pk):
    record = get_object_or_404(MasterData, pk=pk)
    
    if request.method == 'POST':
        # Only update the 'PartNumber' field
        form = ClientMasterDataForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('client_master')  # Redirect back to the client page
    else:
        form = ClientMasterDataForm(instance=record)

    return render(request, 'client_master_template.html', {'form': form, 'editing_record': record})
        
def client_delete_record(request, pk):
    record = get_object_or_404(MasterData, pk=pk)
    record.delete()
    return redirect('client_master')

                   

def client_test(request):
    return render(request, 'client_test_template.html')

    

def client_report(request):
    part_numbers = MasterData.objects.values('PartNumber')
    shifts = Shift.objects.values('Shift_name')
    results = None

    if request.method == 'GET':
        selected_part_number = request.GET.get('partNumber')
        selected_shift = request.GET.get('Shift')
        Date_From = request.GET.get('dateFrom')
        Date_To = request.GET.get('dateTo')

        if selected_part_number:
            results = Result_tbl.objects.filter(PartNumber=selected_part_number)
        
        if selected_shift:
            results = Result_tbl.objects.filter(Shift=selected_shift)

        if Date_From and Date_To:
            date_from = datetime.strptime(Date_From, '%Y-%m-%d').strftime('%Y-%m-%d')
            date_to = datetime.strptime(Date_To, '%Y-%m-%d').strftime('%Y-%m-%d')

            with connections['default'].cursor() as cursor:
                query = """
                    SELECT * FROM leakapp_result_tbl
                    WHERE timestamp_field >= %s AND timestamp_field <= %s
                """
                cursor.execute(query, [date_from, date_to])

                # Fetch column names
                columns = [col[0] for col in cursor.description]

                # Fetch data as list of dictionaries
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'client_report_template.html', {
        'part_numbers': part_numbers,
        'shifts': shifts,
        'results': results
    })


# client shift page views.

def client_shift(request):
    if request.method == 'POST':
        form = ShiftForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('client_shift')
    else:
        form = ShiftForm()

    shifts = Shift.objects.all()

    return render(request, 'client_shift_template.html', {'form': form, 'shifts': shifts})



def edit_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)

    if request.method == 'POST':
        form = ShiftForm(request.POST, instance=shift)
        if form.is_valid():
            new_shift = form.save(commit=False)
            from_time = new_shift.Shift_From
            to_time = new_shift.Shift_To

            if from_time > to_time:
                to_time = time(23, 59, 59)  # Handle the case where a shift continues into the next day

            if from_time != shift.Shift_From or to_time != shift.Shift_To:
                existing_shifts = Shift.objects.exclude(pk=new_shift.pk)

                # Check for time overlap with existing shifts, disallow shifts with small gaps
                for existing_shift in existing_shifts:
                    if (
                        (existing_shift.Shift_From <= from_time <= existing_shift.Shift_To) or
                        (existing_shift.Shift_From <= to_time <= existing_shift.Shift_To) or
                        (from_time <= existing_shift.Shift_From <= to_time) or
                        (
                            (datetime.combine(datetime.today(), existing_shift.Shift_To) + timedelta(minutes=30) >= datetime.combine(datetime.today(), from_time) and existing_shift.Shift_To < to_time) or
                            (datetime.combine(datetime.today(), existing_shift.Shift_From) - timedelta(minutes=30) <= datetime.combine(datetime.today(), to_time) and existing_shift.Shift_From > from_time)
                        )
                    ):
                        form.add_error(None, 'Shift time overlaps with an existing shift or has a small gap between shifts.')
                        break
                else:
                    new_shift.save()
                    return redirect('client_shift')
            else:
                new_shift.save()
                return redirect('client_shift')
    else:
        form = ShiftForm(instance=shift)

    shifts = Shift.objects.all()

    return render(request, 'client_shift_template.html', {'form': form, 'shifts': shifts})

def delete_shift(request, shift_id):
    shift = get_object_or_404(Shift, pk=shift_id)
    shift.delete()
    return redirect('client_shift')




def client_manual(request):
    return render(request, 'client_manual_template.html')

# Operator Views

def operator_test(request):
    return render(request, 'operator_test_template.html')

def operator_report(request):
    part_numbers = MasterData.objects.values('PartNumber')
    shifts = Shift.objects.values('Shift_name')
    results = None

    if request.method == 'GET':
        selected_part_number = request.GET.get('partNumber')
        selected_shift = request.GET.get('Shift')
        Date_From = request.GET.get('dateFrom')
        Date_To = request.GET.get('dateTo')

        if selected_part_number:
            results = Result_tbl.objects.filter(PartNumber=selected_part_number)
        
        if selected_shift:
            results = Result_tbl.objects.filter(Shift=selected_shift)

        if Date_From and Date_To:
            date_from = datetime.strptime(Date_From, '%Y-%m-%d').strftime('%Y-%m-%d')
            date_to = datetime.strptime(Date_To, '%Y-%m-%d').strftime('%Y-%m-%d')

            with connections['default'].cursor() as cursor:
                query = """
                    SELECT * FROM leakapp_result_tbl
                    WHERE timestamp_field >= %s AND timestamp_field <= %s
                """
                cursor.execute(query, [date_from, date_to])

                # Fetch column names
                columns = [col[0] for col in cursor.description]

                # Fetch data as list of dictionaries
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'operator_report_template.html', {
        'part_numbers': part_numbers,
        'shifts': shifts,
        'results': results
    })


def operator_manual(request):
    return render(request, 'operator_manual_template.html')



# Logout View

def logout_view(request):
    logout(request)
    return redirect('login_view')  





