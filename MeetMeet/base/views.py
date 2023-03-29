from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE, HTTP_201_CREATED, HTTP_200_OK, HTTP_202_ACCEPTED
from .serializers import RoomSerializers
from .models import Room, Category, Membership
from authentication.models import User
from .permissions import IsAdmin


@api_view(["GET"])
def Home(request):
    return Response({"success": "base is working"})


@api_view(["POST"])
def SearchRoom(request):
    categories = request.data['categories']
    start_date = request.data['start_date']
    end_date = request.data['end_date']
    member_count = request.data['member_count']
    rooms = Room.objects.filter(Q(categories__name__in=categories) & Q(
        start_date__gte=start_date) & Q(end_date__lte=end_date)  & Q(maximum_member_count=member_count))
    
    
    jsonResponse = RoomSerializers(rooms, many=True).data
    return Response(jsonResponse)


class PrivateMeetViewSet(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializers

    def get(self, request):
        # user = User.objects.get(username = request.user.id)
        userRoomsIds = Membership.objects.filter(
            member_id=request.user.id, is_member=True)
        IDs = []
        for roomId in userRoomsIds:
            IDs.append(roomId.room_id)
        userRooms = Room.objects.filter(id__in=IDs)
        serializer_all = RoomSerializers(instance=userRooms, many=True)
        return Response(serializer_all.data, status=HTTP_200_OK)


class PublicMeetViewSet(APIView):
    permission_classes = [IsAuthenticated]  # check is authenticated
    serializers = RoomSerializers

    def get(self, request):
        queryset = Room.objects.all()
        all_serializers = RoomSerializers(queryset, many=True)
        return Response(all_serializers.data, status=HTTP_202_ACCEPTED)

    def post(self, request):
        room_serializers = RoomSerializers(data=request.data)
        if room_serializers.is_valid():
            room = room_serializers.save()
            owner = Membership.objects.create(
                room_id=room.id, is_owner=True, is_member=True, member_id=request.user.id, is_requested=False, request_status=3)
            return Response({"success": "created!"}, status=HTTP_201_CREATED)
        else:
            print(room_serializers.errors)
            return Response({"fail": "not valid data"}, status=HTTP_406_NOT_ACCEPTABLE)


class PublicMeetDeleteUpdate(APIView):
    # if admin
    serializer_class = RoomSerializers
    # check is authenticated & check the user sends & add the creator
    permission_classes = [IsAdmin, IsAuthenticated]

    def put(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        self.check_object_permissions(request, room)
        car_serializer = RoomSerializers(
            instance=room,
            data=request.data,
            partial=True
        )
        if car_serializer.is_valid():
            car_serializer.save()
            return Response({"success": "added!"}, status=HTTP_202_ACCEPTED)
        return Response({"fail": car_serializer.errors})

    def delete(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        self.check_object_permissions(request, room)
        room.delete()
        return Response({"success": "deleted!"}, status=HTTP_200_OK)
