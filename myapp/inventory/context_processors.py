from .models import entity_choices, Category_Choices, size_Choices, Subcategory_Choices, EmployeeDetails
def entity_choices_processor(request):
    entity_list = [{'value': v, 'label': l} for v, l in (entity_choices or [])]
    categories = [{'value': v, 'label': l} for v, l in (Category_Choices or [])]
    sizes = [{'value': v, 'label': l} for v, l in (size_Choices or [])]
    subcats = [{'value': v, 'label': l} for v, l in (Subcategory_Choices or [])]

 
    CATEGORY_SIZES = {
        'tshirt': [s for s, _ in size_Choices if s in ('XS','S','M','L','XL','2XL','3XL','4XL','5XL')],
        'formals': [s for s, _ in size_Choices if s in ('XS','S','M','L','XL','2XL','3XL','4XL','5XL')],
        'jeans': [s for s, _ in size_Choices if s.isdigit() or s in ('28','30','32','34','36','38','40','42','44','46','48')],
        'safety_shoes': [str(n) for n in range(2, 13)],
        'goggles': [s for s, _ in size_Choices if s in ('normal','overhead')],
        'trainee': [s for s, _ in size_Choices if s in ('XS','S','M','L','XL','2XL','3XL','4XL','5XL')],
    }

    return {
        'ENTITY_CHOICES': entity_list,
        'CATEGORY_CHOICES': categories,
        'SIZE_CHOICES': sizes,
        'SUBCATEGORY_CHOICES': subcats,
        'CATEGORY_SIZES': CATEGORY_SIZES,
        'EMPLOYEES': [
            {'id': e.id, 'emp_id': e.emp_id, 'name': e.emp_name, 'email': e.emp_email}
            for e in EmployeeDetails.objects.all()
        ],
    }
