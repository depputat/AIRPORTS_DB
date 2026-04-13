from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('airlines/', views.airlines_list, name='airlines_list'),
    path('airports/', views.airports_list, name='airports_list'),
    path('flights/', views.flights_list, name='flights_list'),
    path('olap/', views.olap_analytics, name='olap_analytics'),
    path('map/', views.flight_map, name='flight_map'),
    path('api/flight/<int:flight_id>/', views.flight_details, name='flight_details'),
    path('api/active-flights/', views.api_active_flights, name='api_active_flights'),
    path('export/csv/', views.export_csv, name='export_csv'),

    # CRUD для рейсов
    path('flights-crud/', views.flight_list, name='flight_list'),
    path('flights-crud/create/', views.flight_create, name='flight_create'),
    path('flights-crud/<int:flight_id>/update/', views.flight_update, name='flight_update'),
    path('flights-crud/<int:flight_id>/delete/', views.flight_delete, name='flight_delete'),

    # CRUD для пассажиров
    path('passengers-crud/', views.passenger_list, name='passenger_list'),
    path('passengers-crud/create/', views.passenger_create, name='passenger_create'),
    path('passengers-crud/<int:passenger_id>/update/', views.passenger_update, name='passenger_update'),
    path('passengers-crud/<int:passenger_id>/delete/', views.passenger_delete, name='passenger_delete'),

    # CRUD для билетов
    path('tickets-crud/', views.ticket_list, name='ticket_list'),
    path('tickets-crud/create/', views.ticket_create, name='ticket_create'),
    path('tickets-crud/<int:ticket_id>/update/', views.ticket_update, name='ticket_update'),
    path('tickets-crud/<int:ticket_id>/delete/', views.ticket_delete, name='ticket_delete'),
]