from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from .serializers import RoomSerializers
from .models import Room , Category , Membership
from authentication.models import User
from .permissions import IsAdmin

@api_view(["GET"])
def Home(request):
    return Response({"success" : "base is working"})

class PrivateMeetViewSet(APIView):
    # permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializers
    def get (self, request):
        user = User.objects.get(username = request.user.username)
        userRoomsIds = Membership.objects.filter(member_id = user.id , is_member = True)
        IDs = []
        for roomId in userRoomsIds:
            IDs.append(roomId.room_id)
        userRooms = Room.objects.filter(id__in = IDs)
        serializer_all = RoomSerializers(instance=userRooms , many = True)
        return Response({"success" : f"{serializer_all.data}"} , 202)
class PublicMeetViewSet(APIView):
    permission_classes = [IsAuthenticated] # check is authenticated
    serializers = RoomSerializers
    def get (self, request):
        queryset = Room.objects.all()
        all_serializers = RoomSerializers(instance= queryset , many = True)
        return Response({"success" : f"{all_serializers.data}"} , 202)
    def post (self, request):
        room_serializers = RoomSerializers(data = request.data)
        if room_serializers.is_valid():
            room = room_serializers.save()
            for tag_id in request.data.get('categories'):
                try:
                    cate = Category.objects.get(id=tag_id)
                    room.categories.add(cate)
                except cate.DoesNotExist:
                    raise cate.NotFound()

            return Response({"successfully added!"} , 202)
        else :
            return Response({"Failed to add"})
class PublicMeetDeleteUpdate(APIView):
    # if admin 
    serializer_class  = RoomSerializers
    permission_classes = [IsAdmin , IsAuthenticated] # check is authenticated & check the user sends & add the creator 
    def put (self, request , room_id):
        room = get_object_or_404(Room , id = room_id)
        self.check_object_permissions(request, room)
        car_serializer = RoomSerializers(
            instance= room ,
            data= request.data,
            partial = True
        )
        if car_serializer.is_valid():
            car_serializer.save()
            return Response({"successfully" : "added!"} , 202)
        return Response({"message" : car_serializer.errors})
    def delete (self, request , room_id):
        room = get_object_or_404(Room , id = room_id)
        self.check_object_permissions(request , room)
        room.delete()
        return Response({"succsess" : "deleted!"} , 204)