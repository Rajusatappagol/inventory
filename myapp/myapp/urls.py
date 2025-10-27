"""
URL configuration for myapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.shortcuts import redirect
from inventory import views
from rest_framework import routers


# register API routes
router = routers.DefaultRouter()
router.register(r'api/stocks', views.InventoryViewSet, basename='inventory')
def root_redirect(request):
    return redirect('/admin/home/')
def logout_redirect(request):
    return redirect('/inventory/logout/')
def stock_redirect(request):
    return redirect('/inventory/stock/')
def employee_issues_redirect(request):
    return redirect('/inventory/employee_issue_items/')
def stationary_redirect(request):
    return redirect('/stationary/stationary/')  
def location_redirect(request):
    return redirect('location/location/') 
def sign_redirect(request):
    return redirect('/admin/sign/')
def register_redirect(request):
    return redirect('/admin/register/')
def custom_admin_redirect(request):
    return redirect('/admin/custom_admin/')

urlpatterns = [
    path('logout/', logout_redirect),
    path('stock/', stock_redirect),
    path('employee_issues/', employee_issues_redirect),
    path('admin/register/', views.register, name='register'),
    path('', root_redirect),
    path('stationary/stationary/', views.stationary, name='stationary'),
    path('admin/sign/', views.sign_view, name='admin_sign'),
    path('admin/home/', views.home_view, name='admin_home'),
    path('admin/dashboard/', views.dashboard, name='admin_dashboard'),
    path('admin/custom_admin/', views.custom_admin_view, name='admin_custom_admin'),
    path('inventory/stock/', views.stock_view, name='inventory_stock'),
    path('inventory/logout/', views.logout_view, name='inventory_logout'),
    path('inventory/employee_issue_items/', views.employee_issue_items_view, name='inventory_employee_issue_items'),
    path('inventory/', include('inventory.urls')),
    path('', include(router.urls)),
    

]

