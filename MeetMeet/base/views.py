from rest_framework.decorators import api_view , authentication_classes , permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE , HTTP_201_CREATED , HTTP_200_OK, HTTP_202_ACCEPTED , HTTP_404_NOT_FOUND
from django.db.models import Q , Count
from .serializers import RoomSerializers , MembershipSerializer , UserSerializer , RoomDynamicSerializer
from .models import Room , Category , Membership
from authentication.models import User
from .permissions import IsAdmin
import base64

@api_view(["GET"])
def Home(request):
    return Response({"success" : "base is working"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def randomlinks(request , hashid):
    try:
        room_id_version = base64.b64decode(hashid).decode("utf-8")
        listof = room_id_version.split('X')
        try:
            room_id = int(listof[0])
            version = listof[1]
        except:
            return Response({"fail" : "wrong link"},status=HTTP_406_NOT_ACCEPTABLE)
    except:
        return Response({"fail" : "wrong link"},status=HTTP_406_NOT_ACCEPTABLE)
    room = get_object_or_404(Room, id=room_id)
    if room.link == hashid:
        all_serializers = RoomDynamicSerializer(room)
        return Response(all_serializers.data, status=HTTP_202_ACCEPTED)
    else:
        return Response({"fail" : "wrong link"},status=HTTP_406_NOT_ACCEPTABLE)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def userInfo(request , username): # get the info of the user
    user = get_object_or_404(User, username=username)
    user_serializer = UserSerializer(user)
    return Response(user_serializer.data, status=HTTP_200_OK)


class PrivateMeetViewSet(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RoomSerializers
    def get (self, request):
        # user = User.objects.get(username = request.user.id)
        userRoomsIds = Membership.objects.filter(member_id = request.user.id , is_member = True)
        IDs = []
        for roomId in userRoomsIds:
            IDs.append(roomId.room_id)
        userRooms = Room.objects.filter(id__in = IDs)
        serializer_all = RoomSerializers(instance=userRooms , many = True)
        return Response( serializer_all.data , status=HTTP_200_OK)
class PublicMeetViewSet(APIView):
    permission_classes = [IsAuthenticated]
    serializers = RoomSerializers 
    def get (self, request): # get all of rooms    
        try:
            queryset = Room.objects.filter(open_status = 1)
            all_serializers = RoomDynamicSerializer(queryset , many = True , fields = ("title"  ,"room_type" ,"link" , "password" , "description" , "start_date" , "end_date" , "maximum_member_count" , "open_status" , "categories" , "members" ))
            return Response(all_serializers.data , status=HTTP_202_ACCEPTED)
        except all_serializers.DoesNotExist:
            return Response({"fail" : "Not found"} , status=HTTP_404_NOT_FOUND)
    def post (self, request): # create a room
        room_serializers = RoomSerializers(data=request.data)
        if room_serializers.is_valid():
            room = room_serializers.save()
            data_string = str(room.id) + "X01"
            data_bytes = data_string.encode("utf-8")
            link_created = base64.b64encode( data_bytes ) # hashing by id + X0x , x = version of hashing
            listofparams = link_created.decode("utf-8").split("'")
            Room.objects.filter(pk=room.id).update(link = listofparams[0])
            owner = Membership.objects.create(
                room_id=room.id, is_owner=True, is_member=True, member_id=request.user.id, is_requested=False, request_status=3)
            return Response({"success": link_created}, status=HTTP_201_CREATED)
        else:
            return Response({"fail": "not valid data"}, status=HTTP_406_NOT_ACCEPTABLE)

class PublicMeetDeleteUpdate(APIView):
    serializer_class  = RoomSerializers
    permission_classes = [IsAdmin , IsAuthenticated] # check is authenticated & check the user sends & add the creator 
    def post (self, request , room_id): # join room
        user_id = request.user.id
        if Membership.objects.filter(room_id=room_id ,member_id = user_id ).exists():
            return Response({"fail": "already joined"}, status=HTTP_406_NOT_ACCEPTABLE)
        try :
            Membership.objects.create(member_id = user_id , room_id = room_id , is_owner = False , is_member = False , is_requested = True , request_status = 0 )
        except :
            Response({"fail": "already joined"}, status=HTTP_406_NOT_ACCEPTABLE)
        return Response({"success" : "user request sent"} , status=HTTP_202_ACCEPTED)
    def get (self, request , room_id): # see the room details
        room = get_object_or_404(Room, id=room_id)
        all_serializers = RoomDynamicSerializer(room)
        return Response(all_serializers.data, status=HTTP_202_ACCEPTED)
    def put (self, request , room_id): # change the room / link of the room - have params (link)
        link = request.GET.get('link')
        if link is None: # change infos
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
            return Response({"fail" : car_serializer.errors} , status=HTTP_406_NOT_ACCEPTABLE)
        else: # change the link
            room = get_object_or_404(Room , id = room_id)
            self.check_object_permissions(request, room)
            hashid = room.link
            room_id_version = base64.b64decode(hashid).decode("utf-8")
            listof = room_id_version.split('X')
            room_id = int(listof[0])
            version = listof[1]
            data_string = str(room_id) + 'X' + str(int(version) + 1) 
            data_bytes = data_string.encode("utf-8")
            link_created = base64.b64encode( data_bytes ) # hashing by id + X0x , x = version of hashing
            listofparams = link_created.decode("utf-8").split("'")
            Room.objects.filter(pk=room.id).update(link = listofparams[0])
            return Response({"success": link_created}, status=HTTP_201_CREATED)
    def delete (self, request , room_id): # delete the room
        room = get_object_or_404(Room , id = room_id)
        self.check_object_permissions(request , room)
        room.delete()
        return Response({"success" : "deleted!"} , status=HTTP_200_OK)
class ResponseToRequests(APIView): # join the room must add
    permission_classes = [IsAdmin , IsAuthenticated]
    serializer_class = MembershipSerializer
    def post (self, request , room_id): # add user to the room - have params(username) 
        username = request.GET.get('username')
        user = get_object_or_404(User , username = username) 
        room = get_object_or_404(Room , id = room_id)
        maxmember = room.maximum_member_count
        if maxmember == Membership.objects.filter(room_id=room_id).count() :
            return Response({"faild" : "room is full"}, status=HTTP_406_NOT_ACCEPTABLE) 
        if Membership.objects.filter(room_id=room_id ,member_id = user.id ).exists():
            return Response({"fail": "already joined"}, status=HTTP_406_NOT_ACCEPTABLE)
        Membership.objects.create(member_id = user.id , room_id = room_id , is_owner = False , is_member = True , is_requested = False , request_status = 0 )
        return Response({"success" : "user added"} , status=HTTP_201_CREATED)
    def get (self, request , room_id): # get all of requests or members - have params(show_members , username)
        show_members = int( request.GET.get('show_members') )
        if show_members == 0: # show the requests
            try:
                criterion1 = Q(room_id=room_id )
                criterion2 = Q(is_requested = True )
                requests = Membership.objects.filter(criterion2 & criterion1)
            except:
                return Response({"fail" : "not found any requests"} , status=HTTP_404_NOT_FOUND)
            request_serializer = MembershipSerializer(requests , many = True)
            return Response(request_serializer.data , status=HTTP_202_ACCEPTED)
        else : # show the members
            username = request.GET.get('username')
            if username is None : 
                try:
                    members = Membership.objects.filter(room_id=room_id , is_member = True)
                except:
                    return Response({"fail" : "not found any requests"} , status=HTTP_404_NOT_FOUND)
                member_serializer = MembershipSerializer(members , many = True)
                return Response ( member_serializer.data , status=HTTP_200_OK )
            else:
                try:
                    users = User.objects.filter(username__icontains = username)
                except:
                    Response({"fail" : "not found any member"} , status=HTTP_404_NOT_FOUND)
                user_serializer = UserSerializer(users , many = True)
                return Response(user_serializer.data , status=HTTP_200_OK)
    def put (self, request , room_id): # accept or reject requests or add or promote a member
        request_id = request.GET.get('request_id')
        room = get_object_or_404(Room , id = room_id)
        self.check_object_permissions(request, room)   
        try:
            request_member = Membership.objects.get(member_id = request_id)
        except:
            return Response({"fail" : "not found any request"} , status=HTTP_404_NOT_FOUND)
        requests_serializer = MembershipSerializer(instance=request_member,partial = True , data=request.data)
        if requests_serializer.is_valid():
            requests_serializer.save()
            return Response({"success" : "status changed successfully"} , status=HTTP_200_OK)
        else:
            return Response({"fail" : requests_serializer.errors} , status=HTTP_406_NOT_ACCEPTABLE)
    def delete (self, request , room_id): # delete a request or member from history or from room
        request_id = request.GET.get('request_id')
        room = get_object_or_404(Room , id = room_id)
        self.check_object_permissions(request, room)   
        try:
            request_member = Membership.objects.get(member_id = request_id)
        except:
            return Response({"fail" : "not found any request"} , status=HTTP_404_NOT_FOUND)
        request_member.delete()
        return Response({"success" : "deleted"} , status=HTTP_200_OK)