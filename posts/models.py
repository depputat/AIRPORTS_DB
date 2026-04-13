from django.db import models
from django.utils import timezone


class City(models.Model):
    city_id = models.AutoField(primary_key=True, db_column='city_id')
    city_name = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    time_zone = models.CharField(max_length=10)

    class Meta:
        db_table = 'cities'
        #managed = False

    def __str__(self):
        return self.city_name


class Airport(models.Model):
    airport_id = models.AutoField(primary_key=True, db_column='airport_id')
    iata_code = models.CharField(max_length=3, unique=True)
    airport_name = models.CharField(max_length=150)
    city = models.ForeignKey(City, on_delete=models.CASCADE, db_column='city_id', to_field='city_id')

    class Meta:
        db_table = 'airports'
        #managed = False

    def __str__(self):
        return f"{self.iata_code} - {self.airport_name}"


class Airline(models.Model):
    airline_id = models.AutoField(primary_key=True, db_column='airline_id')
    company_name = models.CharField(max_length=100)
    iata_code = models.CharField(max_length=3, unique=True)
    hotline_phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    hub_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, db_column='hub_airport_id',
                                    to_field='airport_id', blank=True, null=True)

    class Meta:
        db_table = 'airlines'
        #managed = False

    def __str__(self):
        return f"{self.iata_code} - {self.company_name}"


class AircraftType(models.Model):
    type_id = models.AutoField(primary_key=True, db_column='type_id')
    model = models.CharField(max_length=100)
    manufacturer = models.CharField(max_length=100)
    payload_capacity = models.IntegerField()
    seating_capacity = models.IntegerField()

    class Meta:
        db_table = 'aircraft_types'
        #managed = False

    def __str__(self):
        return f"{self.manufacturer} {self.model}"


class Airplane(models.Model):
    airplane_id = models.AutoField(primary_key=True, db_column='airplane_id')
    tail_number = models.CharField(max_length=20, unique=True)
    aircraft_type = models.ForeignKey(AircraftType, on_delete=models.CASCADE, db_column='type_id', to_field='type_id')
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, db_column='airline_id', to_field='airline_id')
    manufacture_year = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'airplanes'
        #managed = False

    def __str__(self):
        return self.tail_number


class Route(models.Model):
    route_id = models.AutoField(primary_key=True, db_column='route_id')
    flight_number = models.CharField(max_length=10)
    departure_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, db_column='departure_airport_id',
                                          to_field='airport_id', related_name='departure_routes')
    arrival_airport = models.ForeignKey(Airport, on_delete=models.CASCADE, db_column='arrival_airport_id',
                                        to_field='airport_id', related_name='arrival_routes')
    distance = models.DecimalField(max_digits=8, decimal_places=2)
    airline = models.ForeignKey(Airline, on_delete=models.CASCADE, db_column='airline_id', to_field='airline_id')

    class Meta:
        db_table = 'routes'
        #managed = False

    def __str__(self):
        return f"{self.flight_number}"


class FlightStatus(models.Model):
    status_id = models.AutoField(primary_key=True, db_column='status_id')
    status_name = models.CharField(max_length=50)
    status_description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'flight_status'
        #managed = False

    def __str__(self):
        return self.status_name


class Flight(models.Model):
    flight_id = models.AutoField(primary_key=True, db_column='flight_id')
    route = models.ForeignKey(Route, on_delete=models.CASCADE, db_column='route_id', to_field='route_id')
    airplane = models.ForeignKey(Airplane, on_delete=models.CASCADE, db_column='airplane_id', to_field='airplane_id')
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    flight_status = models.ForeignKey(FlightStatus, on_delete=models.CASCADE, db_column='status_id',
                                      to_field='status_id', blank=True, null=True)

    class Meta:
        db_table = 'flights'
        #managed = False

    def __str__(self):
        return f"{self.route.flight_number} ({self.departure_time})"

    def get_status_display(self):
        if self.flight_status:
            return self.flight_status.status_name
        return "—"

    def get_status_description(self):
        if self.flight_status:
            return self.flight_status.status_description
        return ""


class Passenger(models.Model):
    passenger_id = models.AutoField(primary_key=True, db_column='passenger_id')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100)
    passport = models.CharField(max_length=50, unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    bonus_miles = models.IntegerField(default=0)

    class Meta:
        db_table = 'passengers'
        #managed = False

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class Ticket(models.Model):
    ticket_id = models.AutoField(primary_key=True, db_column='ticket_id')
    passenger = models.ForeignKey(Passenger, on_delete=models.CASCADE, db_column='passenger_id',
                                  to_field='passenger_id')
    flight = models.ForeignKey(Flight, on_delete=models.CASCADE, db_column='flight_id', to_field='flight_id')
    seat_number = models.CharField(max_length=10)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(default=timezone.now)
    baggage_weight = models.DecimalField(max_digits=6, decimal_places=3)

    class Meta:
        db_table = 'tickets'
        #managed = False

    def __str__(self):
        return f"Ticket {self.ticket_id} - {self.passenger}"