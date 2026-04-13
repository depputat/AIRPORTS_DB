from django import forms
from .models import Flight, Passenger, Ticket, Route, Airplane, FlightStatus


class FlightForm(forms.ModelForm):
    class Meta:
        model = Flight
        fields = ['route', 'airplane', 'departure_time', 'arrival_time', 'flight_status']
        widgets = {
            'departure_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'arrival_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['flight_status'].label_from_instance = self.translate_status

    def translate_status(self, obj):
        """Перевод статусов рейсов на русский язык"""
        status_translations = {
            'Scheduled': '🕐 Запланирован',
            'Boarding': '🚪 Посадка',
            'Departed': '✈️ В пути',
            'Arrived': '✅ Прибыл',
            'Cancelled': '❌ Отменён'
        }
        return status_translations.get(obj.status_name, obj.status_name)


class PassengerForm(forms.ModelForm):
    class Meta:
        model = Passenger
        fields = ['first_name', 'last_name', 'middle_name', 'passport', 'phone_number', 'email', 'bonus_miles']


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['passenger', 'flight', 'seat_number', 'ticket_price', 'baggage_weight']