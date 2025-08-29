from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Voucher
from .forms import VoucherApplyForm

@require_POST
def voucher_apply(request):
    form = VoucherApplyForm(request.POST)
    if form.is_valid():
        now = timezone.now()
        code = form.cleaned_data['code']
        try:
            v = Voucher.objects.get(
                code__iexact=code,
                valid_from__lte=now,
                valid_to__gte=now,
                active=True
            )
            request.session['voucher_id'] = v.id
        except Voucher.DoesNotExist:
            request.session['voucher_id'] = None
    return redirect('cart') 
