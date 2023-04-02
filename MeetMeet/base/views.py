from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE, HTTP_201_CREATED, HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_400_BAD_REQUEST
from .serializers import RoomSerializers, RoomCardSerializers, UserSerializer
from .models import Room, Category, Membership
from authentication.models import User
from .permissions import IsAdmin
import datetime
from django.db.models import F
from django.db.models import Count
from rest_framework.pagination import PageNumberPagination


@api_view(["GET"])
def Home(request):
    return Response({"success": "base is working"})


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def Profile(request):
    user = request.user
    if request.method == 'GET':
        jsonResponse = UserSerializer(
            user, fields=["username", "email", "first_name", "last_name", "bio"]).data
        return Response(jsonResponse)

    if request.method == 'PUT':
        data = UserSerializer(instance=user, data=request.data, partial=True)
        if data.is_valid():
            err = data.save()
            if err == -1:
                return Response({"message": "current password is incorrect"}, status=HTTP_400_BAD_REQUEST)
        jsonResponse = UserSerializer(
            user, fields=["username", "email", "first_name", "last_name", "bio"]).data
        return Response({"message": "profile edited successfully", "data": jsonResponse}, status=HTTP_200_OK)


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
    # permission_classes = [IsAuthenticated]  # check is authenticated
    serializers = RoomSerializers

    def get(self, request):
        # filter by category & time period & number of members

        # first need to filter valid events (events that have not started yet)
        rooms = Room.objects.filter(
            start_date__gte=datetime.datetime.now().date())
        # ---------------------filter--------------------
        # getting possible filter params
        categories = request.GET.getlist('categories')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        member_count = request.GET.get('member_count')

        # checking if param exists or not and if exists do the filtering
        if len(categories) != 0:
            rooms = rooms.filter(categories__name__in=categories)
        if start_date is not None:
            rooms = rooms.filter(start_date__gte=start_date)
        if end_date is not None:
            rooms = rooms.filter(end_date__lte=end_date)
        if member_count is not None:
            member_count = int(member_count)
            rooms = rooms.filter(maximum_member_count=member_count)

        # -------------------- sort----------------------
        order = request.GET.get('order')
        # getting sort param from url
        sort = request.GET.get('sort')

        if sort is not None:
            if sort == 'time':
                if order == '1':
                    rooms = rooms.order_by('start_date')
                else:
                    rooms = rooms.order_by('-start_date')

            if sort == "duration":
                rooms = rooms.annotate(
                    sort_param=F('end_date')-F('start_date'))
                if order == '1':
                    rooms = rooms.order_by('sort_param')
                else:
                    rooms = rooms.order_by('-sort_param')

            if sort == 'capacity':
                rooms = rooms.annotate(sort_param=F(
                    'maximum_member_count')-Count('members'))
                if order == '1':
                    rooms = rooms.order_by('sort_param')
                else:
                    rooms = rooms.order_by('-sort_param')
                    
    # -------------------pagination---------------------------

        paginator = PageNumberPagination()
        paginator.page_size = 10
        jsonResponsePaginated = paginator.paginate_queryset(rooms, request)
        jsonResponse = RoomCardSerializers(
            jsonResponsePaginated, many=True).data
        return paginator.get_paginated_response(jsonResponse)

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
