from django.contrib import admin
from .models import EmployeeDetails, Inventory, EmployeeIssue, Location

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
	list_display = ('entity','item_type','color', 'size','quantity', 'created_at', 'updated_at', 'due')
	list_filter = ('item_type',)
	search_fields = ('item_type', 'color', 'size')

@admin.register(EmployeeIssue)
class EmployeeIssueAdmin(admin.ModelAdmin):
	list_display = ('emp_id', 'name', 'email','gender','entity','Category', 'Subcategory', 'size','Issued_quantity', 'issued_date','Next_issue_date' ,'Buy')
	search_fields = ('emp_id', )
	list_filter = ('issued_date',)

@admin.register(EmployeeDetails)
class EmployeeDetailsAdmin(admin.ModelAdmin):
	list_display = ('emp_id', 'emp_name', 'emp_email','gender','entity'	)
	search_fields = ('emp_id', )

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
     list_display = ('Location',)

class StationaryAdmin(admin.ModelAdmin):
	list_display = ('category', 'quantity', 'created_at', 'updated_at')
	search_fields = ('category',)
	list_filter = ('category',)
