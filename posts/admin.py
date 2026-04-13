from django.contrib import admin
from .models import (
    City, Airport, Airline, AircraftType, Airplane,
    Route, Flight, FlightStatus, Passenger, Ticket
)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('city_id', 'city_name', 'country', 'time_zone')
    search_fields = ('city_name', 'country')

@admin.register(Airport)
class AirportAdmin(admin.ModelAdmin):
    list_display = ('airport_id', 'iata_code', 'airport_name', 'city')
    list_filter = ('city',)
    search_fields = ('iata_code', 'airport_name')

@admin.register(Airline)
class AirlineAdmin(admin.ModelAdmin):
    list_display = ('airline_id', 'iata_code', 'company_name', 'hub_airport')
    search_fields = ('company_name', 'iata_code')

@admin.register(AircraftType)
class AircraftTypeAdmin(admin.ModelAdmin):
    list_display = ('type_id', 'model', 'manufacturer', 'seating_capacity')
    search_fields = ('model', 'manufacturer')

@admin.register(FlightStatus)
class FlightStatusAdmin(admin.ModelAdmin):
    list_display = ('status_id', 'status_name', 'status_description')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        status_translations = {
            'Scheduled': '🕐 Запланирован',
            'Boarding': '🚪 Посадка',
            'Departed': '✈️ В пути',
            'Arrived': '✅ Прибыл',
            'Cancelled': '❌ Отменён'
        }
        return form

@admin.register(Airplane)
class AirplaneAdmin(admin.ModelAdmin):
    list_display = ('airplane_id', 'tail_number', 'aircraft_type', 'airline', 'manufacture_year')
    list_filter = ('airline', 'aircraft_type')
    search_fields = ('tail_number',)

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('route_id', 'flight_number', 'airline', 'departure_airport', 'arrival_airport', 'distance')
    list_filter = ('airline',)
    search_fields = ('flight_number',)

class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 0
    fields = ('passenger', 'seat_number', 'ticket_price')

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('flight_id', 'route', 'airplane', 'departure_time', 'arrival_time', 'flight_status')
    list_filter = ('flight_status', 'route__airline')
    inlines = [TicketInline]
    search_fields = ('route__flight_number', 'airplane__tail_number')

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('passenger_id', 'last_name', 'first_name', 'passport', 'bonus_miles')
    search_fields = ('last_name', 'first_name', 'passport', 'email')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_id', 'passenger', 'flight', 'seat_number', 'ticket_price', 'purchase_date')
    list_filter = ('flight__route__airline', 'purchase_date')
    search_fields = ('passenger__passport', 'passenger__last_name')