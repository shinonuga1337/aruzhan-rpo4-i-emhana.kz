from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from faker import Faker
from django.utils import timezone
from emhana.models import Patient, Doctor, Appointment
import random

fake = Faker('ru_RU')


class Command(BaseCommand):
    help = 'Генерация тестовых данных'

    def handle(self, *args, **kwargs):

        patients = []

        # Пациенты
        for _ in range(500):
            patient = Patient.objects.create(
                iin=str(fake.unique.random_number(digits=12)),
                full_name=fake.name(),
                phone=fake.phone_number()
            )

            patients.append(patient)

        # Врачи
        doctors = []

        for i in range(20):

            user = User.objects.create_user(
                username=f'doctor{i}',
                password='12345'
            )

            doctor = Doctor.objects.create(
                user=user,
                specialty=random.choice([
                    'Терапевт',
                    'Хирург',
                    'Педиатр'
                ])
            )

            doctors.append(doctor)

        # Приемы
        statuses = ['completed', 'pending', 'canceled']

        for _ in range(1000):

            Appointment.objects.create(
                patient=random.choice(patients),
                doctor=random.choice(doctors),
                date_time=timezone.now(),
                status=random.choice(statuses),
                notes=fake.text(max_nb_chars=100)
            )

        self.stdout.write(
            self.style.SUCCESS('Тестовые данные успешно созданы!')
        )