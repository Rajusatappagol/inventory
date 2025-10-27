from django.urls import path, include
from . import views
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'api/stocks', views.InventoryViewSet, basename='inventory')

urlpatterns = [
    path('', views.sign_view, name='sign_view'),
    path('sign/', views.sign_view, name='sign_view'),
    path('custom_admin/', views.custom_admin_view, name='custom_admin_view'),
    path('register/', views.register, name='register'),

    path('logout/', views.logout_view, name='logout'),
    path('logout_view/', views.logout_view, name='logout_view'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard_view/', views.dashboard, name='dashboard_view'),

    path('home/', views.home_view, name='home'),
    path('employee_issue_items/', views.employee_issue_items_view, name='employee_issue_items'),
    path('forecast-next-issues/', views.forecast_next_issues, name='forecast_next_issues'),
    path('forecast-month-details/<str:start>/', views.forecast_month_details, name='forecast_month_details'),

    path('get-employeedetails/<str:emp_id>/', views.get_employeedetails, name='get_employeedetails'),
    path('check-issue-block/', views.check_issue_block, name='check_issue_block'),
    path('check-stock-availability/', views.check_stock_availability, name='check_stock_availability'),
    path('search-issues/', views.search_issues, name='search_issues'),
    path('save-issue/', views.save_issue, name='save_issue'),

    path('stock/', views.stock_view, name='stock'),
    path('stock/add/', views.add_stock, name='add_stock'),

    # Stationary pages and actions
    path('stationary/', views.stationary, name='stationary'),
    path('stationary/add-type/', views.add_stationary_type, name='add_stationary_type'),
    path('stationary/add-item/', views.add_stationary_item, name='add_stationary_item'),
    path('stationary/update-item/<int:item_id>/', views.update_stationary_item, name='update_stationary_item'),
    path('stationary/submit-issue/', views.submit_stationary_issue, name='submit_stationary_issue'),

    path('issue_items/<str:category>/', views.issue_items_view, name='issue_items'),
    path('download/employee-issue-report/', views.download_employee_issue_report, name='download_employee_issue_report'),
    path('download/employee-due-report/', views.download_employee_due_report, name='download_employee_due_report'),
    
    # JSON endpoints for dashboard overview reports
    path('api/reports/issue/', views.issue_report_json, name='api_issue_report'),
    path('api/reports/due/', views.due_report_json, name='api_due_report'),
    path('api/reports/extra/', views.extra_report_json, name='api_extra_report'),
    path('api/reports/update-issue/', views.update_issue_ajax, name='api_update_issue'),
    
    # Enhanced forecast API endpoints
    path('api/forecast/details/', views.forecast_details_api, name='api_forecast_details'),
    path('api/forecast/summary/', views.forecast_summary_api, name='api_forecast_summary'),

    # Include DRF router URLs
    path('', include(router.urls)),
]
