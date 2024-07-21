from django.urls import path
from . import views

app_name = 'nagoyameshi'
urlpatterns = [
    path('', views.index, name='index'),
    path('top/', views.top, name='top'),
    path('restaurant/<int:pk>', views.restaurant_detail, name='restaurant_detail'),
    path('restaurant/review_list/<int:pk>', views.review_list, name='review_list'),
    path('restaurant/review_form/<int:pk>', views.review_form, name='review_form'),
    path('restaurant/review_edit/<int:pk>', views.review_edit, name='review_edit'),
    path('restaurant/review_delete/<int:pk>', views.review_delete, name='review_delete'),
    path('restaurant/reservation_form/<int:pk>', views.reservation_form, name='reservation_form'),
    path('restaurant/reservation_delete/<int:pk>', views.reservation_delete, name='reservation_delete'),
    path('mypage/', views.mypage, name='mypage'),

    # サブスク関連
    path("checkout/", views.checkout, name="checkout"),
    path("success/", views.success, name="success"),
    path("portal/", views.portal, name="portal"),
    path("premium/", views.premium, name="premium"),
]
