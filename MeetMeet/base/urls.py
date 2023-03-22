from django.urls import path
from . import views

urlpatterns = [
    path("", views.Home),
    path("rooms" , views.PublicMeetViewSet.as_view()  ),
    path("rooms/<int:room_id>" , views.PublicMeetDeleteUpdate.as_view()),
    path("myrooms/<int:room_id>" , views.PublicMeetDeleteUpdate.as_view()),
    path("myrooms" , views.PrivateMeetViewSet.as_view()),
]
