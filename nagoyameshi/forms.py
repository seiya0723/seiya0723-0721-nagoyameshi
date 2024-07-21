from django import forms
from .models import Review, Reservation, Restaurant
from django.utils import timezone
from django.utils.timezone import localtime
from django.core.exceptions import ValidationError

class ReviewForm(forms.ModelForm):

    class Meta:
        model = Review
        fields = [ 'restaurant_id', 'user_id', 'number_of_stars', 'comment', 'visited_date' ]


class ReservationForm(forms.ModelForm):

    class Meta:
        model = Reservation
        fields = ['user_id', 'restaurant_id', 'reservation_datetime', 'number_of_persons', 'comment']

class RestaurantFloorPriceForm(forms.ModelForm):

    class Meta:
        model = Restaurant
        fields = ['floor_price']

class RestaurantMaximumPriceForm(forms.ModelForm):

    class Meta:
        model = Restaurant
        fields = ['maximum_price']