from django.db import models
from django.utils.timezone import now
from django.utils import timezone


Category_Choices = [
    ('formals', 'Formals'),
    ('tshirt', 'T-Shirt'),
    ('jeans', 'Jeans'),
    ('safety_shoes', 'Safety_Shoes'),
    ('goggles', 'Goggles'),
]
stock_choices = [
    ('in', 'In Stock'),
    ('out', 'Out of Stock'),
    ('low', 'Low Stock'),
    ('extra', 'Extra / Buy')
    ]
Subcategory_Choices = [
    ('black', 'Black'),
    ('white', 'White'),
    ('trainee', 'Trainee'),
    ('jeans', 'Jeans'),
    ('ladies', 'Ladies'),
    ('gents', 'Gents'),
    ('Grey_Shirt','Grey Shirt'),
    ('White_Shirt','White Shirt'),
    ('normal','Normal'),
    ('overhead','Overhead'),
]
size_Choices=[
  ('1','1'),
    ('2','2'),
    ('3','3'),
    ('4','4'),
    ('5','5'),
    ('6','6'),
    ('7','7'),
    ('8','8'),
    ('9','9'),
    ('10','10'),
    ('11','11'),
    ('12','12'),
    ('XS','XS'),
    ('S','S'),
    ('M','M'),
    ('L','L'),
    ('XL','XL'),
    ('2XL','2XL'),
    ('3XL','3XL'),
    ('4XL','4XL'),
    ('5XL','5XL'),
    ('28','28'),
    ('30','30'),
    ('32','32'),
    ('34','34'),
    ('36','36'),
    ('38','38'),
    ('40','40'),
    ('42','42'),
    ('44','44'),
    ('46','46'),
    ('48','48'),
    ('overhead','Overhead'),
    ('normal','Normal'),
]
checkbox_choices=[
    ('active','Active'),
    ('inactive','Inactive')
]
entity_choices= [
  ('AEQUS SEZ PRIVATE LIMITED','AEQUS SEZ PRIVATE LIMITED'),
   ('AEQUS ENGINEERED PLASTICS PRIVATE LIMITED','AEQUS ENGINEERED PLASTICS PRIVATE LIMITED'),
   ('AEQUS AUTOMOTIVE PRIVATE LIMITED','AEQUS AUTOMOTIVE PRIVATE LIMITED'),
   ('AEROSPACE PROCESSING INDIA PVT. LTD.','AEROSPACE PROCESSING INDIA PVT. LTD.'),
   ('AEROSTRUCTURES MANUFACTURING INDIA PRIVATE LIMITED','AEROSTRUCTURES MANUFACTURING INDIA PRIVATE LIMITED'),
   ('SQUAD FORGING INDIA PRIVATE LIMITED','SQUAD FORGING INDIA PRIVATE LIMITED'),
   ('AEQUS PRIVATE LIMITED','AEQUS PRIVATE LIMITED'),
   ('AEROSTRUCTURES ASSEMBLIES INDIA PVT. LTD','AEROSTRUCTURES ASSEMBLIES INDIA PVT. LTD'),
   ('AEQUS FORCE CONSUMER PRODUCT PRIVATE LIMITED','AEQUS FORCE CONSUMER PRODUCT PRIVATE LIMITED'),


]
location_choices=[
    ('Hubli','hubli'),
    ('Belagavi','belagavi'),
    ('Koppal','koppal')
]
# stockmodel
class Inventory(models.Model):
    entity = models.CharField(max_length=100,  choices= entity_choices,blank=True)
    item_type = models.CharField(max_length=20, choices=Category_Choices)
    color = models.CharField(max_length=20, blank=True, choices=Subcategory_Choices)
    size = models.CharField(max_length=20, choices=size_Choices, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    due = models.CharField(max_length=20, choices=checkbox_choices, blank=True)

    def __str__(self):
        return f"{self.get_item_type_display()} ({self.quantity})"
    
# Employee Issue model
class EmployeeIssue(models.Model):
    emp_id = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    employee = models.ForeignKey('EmployeeDetails', null=True, blank=True, on_delete=models.SET_NULL, related_name='issues')
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    entity = models.CharField(max_length=100,  choices= entity_choices,blank=True)
    Category = models.CharField(max_length=20, choices=Category_Choices, blank=True)
    Subcategory = models.CharField(max_length=50, choices=Subcategory_Choices, blank=True)
    size = models.CharField(max_length=20,choices=size_Choices, blank=True)
    Issued_quantity = models.PositiveIntegerField(default=0)
    issued_date = models.DateField(default=timezone.now)
    Next_issue_date = models.DateField(blank=True, null=True)
    Buy = models.CharField(max_length=20, choices=stock_choices, blank=True)
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Price paid if item was bought")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Ensure the `employee` FK is linked automatically when emp_id is present.

        This keeps existing behavior but makes canonical employee details available via
        `issue.employee` for templates and views.
        """
        try:
            if (not getattr(self, 'employee', None)) and self.emp_id:
                # try to find an EmployeeDetails record matching emp_id
                emp = EmployeeDetails.objects.filter(emp_id__iexact=str(self.emp_id).strip()).first()
                if emp:
                    self.employee = emp
                    # keep name/email/gender/entity in sync when available
                    try:
                        if not self.name:
                            self.name = emp.emp_name
                        if not self.email:
                            self.email = getattr(emp, 'emp_email', None) or ''
                        if not getattr(self, 'gender', None):
                            self.gender = getattr(emp, 'gender', '')
                        if not getattr(self, 'entity', None):
                            self.entity = getattr(emp, 'entity', '')
                    except Exception:
                        pass
        except Exception:
            # never fail save because of linking
            pass
        super(EmployeeIssue, self).save(*args, **kwargs)
    
# Employee Details model
class EmployeeDetails(models.Model):
    emp_id = models.CharField(max_length=20)
    emp_name = models.CharField(max_length=100)
    emp_email = models.EmailField()
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),   
        ('female', 'Female'),
    ])
    entity = models.CharField(max_length=100,  choices= entity_choices,blank=True)
    def __str__(self):
        return self.emp_name

class Location(models.Model):
    Location = models.CharField(max_length=100, choices=location_choices, blank=True)
    
    def __str__(self):
        return self.Location


from django.db import models
from django.utils import timezone

class StationaryType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Stationary(models.Model):
    category = models. ForeignKey(StationaryType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category.name} - {self.quantity}"


class StationaryIssue(models.Model):
    # store employee basic details directly on the issue for denormalized history
    emp_id = models.CharField(max_length=20, blank=True, default='')
    emp_name = models.CharField(max_length=100, blank=True, default='')
    emp_email = models.EmailField(blank=True, null=True, default='')
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),   
        ('female', 'Female'),
    ], blank=True, default='')
    entity = models.CharField(max_length=100, choices=entity_choices, blank=True, default='')
    stationary = models.ForeignKey(Stationary, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    issued_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Issue of {self.quantity} {self.stationary.category.name}(s) to {self.emp_name}"

    from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('staff', 'Staff'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

