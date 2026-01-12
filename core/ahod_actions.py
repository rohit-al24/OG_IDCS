
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import OD, STATUS
from .helpers import get_post

@require_POST
def ahod_action_od(request, id):
    od = get_object_or_404(OD, id=id)
    status = request.POST.get('sts')
    ahod_hod_reason = request.POST.get('ahod_hod_reason', '').strip()
    user = request.user
    role = request.POST.get('role', '').strip()

    # --- Mentees Table: AHOD acting as Mentor or Advisor ---
    if role == 'mentor':
        # Only update Mentor status
        od.Mstatus = status
        od.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))
    elif role == 'advisor':
        # Only update Advisor status
        od.Astatus = status
        od.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))

    # --- Dept OD Table: AHOD dept-level actions (no role field) ---
    # If AHOD approves as AHOD before mentor/advisor, also set Mstatus and Astatus to Approved if still Pending
    # Notify student if AHOD acts (for any AHOD/HOD action)
    if status in ['Approved_AHOD_HOD', 'Rejected_AHOD_HOD', STATUS[1][0], STATUS[2][0]]:
        from .models import Notification
        Notification.objects.create(
            student=od.user,
            message=f"Your OD request was {status.split('_')[0]} by AHOD."
        )
    if status == 'Approved_AHOD_HOD':
        od.AHstatus = STATUS[1][0]  # Approved
        od.Hstatus = STATUS[1][0]   # Approved
        if od.Astatus == STATUS[0][0]:
            od.Astatus = STATUS[1][0]  # If advisor is still pending, approve it
        if od.Mstatus == STATUS[0][0]:
            od.Mstatus = STATUS[1][0]  # If mentor is still pending, approve it
        od.ahod_hod_action = status
        od.ahod_hod_reason = ahod_hod_reason
        od.save()
    elif status == 'Rejected_AHOD_HOD':
        od.AHstatus = STATUS[2][0]  # Rejected
        od.Hstatus = STATUS[2][0]   # Rejected
        od.Astatus = STATUS[2][0]   # Advisor also rejected
        if od.Mstatus == STATUS[0][0]:
            od.Mstatus = STATUS[2][0]  # If mentor is still pending, reject it
        od.ahod_hod_action = status
        od.ahod_hod_reason = ahod_hod_reason
        od.save()
    elif status == STATUS[1][0]:  # 'Approved' (AHOD only)
        od.AHstatus = STATUS[1][0]
        if od.Astatus == STATUS[0][0]:
            od.Astatus = STATUS[1][0]
        if od.Mstatus == STATUS[0][0]:
            od.Mstatus = STATUS[1][0]
        od.save()
    elif status == STATUS[2][0]:  # 'Rejected' (AHOD only)
        od.AHstatus = STATUS[2][0]
        if od.Astatus == STATUS[0][0]:
            od.Astatus = STATUS[2][0]
        if od.Mstatus == STATUS[0][0]:
            od.Mstatus = STATUS[2][0]
        od.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))
