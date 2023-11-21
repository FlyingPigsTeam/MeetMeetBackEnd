from django.urls import path
from . import views

urlpatterns = [
    path("", views.Home),
    path("upload" , views.upload_image),
    path("premium" , views.userUpdate ),
    path("rooms" , views.PublicMeetViewSet.as_view()  ),
    path("rooms/<int:room_id>" , views.PublicMeetDeleteUpdate.as_view()),
    path("rooms/<str:hashid>" , views.randomlinks),
    path("users/<str:username>" , views.userInfo),
    path("my-rooms/<int:room_id>" , views.PublicMeetDeleteUpdate.as_view()),
    path("my-rooms/<int:room_id>/requests" , views.ResponseToRequests.as_view()),
    path("my-rooms/<int:room_id>/tasks" , views.taskResponse.as_view()),
    path("my-tasks" , views.AlluserTasks),
    path("my-rooms" , views.PrivateMeetViewSet.as_view()),
    path("profile",views.Profile),
    path("category" , views.CRUDCategorey)
] 
