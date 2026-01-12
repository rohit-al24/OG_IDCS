from django import template
register = template.Library()

@register.filter
def get_custom_name(staff_list, selected_staff_id):
    """
    Extracts the custom staff name from the staff_list and selected_staff_id.
    If selected_staff_id starts with 'custom_', returns the name after 'custom_'.
    """
    if selected_staff_id and str(selected_staff_id).startswith('custom_'):
        return str(selected_staff_id)[7:]
    # fallback: try to find in staff_list
    for s in staff_list:
        if str(s.id) == str(selected_staff_id):
            return getattr(s, 'name', str(selected_staff_id))
    return selected_staff_id
