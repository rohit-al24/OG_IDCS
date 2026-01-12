from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import LEAVE, STATUS
from .helpers import get_post

@require_POST
def ahod_action_leave(request, id):
    leave = get_object_or_404(LEAVE, id=id)
    status = request.POST.get('sts')
    ahod_hod_reason = request.POST.get('ahod_hod_reason', '').strip()
    user = request.user
    role = request.POST.get('role')
    # Always handle by role first
    if role == 'mentor':
        if status == 'Rejected':
            leave.Mstatus = 'Rejected'
            leave.Astatus = 'Rejected'
            leave.AHstatus = 'Rejected'
            leave.Hstatus = 'Rejected'
        else:
            leave.Mstatus = status
        leave.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))
    if role == 'advisor':
        if status == 'Rejected':
            leave.Astatus = 'Rejected'
            leave.AHstatus = 'Rejected'
            leave.Hstatus = 'Rejected'
        else:
            leave.Astatus = status
        leave.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))
    if role == 'ahod':
        # Notify student if AHOD acts (for any AHOD/HOD action)
        from .models import Notification
        Notification.objects.create(
            student=leave.user,
            message=f"Your Leave request was {status.split('_')[0]} by AHOD."
        )
        if status == 'Approved':
            leave.AHstatus = 'Approved'
            # Auto-approve any lower-level statuses still pending
            if leave.Mstatus == 'Pending':
                leave.Mstatus = 'Approved'
            if leave.Astatus == 'Pending':
                leave.Astatus = 'Approved'
            # Only set HOD to Pending if not already set (default is Pending)
            if leave.Hstatus not in ['Pending', 'Approved', 'Rejected']:
                leave.Hstatus = 'Pending'
            leave.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
        elif status == 'Rejected':
            leave.AHstatus = 'Rejected'
            leave.Hstatus = 'Rejected'
            # Cascade rejection to any lower-level statuses still pending
            if leave.Mstatus == 'Pending':
                leave.Mstatus = 'Rejected'
            if leave.Astatus == 'Pending':
                leave.Astatus = 'Rejected'
            leave.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
        elif status == 'Approved_AHOD_HOD':
            leave.AHstatus = 'Approved'
            leave.Hstatus = 'Approved'
            leave.ahod_hod_action = status
            leave.ahod_hod_reason = ahod_hod_reason
            # Auto-approve any lower-level statuses still pending
            if leave.Mstatus == 'Pending':
                leave.Mstatus = 'Approved'
            if leave.Astatus == 'Pending':
                leave.Astatus = 'Approved'
            leave.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
        elif status == 'Rejected_AHOD_HOD':
            leave.AHstatus = 'Rejected'
            leave.Hstatus = 'Rejected'
            leave.ahod_hod_action = status
            leave.ahod_hod_reason = ahod_hod_reason
            # Cascade rejection to any lower-level statuses still pending
            if leave.Mstatus == 'Pending':
                leave.Mstatus = 'Rejected'
            if leave.Astatus == 'Pending':
                leave.Astatus = 'Rejected'
            leave.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
    # Fallback: if user is mentor/advisor but role not set, allow legacy behavior
    is_mentor = hasattr(leave.user, 'mentor') and leave.user.mentor and leave.user.mentor.user == user
    is_advisor = hasattr(leave.user, 'advisor') and leave.user.advisor and leave.user.advisor.user == user
    if is_mentor or is_advisor:
        if is_mentor and is_advisor:
            leave.Mstatus = status
            leave.Astatus = status
        elif is_mentor:
            leave.Mstatus = status
        elif is_advisor:
            leave.Astatus = status
        leave.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))
    return redirect(request.META.get('HTTP_REFERER', '/'))
