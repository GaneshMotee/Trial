from django.urls import path
from . import views
from .views import ShowDetails
# Define the URL patterns for your views

urlpatterns = [
    path('', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('adminpage/', views.admin_master, name='adminpage'),
    path('client/', views.client_master, name='client'),
    path('operator/', views.operator, name='operator'),

    # Admin URLs
    path('admin_master/', views.admin_master, name='admin_master'),
    path('edit/<int:pk>/', views.admin_edit_record, name='edit_record'),
    path('delete/<int:pk>/',views.admin_delete_record, name='delete_record'),
    
    
    path('admin_test/', views.admin_test, name='admin_test'),
    path('ShowDetails/', ShowDetails, name='show_details'),
    path('update_data/', views.update_batch_result_highest, name='update_data'),
    path('get_data/', views.get_current_shift, name='get_data'),
    path('insert_highest_values', views.insert_highest_values, name='insert_highest_values'),
    path('get_setpoint/', views.get_setpoint, name='get_setpoint'),
    path('update_result/', views.update_result, name='update_result'),
    #path('insert_batch_results/', views.insert_batch_results, name='insert_batch_results'),
    #path('get_last_5_nok_filters/', views.get_last_5_nok_filters, name='get_last_5_nok_filters'),
    # path('', index, name='index'),
    
    
    path('admin_shift/', views.admin_shift, name='admin_shift'),
    path('edit_shift/<int:shift_id>/', views.admin_edit_shift, name='admin_edit_shift'),
    path('delete_shift/<int:shift_id>/', views.admin_delete_shift, name='admin_delete_shift'),
    
    
    path('admin_report/', views.admin_report, name='admin_report'),

    
    path('admin_manual/', views.admin_manual, name='admin_manual'),
    path('admin_logout/', views.logout_view, name='admin_logout'),
    
    # path('master/', views.master_view, name='master_screen'),
    # path('insert_data/', views.insert_data, name='insert_data'),
   

    # Client URLs
    path('client/master/', views.client_master, name='client_master'),
    path('client/edit_part_number/<int:pk>/', views.client_edit_part_number, name='client_edit_part_number'),
    path('client/delete/<int:pk>/', views.client_delete_record, name='client_delete_record'),





    path('client/test/', views.client_test, name='client_test'),
    path('client/report/', views.client_report, name='client_report'),

    
    path('client/shift/', views.client_shift, name='client_shift'),
    path('edit_shift/<int:shift_id>/', views.edit_shift, name='edit_shift'),
    path('delete_shift/<int:pk>/', views.delete_shift, name='delete_shift'),
    

    path('client/manual/', views.client_manual, name='client_manual'),
    path('client/logout/', views.logout_view, name='client_logout'),

    # Operator URLs
    path('operator/test/', views.operator_test, name='operator_test'),
    path('operator/report/', views.operator_report, name='operator_report'),
    path('operator/manual/', views.operator_manual, name='operator_manual'),
    path('operator/logout/', views.logout_view, name='operator_logout'),
]





