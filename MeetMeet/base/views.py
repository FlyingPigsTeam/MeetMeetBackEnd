from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE , HTTP_201_CREATED , HTTP_200_OK, HTTP_202_ACCEPTED
from .serializers import RoomSerializers
from .models import Room , Category , Membership
from authentication.models import User
from .permissions import IsAdmin

@api_view(["GET"])
def Home(request):
    return Response({"success" : "base is working"})

class PrivateMeetViewSet(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializers
    def get (self, request):
        user = User.objects.get(username = request.user.username)
        userRoomsIds = Membership.objects.filter(member_id = user.id , is_member = True)
        IDs = []
        for roomId in userRoomsIds:
            IDs.append(roomId.room_id)
        userRooms = Room.objects.filter(id__in = IDs)
        serializer_all = RoomSerializers(instance=userRooms , many = True)
        return Response( serializer_all.data , status=HTTP_200_OK)
class PublicMeetViewSet(APIView):
    permission_classes = [IsAuthenticated] # check is authenticated
    serializers = RoomSerializers
    def get (self, request):
        queryset = Room.objects.all()
        all_serializers = RoomSerializers(queryset , many = True)
        return Response(all_serializers.data , status=HTTP_202_ACCEPTED)
    def post (self, request):
        room_serializers = RoomSerializers(data = request.data)
        if room_serializers.is_valid():
            room = room_serializers.save()
            return Response({"success" : "created!"} , status=HTTP_201_CREATED)
        else :
            return Response({"fail" : "not valid data"} , status=HTTP_406_NOT_ACCEPTABLE)
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
            return Response({"success" : "added!"} , status=HTTP_202_ACCEPTED)
        return Response({"fail" : car_serializer.errors})
    def delete (self, request , room_id):
        room = get_object_or_404(Room , id = room_id)
        self.check_object_permissions(request , room)
        room.delete()
        return Response({"success" : "deleted!"} , status=HTTP_200_OK)