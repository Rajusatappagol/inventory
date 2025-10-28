from urllib import request
from django.contrib import messages
from inventory import models
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth import authenticate, logout
from django.contrib.auth.decorators import login_required
from .models import Inventory
from django.http import JsonResponse, HttpResponseNotAllowed
from django.db.models import Sum, Count, Q
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import InventorySerializer
import json
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .models import Profile
from .decorators import role_required

@login_required
def stock_view(request):
	# Only admin can access stock view
	try:
		if request.user.profile.role != 'admin':
			messages.error(request, 'You do not have permission to access this page.')
			return redirect('employee_issue_items')
	except:
		messages.error(request, 'You do not have permission to access this page.')
		return redirect('employee_issue_items')
	
	from .models import Category_Choices, Subcategory_Choices, entity_choices
	
	category_sizes = {
		'tshirt': ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL'],
		'formals': ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL'],
		'jeans': ['28', '30', '32', '34', '36', '38', '40', '42', '44', '46', '48'],
		'safety_shoes': ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
		'goggles': ['normal', 'overhead'],
		'trainee': ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL'],
	}

	counts = {}
	try:
		qs = Inventory.objects.all()
		tshirt_qs = qs.filter(item_type__iexact='tshirt')
		counts['tshirt'] = {
			'black': int(tshirt_qs.filter(color__iexact='black').aggregate(total=Sum('quantity'))['total'] or 0),
			'white': int(tshirt_qs.filter(color__iexact='white').aggregate(total=Sum('quantity'))['total'] or 0),
		}
		counts['tshirt']['total'] = counts['tshirt']['black'] + counts['tshirt']['white']

		shoes_qs = qs.filter(item_type__iexact='safety_shoes')
		counts['safety_shoes'] = {
			'ladies': int(shoes_qs.filter(color__icontains='ladies').aggregate(total=Sum('quantity'))['total'] or 0),
			'gents': int(shoes_qs.filter(color__icontains='gents').aggregate(total=Sum('quantity'))['total'] or 0),
	
		}
		counts['safety_shoes']['total'] = counts['safety_shoes']['ladies'] + counts['safety_shoes']['gents']

		formals_qs = qs.filter(item_type__iexact='formals')
		counts['formals'] = {
			'gents_grey': int(formals_qs.filter(Q(color__icontains='gents') & Q(color__icontains='grey')).aggregate(total=Sum('quantity'))['total'] or 0),
			'gents_white': int(formals_qs.filter(Q(color__icontains='gents') & Q(color__icontains='white')).aggregate(total=Sum('quantity'))['total'] or 0),
			'ladies_grey': int(formals_qs.filter(Q(color__icontains='ladies') & Q(color__icontains='grey')).aggregate(total=Sum('quantity'))['total'] or 0),
			'ladies_white': int(formals_qs.filter(Q(color__icontains='ladies') & Q(color__icontains='white')).aggregate(total=Sum('quantity'))['total'] or 0),
		}
		counts['formals']['total'] = (
			counts['formals']['gents_grey'] + counts['formals']['gents_white'] +
			counts['formals']['ladies_grey'] + counts['formals']['ladies_white']
		)

		goggles_qs = qs.filter(item_type__iexact='goggles')
		counts['goggles'] = {
			'normal': int(goggles_qs.filter(color__icontains='normal').aggregate(total=Sum('quantity'))['total'] or 0),
			'overhead': int(goggles_qs.filter(color__icontains='overhead').aggregate(total=Sum('quantity'))['total'] or 0),
		}
		counts['goggles']['total'] = counts['goggles']['normal'] + counts['goggles']['overhead']
		counts['jeans'] = int(qs.filter(item_type__iexact='jeans').aggregate(total=Sum('quantity'))['total'] or 0)
		counts['trainee'] = int(qs.filter(item_type__iexact='trainee').aggregate(total=Sum('quantity'))['total'] or 0)

	except Exception:
		counts = {}

	context = {
		'stock_counts': counts,
		'CATEGORY_CHOICES': [{'value': choice[0], 'label': choice[1]} for choice in Category_Choices],
		'SUBCATEGORY_CHOICES': [{'value': choice[0], 'label': choice[1]} for choice in Subcategory_Choices],
		'ENTITY_CHOICES': [{'value': choice[0], 'label': choice[1]} for choice in entity_choices],
		'CATEGORY_SIZES': category_sizes,
	}
	return render(request, 'inventory/stock.html', context)

@login_required
def add_stock(request):
	# Admin-only access for adding stock
	try:
		if hasattr(request.user, 'profile') and request.user.profile.role != 'admin':
			return redirect('employee_issue_items')
	except Exception:
		return redirect('sign_view')
	
	return render(request, 'inventory/add_stock.html')

def home_view(request):
	return render(request, 'admin/home.html')

def custom_admin_view(request):
	return render(request, 'admin/custom_admin.html')

def sign_view(request):
	error_message = None
	next_url = request.GET.get('next') or request.POST.get('next') 
	if request.method == 'POST':
		username = request.POST.get('username', '').strip()
		password = request.POST.get('password', '')
		if not username or not password:
			error_message = 'Username and password are required.'
		else:
			user = authenticate(request, username=username, password=password)
			if user is not None:
				login(request,user)
				messages.success(request, 'Sign in successful.')
				
				# Check user role and redirect accordingly
				try:
					user_role = user.profile.role
					if user_role == 'staff':
						return redirect('employee_issue_items')
					elif user_role == 'admin':
						return redirect('admin_dashboard')
					else:
						return redirect('admin_dashboard')
				except:
					return redirect('admin_dashboard')
			else:
				error_message = 'Invalid username or passwords.'

	return render(request, 'admin/sign.html', {'error_message': error_message, 'next': next_url})


@login_required
def stationary(request):
    # Allow only admin and staff to access stationary view
    try:
        user_role = request.user.profile.role
        if user_role not in ['admin', 'staff']:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('employee_issue_items')
    except Exception as e:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('employee_issue_items')
    
    return render(request, 'stationary/stationary.html')

def logout_view(request):
	logout(request)
	messages.success(request, 'You have been logged out.')
	return redirect('/admin/home/')
@login_required
def dashboard(request):
	# Check user role
	try:
		role = request.user.profile.role
	except:
		role = 'staff'
	
	if role == 'staff':
		return redirect('employee_issue_items')
	
	if role == 'admin':
		from django.db.models import Sum, Count
		import datetime, json
		try:
			total_inventory = int(Inventory.objects.aggregate(total=Sum('quantity'))['total'] or 0)
			try:
				total_allotted = int(models.EmployeeIssue.objects.aggregate(total=Sum('Issued_quantity'))['total'] or 0)
			except Exception:
				total_allotted = 0
			remaining_stock = total_inventory
			# low stock items ( 50)
			low_qs = Inventory.objects.filter(quantity__lte=50).order_by('quantity')
			low_items = list(low_qs.values('id', 'item_type', 'color', 'size', 'quantity')[:200])
			low_count = low_qs.count()
			stock_alert_text = 'Stock OK' if low_count == 0 else f'{low_count} low'

			# Next month and next-to-next month allot counts (by Next_issue_date)
			today = datetime.date.today()
			first_of_next = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
			first_of_next2 = (first_of_next + datetime.timedelta(days=32)).replace(day=1)
			next_month_end = (first_of_next + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
			next2_month_end = (first_of_next2 + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
			next_month_count = models.EmployeeIssue.objects.filter(Next_issue_date__gte=first_of_next, Next_issue_date__lte=next_month_end).aggregate(total=Sum('Issued_quantity'))['total'] or 0
			next2_month_count = models.EmployeeIssue.objects.filter(Next_issue_date__gte=first_of_next2, Next_issue_date__lte=next2_month_end).aggregate(total=Sum('Issued_quantity'))['total'] or 0
			# issued counts for last 6 months (by issued_date)
			issued_months = []
			for m in range(6):
				start = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)  
				ref = (today.replace(day=1) - datetime.timedelta(days=30*(5-m)))
				first = ref.replace(day=1)
				next_month = (first + datetime.timedelta(days=32)).replace(day=1)
				last = next_month - datetime.timedelta(days=1)
				qs = models.EmployeeIssue.objects.filter(issued_date__gte=first, issued_date__lte=last)
				issued_months.append({ 'label': first.strftime('%b %Y'), 'count': int(qs.aggregate(c=Count('id'))['c'] or 0) })

			low_by_type = low_qs.values('item_type').annotate(total=Sum('quantity')).order_by('-total')
			low_labels = [r['item_type'] or 'unknown' for r in low_by_type]
			low_data = [int(r['total'] or 0) for r in low_by_type]

			issued_labels = [m['label'] for m in issued_months]
			issued_data = [m['count'] for m in issued_months]

			try:
				past_start = (today.replace(day=1) - datetime.timedelta(days=30*6)).replace(day=1)
			except Exception:
				past_start = (today - datetime.timedelta(days=30*6))
			past_qs = models.EmployeeIssue.objects.filter(issued_date__gte=past_start, issued_date__lt=today)
			past_total = int(past_qs.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
			avg_monthly = int(past_total / 6) if past_total else 0
			forecast_months = []
			forecast_by_category = {}
			forecast_by_entity = {}
			forecast_by_size = {}
			
			categories = [c[0] for c in getattr(models, 'Category_Choices', [])]
			entities = [e[0] for e in getattr(models, 'entity_choices', [])]
			sizes = [s[0] for s in getattr(models, 'size_Choices', [])]
			
			for m in range(6):
				first = (today.replace(day=1) + datetime.timedelta(days=32*m)).replace(day=1)
				next_month = (first + datetime.timedelta(days=32)).replace(day=1)
				last = next_month - datetime.timedelta(days=1)
				qs_f = models.EmployeeIssue.objects.filter(Next_issue_date__gte=first, Next_issue_date__lte=last)
				qty_sum = int(qs_f.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
				
				# Overall forecast
				forecast_months.append({'label': first.strftime('%b %Y'), 'total_required': (qty_sum if qty_sum > 0 else avg_monthly)})
				
				# Category-wise forecast
				month_label = first.strftime('%b %Y')
				forecast_by_category[month_label] = {}
				for cat in categories:
					cat_qs = qs_f.filter(Category__iexact=cat)
					cat_qty = int(cat_qs.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
					if cat_qty == 0:
						hist_cat_qs = models.EmployeeIssue.objects.filter(
							issued_date__gte=past_start, 
							issued_date__lt=today, 
							Category__iexact=cat
						)
						hist_cat_total = int(hist_cat_qs.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
						cat_qty = int(hist_cat_total / 6) if hist_cat_total else 0
					forecast_by_category[month_label][cat] = cat_qty
				
				# Entity-wise forecast
				forecast_by_entity[month_label] = {}
				for entity in entities:
					ent_qs = qs_f.filter(entity__iexact=entity)
					ent_qty = int(ent_qs.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
					if ent_qty == 0:
						hist_ent_qs = models.EmployeeIssue.objects.filter(
							issued_date__gte=past_start, 
							issued_date__lt=today, 
							entity__iexact=entity
						)
						hist_ent_total = int(hist_ent_qs.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
						ent_qty = int(hist_ent_total / 6) if hist_ent_total else 0
					forecast_by_entity[month_label][entity] = ent_qty
				
				forecast_by_size[month_label] = {}
				common_sizes = ['XS', 'S', 'M', 'L', 'XL', '2XL','3XL','4XL','5XL','28','30', '32', '34', '36', '38', '40', '42', '44', '46', '48', 'normal', 'overhead','2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
				for size in common_sizes:
					size_qs = qs_f.filter(size__iexact=size)
					size_qty = int(size_qs.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
					if size_qty == 0:
						hist_size_qs = models.EmployeeIssue.objects.filter(
							issued_date__gte=past_start, 
							issued_date__lt=today, 
							size__iexact=size
						)
						hist_size_total = int(hist_size_qs.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
						size_qty = int(hist_size_total / 6) if hist_size_total else 0
					forecast_by_size[month_label][size] = size_qty

			forecast_labels = [m['label'] for m in forecast_months]
			forecast_data = [m['total_required'] for m in forecast_months]

			this_month_start = today.replace(day=1)
			this_month_next = (this_month_start + datetime.timedelta(days=32)).replace(day=1)
			this_month_qs = models.EmployeeIssue.objects.filter(issued_date__gte=this_month_start, issued_date__lt=this_month_next)
			this_month_total = int(this_month_qs.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
			forecast_from_current = [int(this_month_total) for _ in range(6)]
			entity_stock = []
			try:
				entity_stock_qs = Inventory.objects.values('entity', 'item_type', 'color').annotate(
					total_quantity=Sum('quantity')
				).filter(total_quantity__gt=0).order_by('entity', 'item_type', 'color')
				
				for item in entity_stock_qs:
					entity_stock.append({
						'entity_name': item['entity'] or 'No Entity',
						'category': item['item_type'] or 'Unknown',
						'subcategory': item['color'] or 'Unknown',
						'total_quantity': int(item['total_quantity'] or 0),
						'updated_date': timezone.now().strftime('%Y-%m-%d'),
					})
			except Exception as e:
				print(f"DEBUG: Error getting entity stock: {e}")
				entity_stock = []

			from .models import entity_choices
			entity_choices_list = [{'value': choice[0], 'label': choice[1]} for choice in entity_choices]

			context = {
				'kpi_opening_stock': total_inventory,
				'kpi_total_allotted': total_allotted,
				'kpi_remaining_stock': remaining_stock,
				'kpi_stock_alert_text': stock_alert_text,
				'kpi_next_month_allot': int(next_month_count or 0),
				'kpi_next_to_next_allot': int(next2_month_count or 0),
				'low_stock_items_json': json.dumps(low_items),
				'low_stock_chart': json.dumps({'labels': low_labels, 'data': low_data}),
				'issued_6m_chart': json.dumps({'labels': issued_labels, 'data': issued_data}),
				'forecast_6m_chart': json.dumps({'labels': forecast_labels, 'data': forecast_data}),
				'forecast_from_current_chart': json.dumps({'labels': forecast_labels, 'data': forecast_from_current}),
				'forecast_by_category': json.dumps(forecast_by_category),
				'forecast_by_entity': json.dumps(forecast_by_entity),
				'forecast_by_size': json.dumps(forecast_by_size),
				'categories_list': json.dumps(categories),
				'entities_list': json.dumps(entities),
				'entity_stock': entity_stock,
				'ENTITY_CHOICES': entity_choices_list,
			}
		except Exception as e:
			print(f"DEBUG: Error in dashboard view: {e}")
			context = {
				'kpi_opening_stock': 0,
				'kpi_total_allotted': 0,
				'kpi_remaining_stock': 0,
				'kpi_stock_alert_text': 'Unknown',
				'kpi_next_month_allot': 0,
				'kpi_next_to_next_allot': 0,
				'low_stock_items_json': '[]',
				'low_stock_chart': json.dumps({'labels': [], 'data': []}),
				'issued_6m_chart': json.dumps({'labels': [], 'data': []}),
				'forecast_6m_chart': json.dumps({'labels': [], 'data': []}),
				'forecast_from_current_chart': json.dumps({'labels': [], 'data': []}),
				'forecast_by_category': json.dumps({}),
				'forecast_by_entity': json.dumps({}),
				'forecast_by_size': json.dumps({}),
				'categories_list': json.dumps([]),
				'entities_list': json.dumps([]),
				'entity_stock': [],
				'ENTITY_CHOICES': [],
			}
		return render(request, 'admin/dashboard.html', context)
	# Fallback for other roles or errors
	try:
		entity_stock = []
		entity_stock_qs = Inventory.objects.values('entity', 'item_type', 'color').annotate(
			total_quantity=Sum('quantity')
		).filter(total_quantity__gt=0).order_by('entity', 'item_type', 'color')
		
		for item in entity_stock_qs:
			entity_stock.append({
				'entity_name': item['entity'] or 'No Entity',
				'category': item['item_type'] or 'Unknown',
				'subcategory': item['color'] or 'Unknown',
				'total_quantity': int(item['total_quantity'] or 0),
				'updated_date': timezone.now().strftime('%Y-%m-%d'),
			})
		
		from .models import entity_choices
		entity_choices_list = [{'value': choice[0], 'label': choice[1]} for choice in entity_choices]
		
		fallback_context = {
			'entity_stock': entity_stock,
			'ENTITY_CHOICES': entity_choices_list,
		}
	except Exception:
		fallback_context = {
			'entity_stock': [],
			'ENTITY_CHOICES': [],
		}
	
	return render(request, 'admin/dashboard.html', fallback_context)


@login_required
def employee_issue_items_view(request):
	# Both admin and staff can access this page
	from .models import EmployeeDetails, EmployeeIssue, Category_Choices, Subcategory_Choices, size_Choices

	employees = EmployeeDetails.objects.all()
	issues_qs = EmployeeIssue.objects.all().order_by('-issued_date', '-id')

	issues = []
	for i in issues_qs:
		issues.append({
			'id': i.id,
			'emp_id': i.emp_id,
			'name': i.name,
			'email': i.email,
			'gender': i.gender,
            'entity': i.entity,
			'Category': i.Category,
			'Subcategory': i.Subcategory,
			'size': i.size,
			'Issued_quantity': i.Issued_quantity,
			'issued_date': i.issued_date.isoformat() if getattr(i, 'issued_date', None) else None,
			'next_issue_date': i.Next_issue_date.isoformat() if getattr(i, 'Next_issue_date', None) else None,
			'Buy': i.Buy or '',
			'buy_price': float(i.buy_price) if getattr(i, 'buy_price', None) else None,
		})

	categories = [{'value': c[0], 'label': c[1]} for c in Category_Choices]
	subcategories = [{'value': s[0], 'label': s[1]} for s in Subcategory_Choices]
	sizes = [{'value': s[0], 'label': s[1]} for s in size_Choices]

	sub_label_map = {s[0]: s[1] for s in Subcategory_Choices}

	category_to_sub = {
		'tshirt': ['black', 'white'],
		'jeans': ['jeans'],
		'safety_shoes': ['ladies', 'gents'],
		'formals': ['Grey_Shirt', 'White_Shirt'],
		'goggles': ['normal', 'overhead'],
		'trainee': ['trainee'],
		
	}

	category_to_size = {
		'tshirt': ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL'],
		'formals': ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL'],
		'jeans': ['28', '30', '32', '34', '36', '38', '40', '42', '44', '46', '48'],
		'safety_shoes': ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
		'goggles': ['normal', 'overhead'],
		'trainee': ['XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL', '5XL'],
	}

	aggregated_qs = EmployeeIssue.objects.values('Category', 'Subcategory', 'size')
	aggregated_qs = aggregated_qs.annotate(total_quantity=Sum('Issued_quantity'), rows=Count('id')).order_by('Category', 'Subcategory', 'size')

	aggregated_issues = []
	for grp in aggregated_qs:
		cat = grp.get('Category') or ''
		sub = grp.get('Subcategory') or ''
		sz = grp.get('size') or ''
		members_qs = EmployeeIssue.objects.filter(Category=cat, Subcategory=sub, size=sz).order_by('-issued_date')
		members = []
		for m in members_qs:
			members.append({
				'id': m.id,
				'emp_id': m.emp_id,
				'name': m.name,
				'email': m.email,
				'gender': m.gender,
				'entity': m.entity,
				'issued_date': m.issued_date.isoformat() if getattr(m, 'issued_date', None) else None,
				'Issued_quantity': m.Issued_quantity,
				'next_issue_date': m.Next_issue_date.isoformat() if getattr(m, 'Next_issue_date', None) else None,
			})

		aggregated_issues.append({
			'Category': cat,
			'Subcategory': sub,
			'size': sz,
			'total_quantity': int(grp.get('total_quantity') or 0),
			'rows': int(grp.get('rows') or 0),
			'members': members,
		})


	return render(request, 'inventory/employee_issue_items.html', {
		'employees': employees,
		'issues': issues,
		'aggregated_issues': aggregated_issues,
		'categories': categories,
		'subcategories': subcategories,
		'sizes': sizes,
		'category_to_sub_json': json.dumps(category_to_sub),
		'category_to_size_json': json.dumps(category_to_size),
		'sub_label_map_json': json.dumps(sub_label_map),

		
	})


@login_required
def save_issue(request):
	# Both admin and staff can save issues
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])

	issue_id = request.POST.get('issue_id') or None
	emp_id = request.POST.get('empId') or request.POST.get('emp_id')
	name = request.POST.get('employeeName') or request.POST.get('name')
	email = request.POST.get('email')
	gender = request.POST.get('gender') 
	entity = request.POST.get('entity') or ''	
	category = request.POST.get('Category') or ''
	subcategory = request.POST.get('Subcategory') or ''
	size = request.POST.get('size') or ''
	issued_quantity = request.POST.get('Issued_quantity') or request.POST.get('Tshirt_quantity') or request.POST.get('accessoryQty')  or request.POST.get('Safety-Shoes') or request.POST.get('jeansQty') or request.POST.get('formalsQty') or request.POST.get("traineeQty")  or request.POST.get('quantity') or request.POST.get('Issued_quantity') or request.POST.get( 'traineejeansQty') or request.POST.get('gogglesQty') or request.POST.get('greyQty') or request.POST.get('whiteQty')
	multi_issues_json = request.POST.get('multi_issues') or ''

	try:
		if emp_id:
			from .models import EmployeeDetails
			emp_q = EmployeeDetails.objects.filter(emp_id__iexact=str(emp_id).strip()).first()
			if not emp_q:
				try:
					EmployeeDetails.objects.create(
						emp_id=str(emp_id).strip(),
						emp_name=(name or '').strip(),
						emp_email=(email or '').strip(),
						gender=(gender or '').strip(),
						entity=(entity or '').strip()
					)
				except Exception:
					pass
	except Exception:
		pass

	def adjust_inventory(category_value, subcategory_value, size_value, delta, entity_value=None):
		"""
		Adjust inventory stock by delta amount for specific entity, category, subcategory, and size.
		Returns True if successful, False if insufficient stock or no matching inventory found.
		"""
		try:
			if not category_value:
				return False
			try:
				d = int(delta)
			except Exception:
				d = 0
			
			if d == 0:
				return True
				
			cat = (category_value or '').strip()
			sub = (subcategory_value or '').strip()
			sz = (size_value or '').strip()
			ent = (entity_value or '').strip()
			
			filters = {}
			if cat:
				filters['item_type__iexact'] = cat
			if sub:
				filters['color__iexact'] = sub
			if sz:
				filters['size__iexact'] = sz
			if ent:
				filters['entity__iexact'] = ent
			
			inv = Inventory.objects.filter(**filters).first()
			
			if not inv:
				if ent:
					fallback_filters = {k: v for k, v in filters.items() if k != 'entity__iexact'}
					inv = Inventory.objects.filter(**fallback_filters).first()
				
				if not inv:
					return False
			
			current = int(inv.quantity or 0)

			if d > 0:  # Issuing items (reducing stock)
				if current < d:
					return False  
				new = current - d
			else:  # Returning items (increasing stock)
				new = current + abs(d)
			
			inv.quantity = new
			inv.save()
			return True
			
		except Exception as e:
			print(f"Error in adjust_inventory: {e}")
			return False

	def check_inventory(category_value, subcategory_value, size_value, required_qty, entity_value=None):
		
		try:
			if required_qty is None:
				required_qty = 0
			req = int(required_qty or 0)
			if req <= 0:
				return True
			
			cat = (category_value or '').strip()
			sub = (subcategory_value or '').strip()
			sz = (size_value or '').strip()
			ent = (entity_value or '').strip()
			
			filters = {}
			if cat:
				filters['item_type__iexact'] = cat
			if sub:
				filters['color__iexact'] = sub
			if sz:
				filters['size__iexact'] = sz
			if ent:
				filters['entity__iexact'] = ent
			
			inv = Inventory.objects.filter(**filters).first()
			
			if not inv:
				if ent:
					fallback_filters = {k: v for k, v in filters.items() if k != 'entity__iexact'}
					inv = Inventory.objects.filter(**fallback_filters).first()
				
				if not inv:
					return False
			
			available = int(inv.quantity or 0)
			return available >= req
			
		except Exception as e:
			print(f"Error in check_inventory: {e}")
			return False

	def get_available_quantity(category_value, subcategory_value, size_value, entity_value=None):
		
		try:
			cat = (category_value or '').strip()
			sub = (subcategory_value or '').strip()
			sz = (size_value or '').strip()
			ent = (entity_value or '').strip()

			if cat and cat.lower() == 'formals':
				qs = Inventory.objects.filter(item_type__iexact=cat)
				if ent:
					qs = qs.filter(entity__iexact=ent)
				if sub:
					token = sub.strip().lower()
					if '_' in token:
						parts = token.split('_')
						qs = qs.filter(Q(color__icontains=parts[0]) & Q(color__icontains=parts[1]))
					else:
						if 'grey' in token or 'gray' in token:
							qs = qs.filter(color__icontains='grey')
						elif 'white' in token:
							qs = qs.filter(color__icontains='white')
						else:
							qs = qs.filter(color__icontains=token)
				if sz:
					qs = qs.filter(size__iexact=sz)
				total = qs.aggregate(total=Sum('quantity'))['total'] or 0
				return int(total)

			filters = {}
			if cat:
				filters['item_type__iexact'] = cat
			if sub:
				filters['color__iexact'] = sub
			if sz:
				filters['size__iexact'] = sz
			if ent:
				filters['entity__iexact'] = ent

			inv = Inventory.objects.filter(**filters).first()
			if not inv and ent:
				fallback_filters = {k: v for k, v in filters.items() if k != 'entity__iexact'}
				inv = Inventory.objects.filter(**fallback_filters).first()

			if inv:
				return int(inv.quantity or 0)

			qs = Inventory.objects.all()
			if cat:
				qs = qs.filter(item_type__iexact=cat)
			if ent:
				qs = qs.filter(entity__iexact=ent)
			if sub:
				s_token = sub.strip()
				qs = qs.filter(
					Q(color__icontains=s_token) | Q(color__iexact=s_token) | Q(item_type__icontains=s_token) | Q(item_type__iexact=s_token)
				)
			if sz:
				qs = qs.filter(size__iexact=sz)
			total = qs.aggregate(total=Sum('quantity'))['total'] or 0
			return int(total)
		except Exception as e:
			print(f"Error in get_available_quantity: {e}")
			return 0

	def latest_next_issue_datetime(emp_id_value, category_value, subcategory_value, size_value):
		"""Return the latest Next_issue_date for this employee+item (datetime) or None.""" 
		try:  
			if not emp_id_value:
				return None
			q = models.EmployeeIssue.objects.filter(emp_id=str(emp_id_value).strip())
			if category_value:
				q = q.filter(Category__iexact=category_value)
			if subcategory_value:
				q = q.filter(Subcategory__iexact=subcategory_value)
			if size_value:
				q = q.filter(size__iexact=size_value)
			q = q.order_by('-issued_date').first()
			if not q:
				return None
			return getattr(q, 'Next_issue_date', None)
		except Exception:
			return None

	def compute_next_issue_date(category_value):
		base = timezone.now()
		cat = (category_value or '').lower()
		if cat in ('tshirt', 'jeans', 'formals'):
			days = 365
		elif cat == 'safety_shoes':
			days = 365 + 90
		elif cat in ('goggles', ''):
			days = 180
		elif cat == 'trainee':
			days = 180
		else:
			days = 365
		return base + timezone.timedelta(days=days)

	try:
		issued_quantity = int(issued_quantity) if issued_quantity not in (None, '') else 0
	except Exception:
		issued_quantity = 0

	if issue_id:
		try:
			issue = models.EmployeeIssue.objects.filter(pk=issue_id).first()
		except Exception:
			issue = None
		if issue:
			old_cat = issue.Category
			old_sub = issue.Subcategory
			old_size = issue.size
			old_qty = int(issue.Issued_quantity or 0)
			issue.emp_id = emp_id or issue.emp_id
			issue.name = name or issue.name
			issue.email = email or issue.email
			issue.gender = gender or issue.gender
			issue.entity = entity or issue.entity
			if category:
				issue.Category = category
			if subcategory:
				issue.Subcategory = subcategory
			if size:
				issue.size = size
			issue.Issued_quantity = issued_quantity
			issue.issued_date = timezone.now()
			is_buy_flag = bool(request.POST.get('Buy') or request.POST.get('buy'))
			issue.Buy = ('extra' if is_buy_flag else '')
			if is_buy_flag:
				buy_price = request.POST.get('buy_price') or request.POST.get('price') or 0
				try:
					issue.buy_price = float(buy_price) if buy_price else None
				except (ValueError, TypeError):
					issue.buy_price = None
			else:
				issue.buy_price = None
			next_cat = category or issue.Category
			issue.Next_issue_date = None if is_buy_flag else compute_next_issue_date(next_cat)
			issue.save()
			try:
				new_cat = issue.Category or ''
				new_sub = issue.Subcategory or ''
				new_size = issue.size or ''
				new_qty = int(issue.Issued_quantity or 0)
				new_entity = entity or ''
				
				if (old_cat or old_sub or old_size) and (old_cat != new_cat or old_sub != new_sub or old_size != new_size):
					old_entity = getattr(issue, 'entity', '') or ''
					adjust_inventory(old_cat, old_sub, old_size, -old_qty, old_entity)
					
					if check_inventory(new_cat, new_sub, new_size, new_qty, new_entity):
						ok = adjust_inventory(new_cat, new_sub, new_size, new_qty, new_entity)
						if not ok:
							messages.warning(request, f'Stock adjustment failed for updated issue: {new_cat} {new_sub} {new_size}')
					else:
						available = get_available_quantity(new_cat, new_sub, new_size, new_entity)
						entity_info = f" in {new_entity}" if new_entity else ""
						messages.error(request, f'Not enough stock to change issue to {new_cat} {new_sub} {new_size}{entity_info}. Required: {new_qty}, Available: {available}.')
						issue.Category = old_cat
						issue.Subcategory = old_sub
						issue.size = old_size
						issue.Issued_quantity = old_qty
						issue.save()
						adjust_inventory(old_cat, old_sub, old_size, old_qty, old_entity)
						return redirect('employee_issue_items')
				else:
					delta = new_qty - old_qty
					if delta != 0:
						if delta > 0:  
							if not check_inventory(new_cat, new_sub, new_size, delta, new_entity):
								available = get_available_quantity(new_cat, new_sub, new_size, new_entity)
								entity_info = f" in {new_entity}" if new_entity else ""
								messages.error(request, f'Not enough stock to increase quantity for {new_cat} {new_sub} {new_size}{entity_info}. Additional required: {delta}, Available: {available}.')
								issue.Issued_quantity = old_qty
								issue.save()
								return redirect('employee_issue_items')
							else:
								ok = adjust_inventory(new_cat, new_sub, new_size, delta, new_entity)
								if not ok:
									messages.warning(request, f'Stock adjustment failed for quantity increase: {new_cat} {new_sub} {new_size}')
						else:  
							ok = adjust_inventory(new_cat, new_sub, new_size, delta, new_entity)
							if not ok:
								messages.warning(request, f'Stock adjustment failed for quantity decrease: {new_cat} {new_sub} {new_size}')
			except Exception as e:
				messages.error(request, f'Error updating issue stock: {str(e)}')
			messages.success(request, 'Issue updated successfully.')
		else:
			messages.error(request, 'Issue not found to update.')
	else:
		if multi_issues_json:
			try:
				items = json.loads(multi_issues_json)
			except Exception:
				items = []
			created = 0
			for it in items:
				try:
					req_qty = int(it.get('Issued_quantity') or 0)
					cat_it = it.get('Category') or ''
					sub_it = it.get('Subcategory') or it.get('subcategory') or ''
					size_it = it.get('size') or ''
					is_buy = bool(it.get('Buy') or it.get('buy'))
					try:
						if emp_id and not is_buy:
							prior = models.EmployeeIssue.objects.filter(emp_id=str(emp_id).strip())
							if cat_it:
								prior = prior.filter(Category__iexact=cat_it)
							if sub_it:
								prior = prior.filter(Subcategory__iexact=sub_it)
							if prior.exists():
								emp_rec = None
								try:
									emp_rec = models.EmployeeDetails.objects.filter(emp_id=str(emp_id).strip()).first()
								except Exception:
									emp_rec = models.EmployeeDetails.objects.filter(emp_id=str(emp_id).strip()).first()
								emp_info = emp_id
								if emp_rec:
									name = getattr(emp_rec, 'emp_name', None) or getattr(emp_rec, 'name', None)
									email = getattr(emp_rec, 'emp_email', None) or getattr(emp_rec, 'email', None)
									if name and email:
										emp_info = f"{emp_id} - {name} ({email})"
									elif name:
										emp_info = f"{emp_id} - {name}"
									elif gender:
										emp_info += f" - {gender}"
										if entity:
											emp_info += f" - {entity}"
								messages.error(request, f'Employee {emp_info} already has an issue for {cat_it} {sub_it}. Not issued')
								continue
					except Exception:
						pass
					next_dt = latest_next_issue_datetime(emp_id or '', cat_it, sub_it, size_it)
					if not is_buy:
						try:
							blocked = bool(next_dt and timezone.now() < next_dt)
						except TypeError:
							blocked = bool(next_dt and timezone.now().date() < next_dt)
					else:
						blocked = False
					if blocked:
						try:
							next_str = next_dt.isoformat()
						except Exception:
							next_str = str(next_dt)
						messages.error(request, f'Already issued: {cat_it} {sub_it} size {size_it}. Next issue date: {next_str}. ')
						continue
					if not is_buy:
						if not check_inventory(cat_it, sub_it, size_it, req_qty, entity or ''):
							available = get_available_quantity(cat_it, sub_it, size_it, entity or '')
							entity_info = f" in {entity}" if entity else ""
							messages.error(request, f'Not enough stock for {cat_it} {sub_it} size {size_it}{entity_info}. Required: {req_qty}, Available: {available}. Issue not created.')
							continue
					buy_price_value = None
					if is_buy:
						price = it.get('buy_price') or it.get('price') or 0
						try:
							buy_price_value = float(price) if price else None
						except (ValueError, TypeError):
							buy_price_value = None
					
					models.EmployeeIssue.objects.create(
						emp_id=emp_id or '',
						name=name or '',
						email=email or '',
						gender=gender or '',
						entity=entity or '',
						Category=cat_it,
						Subcategory=sub_it,
						size=size_it,
						Issued_quantity=req_qty,
						issued_date=timezone.now(),
						Next_issue_date=(None if (it.get('Buy') or it.get('buy')) else compute_next_issue_date(cat_it)),
						Buy=('extra' if it.get('Buy') or it.get('buy') else ''),
						buy_price=buy_price_value,
						employee=(EmployeeDetails.objects.filter(emp_id__iexact=str(emp_id).strip()).first() if emp_id else None)
					)
					created += 1
					try:
						if not is_buy:
							ok = adjust_inventory(cat_it, sub_it, size_it, req_qty, entity or '')
							if not ok:
								messages.warning(request, f'Stock adjustment failed for {cat_it} {sub_it} size {size_it} in entity {entity or "default"}.')
					except Exception as e:
						if not is_buy:
							messages.warning(request, f'Stock adjustment error for {cat_it} {sub_it} size {size_it}: {str(e)}')
				except Exception:
					pass
			messages.success(request, f'Created {created} issue(s).')
		else:
			next_dt_single = latest_next_issue_datetime(emp_id or '', category or '', subcategory or '', size or '')
			is_single_buy = bool(request.POST.get('Buy') or request.POST.get('buy'))
			if not is_single_buy:
				try:
					blocked_single = bool(next_dt_single and timezone.now() < next_dt_single)
				except TypeError:
					blocked_single = bool(next_dt_single and timezone.now().date() < next_dt_single)
			else:
				blocked_single = False
			if blocked_single:
				try:
					next_str = next_dt_single.isoformat()
				except Exception:
					next_str = str(next_dt_single)
				messages.error(request, f'Already issued: {category} {subcategory} size {size}. Next issue date: {next_str}.')
				return redirect('employee_issue_items')
			else:
				try:
					if emp_id and not is_single_buy:
						prior_qs = models.EmployeeIssue.objects.filter(emp_id=str(emp_id).strip())
						if category:
							prior_qs = prior_qs.filter(Category__iexact=category)
						if subcategory:
							prior_qs = prior_qs.filter(Subcategory__iexact=subcategory)
						if prior_qs.exists():
							emp_rec = None
							try:
								emp_rec = models.EmployeeDetails.objects.filter(emp_id=str(emp_id).strip()).first()
							except Exception:
								emp_rec = None
							emp_info = emp_id
							if emp_rec:
								name = getattr(emp_rec, 'emp_name', None) or getattr(emp_rec, 'name', None)
								email = getattr(emp_rec, 'emp_email', None) or getattr(emp_rec, 'email', None)
								if name and email:
									emp_info = f"{emp_id} - {name} ({email})"
								elif name:
									emp_info = f"{emp_id} - {name}"
								elif entity: 
									emp_info += f" - {entity}"
							
							messages.error(request, f'Employee {emp_info} already has an issue for {category} {subcategory}. Not issued.')
							return redirect('employee_issue_items')
				except Exception:
					pass

				try:
					req_qty = int(issued_quantity or 0)
				except Exception:
					req_qty = 0
				if req_qty <= 0:
					messages.error(request, 'Requested quantity must be greater than zero. Not issued.')
					return redirect('employee_issue_items')

				if not is_single_buy and not check_inventory(category or '', subcategory or '', size or '', req_qty, entity or ''):
					available = get_available_quantity(category or '', subcategory or '', size or '', entity or '')
					entity_info = f" in {entity}" if entity else ""
					messages.error(request, f'Not enough stock for {category} {subcategory} size {size}{entity_info}. Required: {req_qty}, Available: {available}. Issue not created.')
					return redirect('employee_issue_items')
				else:
					buy_price_single = None
					if is_single_buy:
						price = request.POST.get('buy_price') or request.POST.get('price') or 0
						try:
							buy_price_single = float(price) if price else None
						except (ValueError, TypeError):
							buy_price_single = None
					
					new_issue = models.EmployeeIssue.objects.create(
						emp_id=emp_id or '',
						name=name or '',
						email=email or '',
						gender=gender or '',
						entity=entity or '',
						Category=category or '',
						Subcategory=subcategory or '',
						size=size or '',
						Issued_quantity=issued_quantity or 0,
						issued_date=timezone.now(),
						Next_issue_date=(None if is_single_buy else compute_next_issue_date(category or '')),
						Buy=('extra' if (request.POST.get('Buy') or request.POST.get('buy')) else ''),
						buy_price=buy_price_single,
						employee=(EmployeeDetails.objects.filter(emp_id__iexact=str(emp_id).strip()).first() if emp_id else None)
					)
					if not is_single_buy:
						try:
							ok = adjust_inventory(category or '', subcategory or '', size or '', int(issued_quantity or 0), entity or '')
							if not ok:
								messages.warning(request, f'Stock adjustment failed for {category} {subcategory} size {size} in entity {entity}. Issue created but stock not updated.')
						except Exception as e:
							messages.warning(request, f'Stock adjustment error for {category} {subcategory} size {size}: {str(e)}')
					
					messages.success(request, 'Issue created successfully.')
	return redirect('employee_issue_items')


@login_required
def check_stock_availability(request):
	
	try:
		entity = request.GET.get('entity') or ''
		category = request.GET.get('category') or ''
		subcategory = request.GET.get('subcategory') or ''
		size = request.GET.get('size') or ''
		qty = request.GET.get('quantity') or request.GET.get('qty') or 0
		try:
			qty = int(qty)
		except Exception:
			qty = 0

		filters = {}
		if category:
			filters['item_type__iexact'] = category
		if subcategory:
			filters['color__iexact'] = subcategory
		if size:
			filters['size__iexact'] = size
		if entity:
			filters['entity__iexact'] = entity

		inv = Inventory.objects.filter(**filters).first()
		if not inv and entity:
			fallback_filters = {k: v for k, v in filters.items() if k != 'entity__iexact'}
			inv = Inventory.objects.filter(**fallback_filters).first()

		if not inv:
			qs = Inventory.objects.all()
			if category:
				qs = qs.filter(item_type__iexact=category)
			if entity:
				qs = qs.filter(entity__iexact=entity)
			if subcategory:
				s_token = subcategory.strip()
				qs = qs.filter(Q(color__icontains=s_token) | Q(color__iexact=s_token) | Q(item_type__icontains=s_token) | Q(item_type__iexact=s_token))
			if size:
				qs = qs.filter(size__iexact=size)
			stock_count = int(qs.aggregate(total=Sum('quantity'))['total'] or 0)
		else:
			stock_count = int(inv.quantity or 0)

		available = stock_count >= qty
		return JsonResponse({'available': available, 'stock_count': stock_count})
	except Exception as e:
		return JsonResponse({'available': False, 'stock_count': 0, 'error': str(e)}, status=500)

def issue_items_view(request, category):
	valid_categories = ['formals', 'tshirt', 'jeans', 'safety_shoes', 'goggles', 'trainee', ]
	if category not in valid_categories:
		return HttpResponseNotAllowed(['GET'], "Invalid category")
	EmployeeIssues = models.EmployeeIssue.objects.all()
	return render(request, 'inventory/issue_items.html', {'category': category, 'EmployeeIssues': EmployeeIssues})

@login_required
def forecast_next_issues(request):
	# Both admin and staff can view forecast data
	try:
		from django.utils import timezone
		import datetime
		from .models import Category_Choices

		now = timezone.now().date()
		months = []
		for m in range(6):
			first = (now.replace(day=1) + datetime.timedelta(days=32*m)).replace(day=1)
			next_month = (first + datetime.timedelta(days=32)).replace(day=1)
			last = next_month - datetime.timedelta(days=1)
			months.append((first, last))

		data = []
		categories = [c[0] for c in Category_Choices]
		for start, end in months:
			qs = models.EmployeeIssue.objects.filter(Next_issue_date__gte=start, Next_issue_date__lte=end)
			total = qs.count()
			by_cat_qs = qs.values('Category').annotate(c=Count('id'))
			by_cat = {c: 0 for c in categories}
			for row in by_cat_qs:
				k = row.get('Category') or ''
				if k in by_cat:
					by_cat[k] = int(row.get('c') or 0)
				else:
					by_cat[k] = int(row.get('c') or 0)

			data.append({ 'label': start.strftime('%b %Y'), 'start': str(start), 'end': str(end), 'total': int(total), 'by_category': by_cat })

		return JsonResponse({'months': data})
	except Exception as e:
		return JsonResponse({'months': [], 'error': str(e)}, status=500)

@login_required
def forecast_month_details(request, start):
	# Both admin and staff can view forecast month details
	try:
		import datetime

		try:
			start_date = datetime.date.fromisoformat(start)
		except Exception:
			return JsonResponse({'items': []})

		next_month = (start_date.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
		last = next_month - datetime.timedelta(days=1)

		qs = models.EmployeeIssue.objects.filter(Next_issue_date__gte=start_date, Next_issue_date__lte=last).order_by('-Next_issue_date', '-issued_date')
		items = []
		for i in qs:
			items.append({
				'id': i.id,
				'emp_id': i.emp_id,
				'name': i.name,
				'email': i.email,
				'gender': i.gender,
				'entity': i.entity,
				'Category': i.Category,
				'Subcategory': i.Subcategory,
				'size': i.size,
				'Issued_quantity': int(i.Issued_quantity or 0),
				'issued_date': i.issued_date.isoformat() if getattr(i, 'issued_date', None) else None,
				'Next_issue_date': i.Next_issue_date.isoformat() if getattr(i, 'Next_issue_date', None) else None,
			})
		return JsonResponse({'items': items})
	except Exception:
		return JsonResponse({'items': []})


def search_issues(request):
	try:
		q = (request.GET.get('q') or '').strip()
		if not q:
			return JsonResponse({'items': []})

		exact_qs = models.EmployeeIssue.objects.filter(emp_id__iexact=q).order_by('-issued_date')
		if exact_qs.exists():
			qs = exact_qs
		else:
			qs = models.EmployeeIssue.objects.filter(
				Q(emp_id__icontains=q) | Q(name__icontains=q) | Q(email__icontains=q)
			).order_by('-issued_date')[:200]

		items = []
		for i in qs:
			items.append({
				'id': i.id,
				'emp_id': i.emp_id,
				'name': i.name,
				'email': i.email,
				'gender': i.gender,
				'entity': i.entity,
				'Category': i.Category,
				'Subcategory': i.Subcategory,
				'size': i.size,
				'Issued_quantity': int(i.Issued_quantity or 0),
				'issued_date': i.issued_date.isoformat() if getattr(i, 'issued_date', None) else None,
				'Next_issue_date': i.Next_issue_date.isoformat() if getattr(i, 'Next_issue_date', None) else None,
				'Buy': i.Buy or '',
			})
		return JsonResponse({'items': items})
	except Exception:
		return JsonResponse({'items': []})

def check_issue_block(request):
	try:
		emp_id = (request.GET.get('emp_id') or request.GET.get('empId') or '').strip()
		category = (request.GET.get('Category') or request.GET.get('category') or '').strip()
		sub = (request.GET.get('Subcategory') or request.GET.get('sub') or '').strip()
		size = (request.GET.get('size') or '').strip()
		if not emp_id:
			return JsonResponse({'blocked': False, 'next_issue_date': None})
		q = models.EmployeeIssue.objects.filter(emp_id=str(emp_id).strip())
		if category:
			q = q.filter(Category__iexact=category)
		if sub:
			q = q.filter(Subcategory__iexact=sub)
		if size:
			q = q.filter(size__iexact=size)
		q = q.order_by('-issued_date').first()
		if not q:
			return JsonResponse({'blocked': False, 'next_issue_date': None})
		next_dt = getattr(q, 'Next_issue_date', None)
		if not next_dt:
			return JsonResponse({'blocked': False, 'next_issue_date': None})
		try:
			blocked = bool(next_dt and timezone.now() < next_dt)
		except TypeError:
			blocked = bool(next_dt and timezone.now().date() < next_dt)
		try:
			nd = next_dt.isoformat()
		except Exception:
			nd = str(next_dt)
		return JsonResponse({'blocked': bool(blocked), 'next_issue_date': nd})
	except Exception:
		return JsonResponse({'blocked': False, 'next_issue_date': None})


from django.shortcuts import render
from .models import EmployeeDetails

def employee_list(request):
	employees = EmployeeDetails.objects.all()
	return render(request, "employee_details", {"employees": employees})

def get_employeedetails(request, emp_id):
	try:
		emp = EmployeeDetails.objects.filter(emp_id__iexact=str(emp_id).strip()).first()
	except Exception:
		emp = None
	if not emp:
		return JsonResponse({'error': 'Employee not found'}, status=404)

	return JsonResponse({
		'emp_id': emp.emp_id,
		'emp_name': emp.emp_name,
		'emp_email': emp.emp_email,
		'emp_gender': emp.gender,
		'emp_entity': emp.entity,
	})

from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class InventoryViewSet(viewsets.ModelViewSet):
	queryset = Inventory.objects.all().order_by('-updated_at')
	serializer_class = InventorySerializer
	permission_classes = [AllowAny]
	
	def get_authenticators(self):
		"""
		Remove SessionAuthentication for this viewset to avoid CSRF issues
		"""
		if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
			return []
		return super().get_authenticators()

	def create(self, request, *args, **kwargs):
		data = request.data
		item_type = data.get('item_type')
		color = data.get('color') or data.get('color_or_type') or ''
		size = data.get('size') or ''

		try:
			quantity = int(data.get('quantity') or 0)
		except (TypeError, ValueError):
			return Response({'detail': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

		if not item_type:
			return Response({'detail': 'item_type is required'}, status=status.HTTP_400_BAD_REQUEST)

		entity = (data.get('entity') or '').strip()

		existing_qs = Inventory.objects.filter(
			item_type__iexact=item_type,
			color__iexact=color,
			size__iexact=size,
		)
		if entity:
			existing_qs = existing_qs.filter(entity__iexact=entity)
		existing = existing_qs.first()

		if existing:
			existing.quantity = (existing.quantity or 0) + quantity
			existing.save()
			serializer = self.get_serializer(existing)
			return Response(serializer.data, status=status.HTTP_200_OK)

		# create new
		payload = dict(request.data)
		if entity:
			payload['entity'] = entity
		serializer = self.get_serializer(data=payload)
		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		headers = self.get_success_headers(serializer.data)
		return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime
import csv
from .models import EmployeeIssue



@login_required
def download_employee_issue_report(request):
	# Admin-only access for downloading reports
	try:
		if hasattr(request.user, 'profile') and request.user.profile.role != 'admin':
			return HttpResponse('Permission denied', status=403)
	except Exception:
		return HttpResponse('Permission denied', status=403)
	
	start_date_str = request.GET.get('start')
	end_date_str = request.GET.get('end')

	if not start_date_str or not end_date_str:
		return HttpResponse("Start date and end date are required.", status=400)

	try:
		start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
		end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
	except ValueError:
		return HttpResponse("Invalid date format.", status=400)

	issues = EmployeeIssue.objects.filter(issued_date__range=(start_date, end_date))

	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="employee_issue_report_{start_date}_{end_date}.csv"'

	writer = csv.writer(response)
	writer.writerow(['Employee ID', 'Employee Name', 'Entity', 'Category', 'Subcategory', 'Size', 'Quantity', 'Issued Date', 'Buy Price'])

	for issue in issues:
		emp_id_out = getattr(issue, 'emp_id', '')
		emp_name_out = getattr(issue, 'name', '')
		entity_out = getattr(issue, 'entity', '')
		category_out = getattr(issue, 'Category', '')
		sub_out = getattr(issue, 'Subcategory', '')
		size_out = getattr(issue, 'size', '')
		qty_out = int(getattr(issue, 'Issued_quantity', 0) or 0)
		issued_dt = getattr(issue, 'issued_date', None)
		issued_str = issued_dt.strftime("%Y-%m-%d") if issued_dt else ''
		buy_price_out = getattr(issue, 'buy_price', None)
		buy_price_str = f"₹{buy_price_out}" if buy_price_out else ''
		writer.writerow([emp_id_out, emp_name_out, entity_out, category_out, sub_out, size_out, qty_out, issued_str, buy_price_str])

	return response

@login_required
def download_employee_due_report(request):
	try:
		if hasattr(request.user, 'profile') and request.user.profile.role != 'admin':
			return HttpResponse('Permission denied', status=403)
	except Exception:
		return HttpResponse('Permission denied', status=403)
	
	today = datetime.today().date()
	issues = EmployeeIssue.objects.filter(Next_issue_date__lte=today).order_by('Next_issue_date')

	if not issues.exists():
		return HttpResponse("No due issues found.", status=404)

	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = f'attachment; filename="employee_due_report_{today}.csv"'

	writer = csv.writer(response)
	writer.writerow(['Employee ID', 'Employee Name', 'Entity', 'Category', 'Subcategory', 'Size', 'Quantity', 'Issued Date', 'Next Issue Date', 'Buy Price'])

	for issue in issues:
		emp_id_out = getattr(issue, 'emp_id', '')
		emp_name_out = getattr(issue, 'name', '')
		entity_out = getattr(issue, 'entity', '')
		category_out = getattr(issue, 'Category', '')
		sub_out = getattr(issue, 'Subcategory', '')
		size_out = getattr(issue, 'size', '')
		qty_out = int(getattr(issue, 'Issued_quantity', 0) or 0)
		issued_dt = getattr(issue, 'issued_date', None)
		issued_str = issued_dt.strftime("%Y-%m-%d") if issued_dt else ''
		next_dt = getattr(issue, 'Next_issue_date', None)
		next_str = next_dt.strftime("%Y-%m-%d") if next_dt else ''
		buy_price_out = getattr(issue, 'buy_price', None)
		buy_price_str = f"₹{buy_price_out}" if buy_price_out else ''
		writer.writerow([emp_id_out, emp_name_out, entity_out, category_out, sub_out, size_out, qty_out, issued_str, next_str, buy_price_str])

	return response


@login_required
def forecast_details_api(request):
	"""API endpoint for detailed forecast data with filtering - Admin only"""
	# Admin-only access
	try:
		if hasattr(request.user, 'profile') and request.user.profile.role != 'admin':
			return JsonResponse({'error': 'Permission denied'}, status=403)
	except Exception:
		return JsonResponse({'error': 'Permission denied'}, status=403)
	
	try:
		import datetime
		from django.db.models import Sum, Count
		
		today = datetime.date.today()
		filter_type = request.GET.get('type', 'category')  # category, entity, size
		filter_value = request.GET.get('value', '')
		months = int(request.GET.get('months', 6))
		
		forecast_data = []
		
		for m in range(months):
			first = (today.replace(day=1) + datetime.timedelta(days=32*m)).replace(day=1)
			next_month = (first + datetime.timedelta(days=32)).replace(day=1)
			last = next_month - datetime.timedelta(days=1)
			
			# Base query for this month
			qs = models.EmployeeIssue.objects.filter(Next_issue_date__gte=first, Next_issue_date__lte=last)
			
			# Apply filter if specified
			if filter_type == 'category' and filter_value:
				qs = qs.filter(Category__iexact=filter_value)
			elif filter_type == 'entity' and filter_value:
				qs = qs.filter(entity__iexact=filter_value)
			elif filter_type == 'size' and filter_value:
				qs = qs.filter(size__iexact=filter_value)
			
			# Get detailed breakdown
			total_qty = int(qs.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
			total_count = qs.count()
			
			# Get breakdown by different dimensions
			by_category = list(qs.values('Category').annotate(
				qty=Sum('Issued_quantity'), 
				count=Count('id')
			).order_by('-qty'))
			
			by_entity = list(qs.values('entity').annotate(
				qty=Sum('Issued_quantity'), 
				count=Count('id')
			).order_by('-qty'))
			
			by_size = list(qs.values('size').annotate(
				qty=Sum('Issued_quantity'), 
				count=Count('id')
			).order_by('-qty'))
			
			forecast_data.append({
				'month': first.strftime('%b %Y'),
				'start_date': first.isoformat(),
				'end_date': last.isoformat(),
				'total_quantity': total_qty,
				'total_employees': total_count,
				'by_category': by_category,
				'by_entity': by_entity,
				'by_size': by_size
			})
		
		return JsonResponse({
			'success': True,
			'filter_type': filter_type,
			'filter_value': filter_value,
			'months': months,
			'forecast_data': forecast_data
		})
		
	except Exception as e:
		return JsonResponse({
			'success': False,
			'error': str(e)
		})

def forecast_summary_api(request):
	"""API endpoint for forecast summary statistics"""
	try:
		import datetime
		from django.db.models import Sum, Count, Q
		
		today = datetime.date.today()
		months = int(request.GET.get('months', 6))
		
		# Calculate totals for next N months
		future_start = today.replace(day=1)
		future_end = (future_start + datetime.timedelta(days=32*months)).replace(day=1) - datetime.timedelta(days=1)
		
		future_issues = models.EmployeeIssue.objects.filter(
			Next_issue_date__gte=future_start, 
			Next_issue_date__lte=future_end
		)
		
		summary = {
			'total_forecast_quantity': int(future_issues.aggregate(s=Sum('Issued_quantity'))['s'] or 0),
			'total_forecast_employees': future_issues.count(),
			'categories_breakdown': list(future_issues.values('Category').annotate(
				qty=Sum('Issued_quantity'), 
				count=Count('id')
			).order_by('-qty')[:10]),
			'entities_breakdown': list(future_issues.values('entity').annotate(
				qty=Sum('Issued_quantity'), 
				count=Count('id')
			).order_by('-qty')[:10]),
			'sizes_breakdown': list(future_issues.values('size').annotate(
				qty=Sum('Issued_quantity'), 
				count=Count('id')
			).order_by('-qty')[:10]),
			'monthly_totals': [],
		}
		
		# Calculate monthly totals
		for m in range(months):
			first = (today.replace(day=1) + datetime.timedelta(days=32*m)).replace(day=1)
			next_month = (first + datetime.timedelta(days=32)).replace(day=1)
			last = next_month - datetime.timedelta(days=1)
			
			month_qs = models.EmployeeIssue.objects.filter(Next_issue_date__gte=first, Next_issue_date__lte=last)
			month_qty = int(month_qs.aggregate(s=Sum('Issued_quantity'))['s'] or 0)
			
			summary['monthly_totals'].append({
				'month': first.strftime('%b %Y'),
				'quantity': month_qty,
				'employees': month_qs.count()
			})
		
		return JsonResponse({
			'success': True,
			'summary': summary
		})
		
	except Exception as e:
		return JsonResponse({
			'success': False,
			'error': str(e)
		})


def issue_report_json(request):
	"""Return JSON list of EmployeeIssue items for an issued_date range.

	Query params: start=YYYY-MM-DD, end=YYYY-MM-DD
	"""
	try:
		from datetime import datetime
		start = request.GET.get('start')
		end = request.GET.get('end')
		
		print(f"DEBUG: issue_report_json called with start={start}, end={end}")
		
		if not start or not end:
			print("DEBUG: Missing start or end date")
			return JsonResponse({'items': [], 'debug': 'missing_dates'})
		
		try:
			start_date = datetime.fromisoformat(start).date()
			end_date = datetime.fromisoformat(end).date()
			print(f"DEBUG: Parsed dates - start_date={start_date}, end_date={end_date}")
		except Exception as e:
			print(f"DEBUG: Date parsing error: {e}")
			return JsonResponse({'items': [], 'debug': f'date_parse_error: {e}'})

		# Check how many issues have issued_date in range
		qs = models.EmployeeIssue.objects.filter(issued_date__gte=start_date, issued_date__lte=end_date).order_by('-issued_date')
		count_in_range = qs.count()
		print(f"DEBUG: Issues with issued_date in range {start_date} to {end_date}: {count_in_range}")
		
		# If no results, check what issued_dates we do have
		if count_in_range == 0:
			sample_issued_dates = models.EmployeeIssue.objects.all().values_list('issued_date', flat=True)[:10]
			print(f"DEBUG: Sample issued_dates in DB: {list(sample_issued_dates)}")
		
		items = []
		for i in qs:
			items.append({
				'id': i.id,
				'emp_id': i.emp_id,
				'name': i.name,
				'email': i.email,
				'entity': i.entity,
				'Category': i.Category,
				'Subcategory': i.Subcategory,
				'size': i.size,
				'Issued_quantity': int(i.Issued_quantity or 0),
				'issued_date': i.issued_date.isoformat() if getattr(i, 'issued_date', None) else None,
				'Next_issue_date': i.Next_issue_date.isoformat() if getattr(i, 'Next_issue_date', None) else None,
				'Buy': i.Buy or '',
				'buy_price': float(i.buy_price) if getattr(i, 'buy_price', None) else None,
			})
		
		print(f"DEBUG: Returning {len(items)} items")
		return JsonResponse({'items': items, 'debug': f'found_{len(items)}_items'})
	except Exception as e:
		print(f"DEBUG: Exception in issue_report_json: {e}")
		return JsonResponse({'items': [], 'debug': f'exception: {str(e)}'})


def due_report_json(request):
	
	try:
		from datetime import datetime
		start = request.GET.get('start')
		end = request.GET.get('end')
		
		# Debug: Let's see what we're getting
		print(f"DEBUG: due_report_json called with start={start}, end={end}")
		
		if not start or not end:
			print("DEBUG: Missing start or end date")
			return JsonResponse({'items': [], 'debug': 'missing_dates'})
		
		try:
			start_date = datetime.fromisoformat(start).date()
			end_date = datetime.fromisoformat(end).date()
			print(f"DEBUG: Parsed dates - start_date={start_date}, end_date={end_date}")
		except Exception as e:
			print(f"DEBUG: Date parsing error: {e}")
			return JsonResponse({'items': [], 'debug': f'date_parse_error: {e}'})

		# First, let's see how many total issues we have
		total_issues = models.EmployeeIssue.objects.all().count()
		print(f"DEBUG: Total EmployeeIssue records: {total_issues}")
		
		# Check how many have Next_issue_date set
		issues_with_next_date = models.EmployeeIssue.objects.filter(Next_issue_date__isnull=False).count()
		print(f"DEBUG: Issues with Next_issue_date: {issues_with_next_date}")
		
		# Check date range
		qs = models.EmployeeIssue.objects.filter(Next_issue_date__gte=start_date, Next_issue_date__lte=end_date).order_by('Next_issue_date')
		count_in_range = qs.count()
		print(f"DEBUG: Issues in date range {start_date} to {end_date}: {count_in_range}")
		
		if count_in_range == 0:
			sample_dates = models.EmployeeIssue.objects.filter(Next_issue_date__isnull=False).values_list('Next_issue_date', flat=True)[:10]
			print(f"DEBUG: Sample Next_issue_dates in DB: {list(sample_dates)}")
		
		items = []
		for i in qs:
			items.append({
				'id': i.id,
				'emp_id': i.emp_id,
				'name': i.name,
				'email': i.email,
				'entity': i.entity,
				'Category': i.Category,
				'Subcategory': i.Subcategory,
				'size': i.size,
				'Issued_quantity': int(i.Issued_quantity or 0),
				'issued_date': i.issued_date.isoformat() if getattr(i, 'issued_date', None) else None,
				'Next_issue_date': i.Next_issue_date.isoformat() if getattr(i, 'Next_issue_date', None) else None,
				'Buy': i.Buy or '',
				'buy_price': float(i.buy_price) if getattr(i, 'buy_price', None) else None,
			})
		
		print(f"DEBUG: Returning {len(items)} items")
		return JsonResponse({'items': items, 'debug': f'found_{len(items)}_items'})
	except Exception as e:
		print(f"DEBUG: Exception in due_report_json: {e}")
		return JsonResponse({'items': [], 'debug': f'exception: {str(e)}'})


def extra_report_json(request):
	"""Return JSON list of EmployeeIssue items for issued_date range where Buy='extra'.

	Query params: start=YYYY-MM-DD, end=YYYY-MM-DD
	"""
	try:
		from datetime import datetime
		start = request.GET.get('start')
		end = request.GET.get('end')
		
		print(f"DEBUG: extra_report_json called with start={start}, end={end}")
		
		if not start or not end:
			print("DEBUG: Missing start or end date")
			return JsonResponse({'items': [], 'debug': 'missing_dates'})
		
		try:
			start_date = datetime.fromisoformat(start).date()
			end_date = datetime.fromisoformat(end).date()
			print(f"DEBUG: Parsed dates - start_date={start_date}, end_date={end_date}")
		except Exception as e:
			print(f"DEBUG: Date parsing error: {e}")
			return JsonResponse({'items': [], 'debug': f'date_parse_error: {e}'})

		from django.db.models import Q
		qs = models.EmployeeIssue.objects.filter(
			Q(Buy__iexact='extra') |
			Q(Next_issue_date__gte=start_date, Next_issue_date__lte=end_date)
		).order_by('-issued_date')
		
		count_in_range = qs.count()
		print(f"DEBUG: Extra/Buy items in range: {count_in_range}")
		
		buy_extra_count = models.EmployeeIssue.objects.filter(Buy__iexact='extra').count()
		print(f"DEBUG: Total Buy='extra' items: {buy_extra_count}")
		
		items = []
		for i in qs:
			items.append({
				'id': i.id,
				'emp_id': i.emp_id,
				'name': i.name,
				'email': i.email,
				'entity': i.entity,
				'Category': i.Category,
				'Subcategory': i.Subcategory,
				'size': i.size,
				'Issued_quantity': int(i.Issued_quantity or 0),
				'issued_date': i.issued_date.isoformat() if getattr(i, 'issued_date', None) else None,
				'Next_issue_date': i.Next_issue_date.isoformat() if getattr(i, 'Next_issue_date', None) else None,
				'Buy': i.Buy or '',
				'buy_price': float(i.buy_price) if getattr(i, 'buy_price', None) else None,
			})
		
		print(f"DEBUG: Returning {len(items)} items")
		return JsonResponse({'items': items, 'debug': f'found_{len(items)}_items'})
	except Exception as e:
		print(f"DEBUG: Exception in extra_report_json: {e}")
		return JsonResponse({'items': [], 'debug': f'exception: {str(e)}'})


def update_issue_ajax(request):
	"""AJAX-friendly endpoint to update an existing EmployeeIssue record.

	Expects POST with issue_id and any updatable fields. Returns JSON.
	"""
	try:
		if request.method != 'POST':
			return JsonResponse({'error': 'POST required'}, status=405)
		from datetime import datetime
		issue_id = request.POST.get('issue_id') or request.POST.get('id')
		if not issue_id:
			return JsonResponse({'error': 'issue_id required'}, status=400)
		issue = models.EmployeeIssue.objects.filter(pk=issue_id).first()
		if not issue:
			return JsonResponse({'error': 'Issue not found'}, status=404)

		for field in ('emp_id', 'name', 'email','entity', 'Category', 'Subcategory', 'size', 'Buy'):
			v = request.POST.get(field)
			if v is not None:
				setattr(issue, field if field != 'emp_id' else 'emp_id', v)

		# quantity
		qv = request.POST.get('Issued_quantity')
		if qv is not None and qv != '':
			try:
				issue.Issued_quantity = int(qv)
			except Exception:
				pass

		# buy_price
		buy_price = request.POST.get('buy_price')
		if buy_price is not None:
			if buy_price == '' or buy_price == '-':
				issue.buy_price = None
			else:
				try:
					issue.buy_price = float(buy_price)
				except (ValueError, TypeError):
					pass  # keep existing value if conversion fails

		# dates
		issued_date = request.POST.get('issued_date')
		if issued_date:
			try:
				issue.issued_date = datetime.fromisoformat(issued_date).date()
			except Exception:
				pass
		next_date = request.POST.get('Next_issue_date')
		if next_date == '':
			issue.Next_issue_date = None
		elif next_date:
			try:
				issue.Next_issue_date = datetime.fromisoformat(next_date).date()
			except Exception:
				pass

		issue.save()
		return JsonResponse({'ok': True, 'id': issue.id})
	except Exception:
		return JsonResponse({'ok': False})

from django.shortcuts import render, redirect
from .models import Stationary, StationaryType
def stationary(request):

	from .models import Stationary, StationaryType, EmployeeDetails
	items = Stationary.objects.all().order_by('-updated_at')
	types = StationaryType.objects.all().order_by('name')
	employees = EmployeeDetails.objects.all()
	issued_items = []
	try:
		from .models import StationaryIssue
		issued_items = StationaryIssue.objects.all().order_by('-id')[:50]
	except Exception:
		issued_items = []
	return render(request, 'stationary/stationary.html', {'items': items, 'types': types, 'employees': employees, 'issued_items': issued_items})
def stationary_inventory(request):
    items = Stationary.objects.all().order_by('-updated_at')
    types = StationaryType.objects.all()  
    return render(request, 'stationary.html', {'items': items, 'types': types})

from django.shortcuts import render, redirect
from .models import Stationary, StationaryType

def add_stationary_type(request):
	from .models import StationaryType, Stationary
	from django.http import JsonResponse
	import json
	
	if request.method == 'POST':
		name = request.POST.get('new_type')
		quantity = request.POST.get('quantity', 0)
		
		# Handle AJAX request
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
			if name:
				try:
					name = name.strip()
					stationary_type, created = StationaryType.objects.get_or_create(name=name)
					
					try:
						qty = int(quantity or 0)
					except:
						qty = 0
					
					if qty > 0:
						stationary_item, item_created = Stationary.objects.get_or_create(
							category=stationary_type,
							defaults={'quantity': qty}
						)
						if not item_created:
							stationary_item.quantity += qty
							stationary_item.save()
					else:
						stationary_item, item_created = Stationary.objects.get_or_create(
							category=stationary_type,
							defaults={'quantity': 0}
						)
					
					return JsonResponse({
						'success': True,
						'message': f'New item type "{name}" created successfully!',
						'new_item': {
							'id': stationary_item.id,
							'category_id': stationary_type.id,
							'category_name': stationary_type.name,
							'quantity': stationary_item.quantity,
							'updated_at': stationary_item.updated_at.strftime('%Y-%m-%d %H:%M')
						}
					})
				except Exception as e:
					return JsonResponse({
						'success': False,
						'message': f'Error creating item type: {str(e)}'
					})
			else:
				return JsonResponse({
					'success': False,
					'message': 'Item name is required'
				})
		
		if name:
			StationaryType.objects.get_or_create(name=name.strip())
	
	return redirect('stationary')

def add_stationary_item(request):
	from .models import Stationary, StationaryType
	from django.http import JsonResponse
	
	if request.method == 'POST':
		category_id = request.POST.get('category')
		quantity = request.POST.get('quantity')
		
		# Handle AJAX request
		if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
			try:
				q = int(quantity or 0)
			except Exception:
				q = 0
			
			if category_id and q > 0:
				try:
					category = StationaryType.objects.get(id=category_id)
					s = Stationary.objects.filter(category=category).first()
					if s:
						s.quantity = (s.quantity or 0) + q
						s.save()
						return JsonResponse({
							'success': True,
							'message': f'Added {q} units to {category.name}. Total: {s.quantity}',
							'updated_item': {
								'id': s.id,
								'category_id': category.id,
								'category_name': category.name,
								'quantity': s.quantity,
								'updated_at': s.updated_at.strftime('%Y-%m-%d %H:%M')
							}
						})
					else:
						s = Stationary.objects.create(category=category, quantity=q)
						return JsonResponse({
							'success': True,
							'message': f'Created new stock for {category.name} with {q} units',
							'new_item': {
								'id': s.id,
								'category_id': category.id,
								'category_name': category.name,
								'quantity': s.quantity,
								'updated_at': s.updated_at.strftime('%Y-%m-%d %H:%M')
							}
						})
				except StationaryType.DoesNotExist:
					return JsonResponse({
						'success': False,
						'message': 'Selected category does not exist'
					})
			else:
				return JsonResponse({
					'success': False,
					'message': 'Please select a category and enter a valid quantity'
				})
		
		try:
			q = int(quantity or 0)
		except Exception:
			q = 0
		if category_id and q > 0:
			try:
				category = StationaryType.objects.get(id=category_id)
				s = Stationary.objects.filter(category=category).first()
				if s:
					s.quantity = (s.quantity or 0) + q
					s.save()
				else:
					Stationary.objects.create(category=category, quantity=q)
			except StationaryType.DoesNotExist:
				pass
	return redirect('stationary')

def update_stationary_item(request, item_id):
	from .models import Stationary
	if request.method == 'POST':
		try:
			s = Stationary.objects.filter(pk=item_id).first()
			if s:
				qty = request.POST.get('quantity')
				try:
					s.quantity = int(qty or s.quantity)
					s.save()
				except Exception:
					pass
		except Exception:
			pass
	return redirect('stationary')

def submit_stationary_issue(request):
	"""Handle stationary issue form submission"""
	if request.method == 'POST':
		try:
			from .models import StationaryIssue, Stationary, EmployeeDetails
			
			emp_id = request.POST.get('empId')
			emp_name = request.POST.get('empName')
			emp_email = request.POST.get('empEmail')
			emp_gender = request.POST.get('empGender')
			emp_entity = request.POST.get('empEntity')
			stationary_id = request.POST.get('stationaryItem')
			quantity_issued = int(request.POST.get('quantityIssued', 0))
			issue_date = request.POST.get('issueDate')
			
			# Validate inputs
			if not all([emp_id, emp_name, stationary_id, quantity_issued]):
				messages.error(request, '❌ Please fill all required fields')
				return redirect('stationary')
			
			stationary_item = Stationary.objects.get(id=stationary_id)
			
			if stationary_item.quantity < quantity_issued:
				messages.error(request, f'❌ Not enough stock! Available: {stationary_item.quantity}, Requested: {quantity_issued}')
				return redirect('stationary')
			
			issue = StationaryIssue.objects.create(
				emp_id=emp_id,
				emp_name=emp_name,
				emp_email=emp_email or '',
				gender=emp_gender.lower() if emp_gender else 'male',
				entity=emp_entity or '',
				stationary=stationary_item,
				quantity=quantity_issued
			)
			
			# Reduce the stock
			stationary_item.quantity -= quantity_issued
			stationary_item.save()
			
			messages.success(request, f'✅ Successfully issued {quantity_issued} {stationary_item.category.name}(s) to {emp_name}')
			
		except Stationary.DoesNotExist:
			messages.error(request, '❌ Selected stationary item not found')
		except Exception as e:
			messages.error(request, f'❌ Error processing issue: {str(e)}')
	
	return redirect('stationary')

# create Profile model for User registration

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        role = request.POST['role']
        user = User.objects.create_user(username=username, password=password)
        user.profile.role = role
        user.profile.save()

        return redirect('sign.html')

    return render(request, 'admin/register.html')
