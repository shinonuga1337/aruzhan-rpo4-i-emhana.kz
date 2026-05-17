from django.http import JsonResponse  # 👈 ДОБАВИЛ

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
import json

from .models import Appointment, Patient, Doctor


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('emhana:dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('emhana:login')


@login_required
def dashboard_view(request):
    seven_days_ago = timezone.now() - timedelta(days=7)

    daily_appointments = Appointment.objects.filter(date_time__gte=seven_days_ago) \
        .annotate(date=TruncDate('date_time')) \
        .values('date') \
        .annotate(count=Count('id')) \
        .order_by('date')

    dates = [obj['date'].strftime('%m/%d/%Y') for obj in daily_appointments]
    counts = [obj['count'] for obj in daily_appointments]

    status_data = Appointment.objects.values('status').annotate(count=Count('id'))

    statuses = [i['status'] for i in status_data]
    status_counts = [i['count'] for i in status_data]

    total_patients = Patient.objects.count()
    pending_appointments = Appointment.objects.filter(status='pending').count()

    context = {
        'dates_json': json.dumps(dates),
        'counts_json': json.dumps(counts),
        'total_patients': total_patients,
        'pending_appointments': pending_appointments,
        'statuses_json': json.dumps(statuses),
        'status_counts_json': json.dumps(status_counts),
    }
    return render(request, 'dashboard.html', context)


@login_required
def appointment_list_view(request):
    appointments = Appointment.objects.all().order_by('-date_time')

    status_filter = request.GET.get('status')
    doctor_filter = request.GET.get('doctor_id')
    iin = request.GET.get('iin')

    if status_filter:
        appointments = appointments.filter(status=status_filter)

    if doctor_filter:
        appointments = appointments.filter(doctor_id=doctor_filter)

    if iin:
        appointments = appointments.filter(patient__iin__icontains=iin)

    # PAGINATION
    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    doctors = Doctor.objects.all()

    context = {
        'appointments': page_obj,  # 👈 важно
        'page_obj': page_obj,
        'doctors': doctors,
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'partials/appointments_table.html', context)
    return render(request, 'appointment_list.html', context)


@login_required
def appointment_create_view(request):
    if request.method == 'POST':
        iin = request.POST.get('iin')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        doctor_id = request.POST.get('doctor_id')
        date_time = request.POST.get('date_time')
        notes = request.POST.get('notes')

        patient, created = Patient.objects.get_or_create(
            iin=iin,
            defaults={'full_name': full_name, 'phone': phone}
        )

        Appointment.objects.create(
            patient=patient,
            doctor_id=doctor_id,
            date_time=date_time,
            notes=notes
        )

        return redirect('emhana:appointment_list')

    doctors = Doctor.objects.all()
    return render(request, 'appointment_create.html', {'doctors': doctors})

@login_required
def search_appointments(request):
    iin = request.GET.get('iin', '')

    qs = Appointment.objects.select_related('patient', 'doctor')

    if iin:
        qs = qs.filter(patient__iin__icontains=iin)

    results = [
        {
            "patient": a.patient.full_name,
            "iin": a.patient.iin,
            "doctor": a.doctor.id,
            "date_time": a.date_time.strftime("%Y-%m-%d %H:%M"),
            "status": a.status,
        }
        for a in qs[:20]
    ]

    return JsonResponse({"results": results})