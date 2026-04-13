from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Avg, Sum
from django.contrib import messages
from .models import (Airport, Airline, Airplane, Route, Flight, Passenger, Ticket)
from .forms import FlightForm, PassengerForm, TicketForm
import csv
import json
from datetime import datetime


def index(request):
    return render(request, "index.html")


def airlines_list(request):
    airlines = Airline.objects.select_related('hub_airport').all().order_by("company_name")
    return render(request, "airlines.html", {"airlines": airlines})


def airports_list(request):
    airports = Airport.objects.select_related('city').all().order_by("iata_code")
    return render(request, "airports.html", {"airports": airports})


def flights_list(request):
    flights = Flight.objects.select_related(
        'route__departure_airport',
        'route__arrival_airport',
        'airplane',
        'flight_status',
        'route__airline'
    ).all().order_by("departure_time")
    return render(request, "flights.html", {"flights": flights})


def olap_analytics(request):
    report = request.GET.get('report', 'dashboard')
    context = {'headers': [], 'rows': [], 'report': report}

    context['total_flights'] = Flight.objects.count()
    context['total_airlines'] = Airline.objects.count()
    context['total_routes'] = Route.objects.count()
    context['total_passengers'] = Passenger.objects.count()
    context['active_flights'] = Flight.objects.filter(
        flight_status__status_name__in=['Scheduled', 'Boarding', 'Departed']
    ).count()

    if report == 'rollup_airline':
        data = Flight.objects.values(
            'route__airline__company_name',
            'route__airline__iata_code'
        ).annotate(
            flight_count=Count('flight_id'),
            avg_dist=Avg('route__distance'),
            total_dist=Sum('route__distance')
        ).order_by('-flight_count')

        context['headers'] = ['Авиакомпания', 'Код IATA', 'Рейсов', 'Ср. дистанция (км)', 'Всего км']
        context['rows'] = [[
            d['route__airline__company_name'],
            d['route__airline__iata_code'],
            d['flight_count'],
            round(float(d['avg_dist'] or 0), 1),
            float(d['total_dist'] or 0)
        ] for d in data]

    elif report == 'rollup_route':
        data = Route.objects.annotate(
            flight_count=Count('flight')
        ).select_related('departure_airport', 'arrival_airport').order_by('-flight_count')

        context['headers'] = ['Маршрут', 'Дистанция (км)', 'Рейсов']
        context['rows'] = [[
            f"{r.departure_airport.iata_code} → {r.arrival_airport.iata_code}",
            float(r.distance),
            r.flight_count,
        ] for r in data]

    elif report == 'rollup_aircraft':
        data = Flight.objects.values(
            'airplane__tail_number',
            'airplane__aircraft_type__model',
            'airplane__aircraft_type__manufacturer'
        ).annotate(
            flight_count=Count('flight_id'),
            avg_dist=Avg('route__distance')
        ).order_by('-flight_count')

        context['headers'] = ['Бортовой номер', 'Модель', 'Производитель', 'Рейсов', 'Ср. км']
        context['rows'] = [[
            d['airplane__tail_number'],
            d['airplane__aircraft_type__model'],
            d['airplane__aircraft_type__manufacturer'],
            d['flight_count'],
            round(float(d['avg_dist'] or 0), 1)
        ] for d in data]

    elif report == 'rollup_time':
        data = Flight.objects.extra(
            select={'month': "TO_CHAR(departure_time, 'YYYY-MM')"}
        ).values('month').annotate(
            flight_count=Count('flight_id'),
            avg_dist=Avg('route__distance')
        ).order_by('month')

        context['headers'] = ['Месяц', 'Рейсов', 'Ср. дистанция (км)']
        context['rows'] = [[
            d['month'],
            d['flight_count'],
            round(float(d['avg_dist'] or 0), 1)
        ] for d in data]

    elif report == 'slice_airline':
        airline_id = request.GET.get('airline_id')
        if airline_id:
            data = Flight.objects.filter(
                route__airline_id=airline_id
            ).select_related(
                'route__departure_airport',
                'route__arrival_airport',
                'airplane',
                'flight_status'
            ).order_by('departure_time')

            context['headers'] = ['Рейс', 'Маршрут', 'Самолет', 'Вылет', 'Статус']
            context['rows'] = [[
                f.route.flight_number,
                f"{f.route.departure_airport.iata_code} → {f.route.arrival_airport.iata_code}",
                f.airplane.tail_number,
                f.departure_time.strftime('%d.%m.%Y %H:%M'),
                f.flight_status.status_name if f.flight_status else '—'
            ] for f in data]
            context['selected_airline_id'] = airline_id

    elif report == 'slice_route':
        route_id = request.GET.get('route_id')
        if route_id:
            data = Flight.objects.filter(
                route_id=route_id
            ).select_related(
                'airplane__aircraft_type',
                'route__airline',
                'flight_status'
            ).order_by('departure_time')

            context['headers'] = ['Дата вылета', 'Борт', 'Тип ВС', 'Авиакомпания', 'Статус']
            context['rows'] = [[
                f.departure_time.strftime('%d.%m.%Y %H:%M'),
                f.airplane.tail_number,
                f"{f.airplane.aircraft_type.manufacturer} {f.airplane.aircraft_type.model}",
                f.route.airline.company_name,
                f.flight_status.status_name if f.flight_status else '—'
            ] for f in data]
            context['selected_route_id'] = route_id

    elif report == 'matrix_aircraft_route':
        airplanes = Airplane.objects.all().order_by('tail_number')
        routes = Route.objects.all().order_by('flight_number')

        flight_counts = Flight.objects.values(
            'airplane_id', 'route_id'
        ).annotate(cnt=Count('flight_id'))

        counts_dict = {}
        for item in flight_counts:
            key = (item['airplane_id'], item['route_id'])
            counts_dict[key] = item['cnt']

        context['headers'] = ['Самолет'] + [
            f"{r.flight_number} ({r.departure_airport.iata_code}-{r.arrival_airport.iata_code})" for r in routes]
        context['rows'] = []

        for plane in airplanes:
            row = [f"{plane.tail_number} ({plane.aircraft_type.model})"]
            for route in routes:
                count = counts_dict.get((plane.airplane_id, route.route_id), 0)
                row.append(count if count > 0 else '—')
            context['rows'].append(row)

    elif report == 'passenger_statistics':
        data = Passenger.objects.annotate(
            tickets_count=Count('ticket'),
            total_spent=Sum('ticket__ticket_price'),
            avg_price=Avg('ticket__ticket_price')
        ).order_by('-total_spent')

        context['headers'] = ['Пассажир', 'Паспорт', 'Билетов', 'Всего потрачено (₽)', 'Ср. цена билета']
        context['rows'] = [[
            f"{p.last_name} {p.first_name} {p.middle_name}",
            p.passport,
            p.tickets_count,
            float(p.total_spent or 0),
            round(float(p.avg_price or 0), 2)
        ] for p in data]

    context['airlines'] = Airline.objects.all().order_by('company_name')
    context['routes'] = Route.objects.select_related(
        'departure_airport', 'arrival_airport'
    ).all().order_by('flight_number')

    return render(request, "olap_analytics.html", context)


def flight_map(request):
    """Интерактивная карта полетов"""
    all_flights = Flight.objects.select_related(
        'route__departure_airport__city',
        'route__arrival_airport__city',
        'airplane__aircraft_type',
        'route__airline',
        'flight_status'
    ).order_by('departure_time')

    flights_data = []
    for flight in all_flights:
        flights_data.append({
            'id': flight.flight_id,
            'flight_number': flight.route.flight_number,
            'airline': flight.route.airline.company_name,
            'airline_code': flight.route.airline.iata_code,
            'airplane': f"{flight.airplane.tail_number}",
            'aircraft_type': f"{flight.airplane.aircraft_type.manufacturer} {flight.airplane.aircraft_type.model}",
            'departure_airport': {
                'iata': flight.route.departure_airport.iata_code,
                'name': flight.route.departure_airport.airport_name,
                'city': flight.route.departure_airport.city.city_name,
                'country': flight.route.departure_airport.city.country,
            },
            'arrival_airport': {
                'iata': flight.route.arrival_airport.iata_code,
                'name': flight.route.arrival_airport.airport_name,
                'city': flight.route.arrival_airport.city.city_name,
                'country': flight.route.arrival_airport.city.country,
            },
            'departure_time': flight.departure_time.isoformat(),
            'arrival_time': flight.arrival_time.isoformat(),
            'status': flight.flight_status.status_name if flight.flight_status else 'Unknown',
            'distance': float(flight.route.distance),
        })

    return render(request, "flight_map.html", {
        'flights_json': json.dumps(flights_data),
        'active_flights_count': len(flights_data)
    })

def flight_details(request, flight_id):
    try:
        flight = Flight.objects.select_related(
            'route__departure_airport__city',
            'route__arrival_airport__city',
            'airplane__aircraft_type',
            'route__airline',
            'flight_status'
        ).get(flight_id=flight_id)

        tickets = Ticket.objects.filter(flight=flight).select_related('passenger')

        data = {
            'flight_number': flight.route.flight_number,
            'airline': flight.route.airline.company_name,
            'airplane': f"{flight.airplane.tail_number} ({flight.airplane.aircraft_type.model})",
            'departure': {
                'airport': f"{flight.route.departure_airport.iata_code} - {flight.route.departure_airport.airport_name}",
                'city': flight.route.departure_airport.city.city_name,
                'time': flight.departure_time.strftime('%Y-%m-%d %H:%M'),
            },
            'arrival': {
                'airport': f"{flight.route.arrival_airport.iata_code} - {flight.route.arrival_airport.airport_name}",
                'city': flight.route.arrival_airport.city.city_name,
                'time': flight.arrival_time.strftime('%Y-%m-%d %H:%M'),
            },
            'distance': f"{flight.route.distance} км",
            'status': flight.flight_status.status_name if flight.flight_status else 'Unknown',
            'passengers_count': tickets.count(),
        }
        return JsonResponse(data)
    except Flight.DoesNotExist:
        return JsonResponse({'error': 'Рейс не найден'}, status=404)


def export_csv(request):
    """Экспорт данных в CSV с учётом выбранного отчёта OLAP"""
    report = request.GET.get('report', 'flights')
    airline_id = request.GET.get('airline_id')
    route_id = request.GET.get('route_id')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    filename = f"report_{report}_{datetime.now().strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff'.encode('utf8'))

    writer = csv.writer(response)

    if report == 'flights':
        writer.writerow(['Рейс', 'Авиакомпания', 'Маршрут', 'Самолет', 'Вылет', 'Прилет', 'Статус'])
        flights = Flight.objects.select_related(
            'route__airline', 'route__departure_airport',
            'route__arrival_airport', 'airplane', 'flight_status'
        ).all()
        for f in flights:
            writer.writerow([
                f.route.flight_number,
                f.route.airline.company_name,
                f"{f.route.departure_airport.iata_code} → {f.route.arrival_airport.iata_code}",
                f.airplane.tail_number,
                f.departure_time.strftime('%Y-%m-%d %H:%M'),
                f.arrival_time.strftime('%Y-%m-%d %H:%M'),
                f.flight_status.status_name if f.flight_status else '—',
            ])

    elif report == 'rollup_airline':
        writer.writerow(['Авиакомпания', 'Код IATA', 'Рейсов', 'Ср. дистанция (км)', 'Всего км'])
        data = Flight.objects.values(
            'route__airline__company_name',
            'route__airline__iata_code'
        ).annotate(
            flight_count=Count('flight_id'),
            avg_dist=Avg('route__distance'),
            total_dist=Sum('route__distance')
        ).order_by('-flight_count')

        for d in data:
            writer.writerow([
                d['route__airline__company_name'],
                d['route__airline__iata_code'],
                d['flight_count'],
                round(float(d['avg_dist'] or 0), 1),
                float(d['total_dist'] or 0)
            ])

    elif report == 'rollup_route':
        writer.writerow(['Маршрут', 'Дистанция (км)', 'Рейсов'])
        data = Route.objects.annotate(
            flight_count=Count('flight')
        ).select_related('departure_airport', 'arrival_airport').order_by('-flight_count')

        for r in data:
            writer.writerow([
                f"{r.departure_airport.iata_code} → {r.arrival_airport.iata_code}",
                float(r.distance),
                r.flight_count,
            ])

    elif report == 'rollup_aircraft':
        writer.writerow(['Бортовой номер', 'Модель', 'Производитель', 'Рейсов', 'Ср. км'])
        data = Flight.objects.values(
            'airplane__tail_number',
            'airplane__aircraft_type__model',
            'airplane__aircraft_type__manufacturer'
        ).annotate(
            flight_count=Count('flight_id'),
            avg_dist=Avg('route__distance')
        ).order_by('-flight_count')

        for d in data:
            writer.writerow([
                d['airplane__tail_number'],
                d['airplane__aircraft_type__model'],
                d['airplane__aircraft_type__manufacturer'],
                d['flight_count'],
                round(float(d['avg_dist'] or 0), 1)
            ])

    elif report == 'rollup_time':
        writer.writerow(['Месяц', 'Рейсов', 'Ср. дистанция (км)'])
        data = Flight.objects.extra(
            select={'month': "TO_CHAR(departure_time, 'YYYY-MM')"}
        ).values('month').annotate(
            flight_count=Count('flight_id'),
            avg_dist=Avg('route__distance')
        ).order_by('month')

        for d in data:
            writer.writerow([
                d['month'],
                d['flight_count'],
                round(float(d['avg_dist'] or 0), 1)
            ])

    elif report == 'slice_airline':
        writer.writerow(['Рейс', 'Маршрут', 'Самолет', 'Вылет', 'Статус'])
        if airline_id:
            data = Flight.objects.filter(
                route__airline_id=airline_id
            ).select_related(
                'route__departure_airport',
                'route__arrival_airport',
                'airplane',
                'flight_status'
            ).order_by('departure_time')

            for f in data:
                writer.writerow([
                    f.route.flight_number,
                    f"{f.route.departure_airport.iata_code} → {f.route.arrival_airport.iata_code}",
                    f.airplane.tail_number,
                    f.departure_time.strftime('%Y-%m-%d %H:%M'),
                    f.flight_status.status_name if f.flight_status else '—'
                ])
        else:
            writer.writerow(['Выберите авиакомпанию для экспорта'])

    elif report == 'slice_route':
        writer.writerow(['Дата вылета', 'Борт', 'Тип ВС', 'Авиакомпания', 'Статус'])
        if route_id:
            data = Flight.objects.filter(
                route_id=route_id
            ).select_related(
                'airplane__aircraft_type',
                'route__airline',
                'flight_status'
            ).order_by('departure_time')

            for f in data:
                writer.writerow([
                    f.departure_time.strftime('%Y-%m-%d %H:%M'),
                    f.airplane.tail_number,
                    f"{f.airplane.aircraft_type.manufacturer} {f.airplane.aircraft_type.model}",
                    f.route.airline.company_name,
                    f.flight_status.status_name if f.flight_status else '—'
                ])
        else:
            writer.writerow(['Выберите маршрут для экспорта'])

    elif report == 'matrix_aircraft_route':
        airplanes = Airplane.objects.all().order_by('tail_number')
        routes = Route.objects.all().order_by('flight_number')
        header_row = ['Самолет'] + [f"{r.flight_number} ({r.departure_airport.iata_code}-{r.arrival_airport.iata_code})"
                                    for r in routes]
        writer.writerow(header_row)
        flight_counts = Flight.objects.values(
            'airplane_id', 'route_id'
        ).annotate(cnt=Count('flight_id'))

        counts_dict = {}
        for item in flight_counts:
            key = (item['airplane_id'], item['route_id'])
            counts_dict[key] = item['cnt']

        for plane in airplanes:
            row = [f"{plane.tail_number} ({plane.aircraft_type.model})"]
            for route in routes:
                count = counts_dict.get((plane.airplane_id, route.route_id), 0)
                row.append(count if count > 0 else 'NULL')
            writer.writerow(row)

    elif report == 'passenger_statistics':
        writer.writerow(['Пассажир', 'Паспорт', 'Билетов', 'Всего потрачено (₽)', 'Ср. цена билета'])
        data = Passenger.objects.annotate(
            tickets_count=Count('ticket'),
            total_spent=Sum('ticket__ticket_price'),
            avg_price=Avg('ticket__ticket_price')
        ).order_by('-total_spent')

        for p in data:
            writer.writerow([
                f"{p.last_name} {p.first_name} {p.middle_name}",
                p.passport,
                p.tickets_count,
                float(p.total_spent or 0),
                round(float(p.avg_price or 0), 2)
            ])

    elif report == 'airlines':
        writer.writerow(['Авиакомпания', 'Код IATA', 'Телефон', 'Email', 'Хаб'])
        airlines = Airline.objects.select_related('hub_airport').all()
        for a in airlines:
            writer.writerow([
                a.company_name,
                a.iata_code,
                a.hotline_phone or '',
                a.email or '',
                f"{a.hub_airport.iata_code}" if a.hub_airport else '',
            ])

    elif report == 'passengers':
        writer.writerow(['Фамилия', 'Имя', 'Отчество', 'Паспорт', 'Телефон', 'Email', 'Бонусные мили'])
        passengers = Passenger.objects.all()
        for p in passengers:
            writer.writerow([
                p.last_name,
                p.first_name,
                p.middle_name,
                p.passport,
                p.phone_number or '',
                p.email or '',
                p.bonus_miles,
            ])

    else:
        writer.writerow(['Неизвестный тип отчёта'])

    return response


def api_active_flights(request):
    active_flights = Flight.objects.filter(
        flight_status__status_name__in=['Scheduled', 'Boarding', 'Departed']
    ).select_related(
        'route__departure_airport',
        'route__arrival_airport',
        'airplane__aircraft_type',
        'route__airline'
    )

    data = []
    for flight in active_flights:
        data.append({
            'id': flight.flight_id,
            'flight_number': flight.route.flight_number,
            'airline': flight.route.airline.iata_code,
            'departure': {'iata': flight.route.departure_airport.iata_code},
            'arrival': {'iata': flight.route.arrival_airport.iata_code},
            'aircraft': flight.airplane.aircraft_type.model,
            'status': flight.flight_status.status_name if flight.flight_status else 'Unknown',
        })
    return JsonResponse({'flights': data})


# CRUD для рейсов
def flight_list(request):
    """Список всех рейсов с возможностью CRUD"""
    flights = Flight.objects.select_related(
        'route__departure_airport',
        'route__arrival_airport',
        'airplane',
        'flight_status',
        'route__airline'
    ).all().order_by("departure_time")
    return render(request, "flight_crud_list.html", {"flights": flights})


def flight_create(request):
    """Создание нового рейса"""
    if request.method == 'POST':
        form = FlightForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Рейс успешно создан!')
            return redirect('flight_list')
    else:
        form = FlightForm()
    return render(request, "flight_form.html", {"form": form, "title": "Создание рейса"})


def flight_update(request, flight_id):
    """Редактирование рейса"""
    flight = get_object_or_404(Flight, flight_id=flight_id)

    if request.method == 'POST':
        form = FlightForm(request.POST, instance=flight)
        if form.is_valid():
            form.save()
            messages.success(request, 'Рейс успешно обновлен!')
            return redirect('flight_list')
    else:
        # При GET запросе создаем форму с существующими данными
        form = FlightForm(instance=flight)

    return render(request, "flight_form.html", {
        "form": form,
        "title": "Редактирование рейса",
        "flight": flight
    })

def flight_delete(request, flight_id):
    """Удаление рейса"""
    flight = get_object_or_404(Flight, flight_id=flight_id)
    if request.method == 'POST':
        flight.delete()
        messages.success(request, 'Рейс успешно удален!')
        return redirect('flight_list')
    return render(request, "flight_confirm_delete.html", {"flight": flight})

# CRUD для пассажиров
def passenger_list(request):
    """Список всех пассажиров"""
    passengers = Passenger.objects.all().order_by("last_name", "first_name")
    return render(request, "passenger_crud_list.html", {"passengers": passengers})

def passenger_create(request):
    """Создание нового пассажира"""
    if request.method == 'POST':
        form = PassengerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пассажир успешно создан!')
            return redirect('passenger_list')
    else:
        form = PassengerForm()
    return render(request, "passenger_form.html", {"form": form, "title": "Создание пассажира"})

def passenger_update(request, passenger_id):
    """Редактирование пассажира"""
    passenger = get_object_or_404(Passenger, passenger_id=passenger_id)
    if request.method == 'POST':
        form = PassengerForm(request.POST, instance=passenger)
        if form.is_valid():
            form.save()
            messages.success(request, 'Пассажир успешно обновлен!')
            return redirect('passenger_list')
    else:
        form = PassengerForm(instance=passenger)
    return render(request, "passenger_form.html", {"form": form, "title": "Редактирование пассажира", "passenger": passenger})

def passenger_delete(request, passenger_id):
    """Удаление пассажира"""
    passenger = get_object_or_404(Passenger, passenger_id=passenger_id)
    if request.method == 'POST':
        passenger.delete()
        messages.success(request, 'Пассажир успешно удален!')
        return redirect('passenger_list')
    return render(request, "passenger_confirm_delete.html", {"passenger": passenger})

# CRUD для билетов
def ticket_list(request):
    """Список всех билетов"""
    tickets = Ticket.objects.select_related(
        'passenger', 'flight__route__departure_airport', 'flight__route__arrival_airport'
    ).all().order_by("-purchase_date")
    return render(request, "ticket_crud_list.html", {"tickets": tickets})

def ticket_create(request):
    """Создание нового билета"""
    if request.method == 'POST':
        form = TicketForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Билет успешно создан!')
            return redirect('ticket_list')
    else:
        form = TicketForm()
    return render(request, "ticket_form.html", {"form": form, "title": "Создание билета"})

def ticket_update(request, ticket_id):
    """Редактирование билета"""
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Билет успешно обновлен!')
            return redirect('ticket_list')
    else:
        form = TicketForm(instance=ticket)
    return render(request, "ticket_form.html", {"form": form, "title": "Редактирование билета", "ticket": ticket})

def ticket_delete(request, ticket_id):
    """Удаление билета"""
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    if request.method == 'POST':
        ticket.delete()
        messages.success(request, 'Билет успешно удален!')
        return redirect('ticket_list')
    return render(request, "ticket_confirm_delete.html", {"ticket": ticket})