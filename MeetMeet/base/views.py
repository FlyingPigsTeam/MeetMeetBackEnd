
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.status import HTTP_406_NOT_ACCEPTABLE, HTTP_201_CREATED, HTTP_200_OK, HTTP_202_ACCEPTED, HTTP_404_NOT_FOUND,  HTTP_400_BAD_REQUEST
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import Q, Count
from .serializers import RoomSerializers, MembershipSerializer, UserSerializer, RoomDynamicSerializer, RoomCardSerializers, ProfileSerializer, ShowMembershipSerializer, TaskSerializerDynamic, TaskSerializer, categoriesSerializers
from .models import Room, Category, Membership, Task, BriefPlan
from authentication.models import User
from .permissions import IsAdmin
import base64
import datetime
from django.db.models import F
from rest_framework.pagination import PageNumberPagination
import os

MAIN_URL = 'meet-meet.ir'


def save_file_to_server(file_data, where, name):
    # create a file system storage object
    fs = FileSystemStorage(location=f'{settings.MEDIA_ROOT}/{where}')
    # save the file data to the media folder
    file_name = fs.save(name, file_data)
    # get the file url
    file_url = fs.url(file_name)
    # return the file url
    return file_name


def delete_file_in_server(path):
    if os.path.exists(path):
        os.remove(path)
        return True
    else:
        return True


@api_view(["POST", "PUT"])
@permission_classes([IsAuthenticated, IsAdmin])
def upload_image(request):  # have params (where , id) => profile , brief_plan , room
    try:
        where = request.GET.get('where')
    except:
        return Response({"fail": "bad parames"}, status=HTTP_400_BAD_REQUEST)
    if where == "profile":  # mediafiels/profile/id.typefile
        try:
            id = request.user.id
        except:
            return Response({"fail": "bad parames"}, status=HTTP_400_BAD_REQUEST)
        if request.user.id != id:
            return Response({"fail": "access denied"}, status=HTTP_406_NOT_ACCEPTABLE)
        delete_file_in_server(f'{settings.MEDIA_ROOT}/{where}/{id}.PNG')
        delete_file_in_server(f'{settings.MEDIA_ROOT}/{where}/{id}.JPEG')
        delete_file_in_server(f'{settings.MEDIA_ROOT}/{where}/{id}.JPG')
        file_data = request.data.get('image')
        file_type = file_data.name.split('.')[1]
        file_path = save_file_to_server(
            file_data, "profile/", f'{id}.{file_type}')
        # must changed for different where!
        User.objects.filter(pk=id).update(
            picture_path=f"http://{MAIN_URL}/media/profile/{file_path}")
        return Response({"success": "file successfully added"}, status=HTTP_201_CREATED)
    elif where == "room":  # mediafiels/room/id.typefile
        try:
            id = int(request.GET.get("id"))
        except:
            return Response({"fail": "bad parames"}, status=HTTP_400_BAD_REQUEST)  
        theUser = get_object_or_404(Membership , room_id = id , member_id = request.user.id )
        if theUser.is_owner == False :
            return Response({"fail": "access denied"}, status=HTTP_406_NOT_ACCEPTABLE)
        delete_file_in_server(f'{settings.MEDIA_ROOT}/{where}/{id}.PNG') 
        delete_file_in_server(f'{settings.MEDIA_ROOT}/{where}/{id}.JPEG')
        delete_file_in_server(f'{settings.MEDIA_ROOT}/{where}/{id}.JPG')
        file_data = request.data.get('image')
        file_type = file_data.name.split('.')[1]
        file_path = save_file_to_server(
            file_data, "room/", f'{id}.{file_type}')
        # must changed for different where!
        Room.objects.filter(pk=id).update(
            main_picture_path=f"http://{MAIN_URL}/media/room/{file_path}")
        return Response({"success": "file successfully added"}, status=HTTP_201_CREATED)
    elif where == "brief_plan" : # mediafiels/brief_plan/room_id/id.typefile
        try:
            id = int(request.GET.get("id"))
            room_id = int(request.GET.get("room_id"))
        except:
            return Response({"fail": "bad parames"}, status=HTTP_400_BAD_REQUEST)  
        theUser = get_object_or_404(Membership , room_id = room_id , member_id = request.user.id )
        if theUser.is_owner == False :
            return Response({"fail": "access denied"}, status=HTTP_406_NOT_ACCEPTABLE)  
        delete_file_in_server(f'{settings.MEDIA_ROOT}/{where}/{room_id}/{id}.PNG') 
        delete_file_in_server(f'{settings.MEDIA_ROOT}/{where}/{room_id}/{id}.JPEG')
        delete_file_in_server(f'{settings.MEDIA_ROOT}/{where}/{room_id}/{id}.JPG')
        file_data = request.data.get('image')
        file_type = file_data.name.split('.')[1]
        file_path = save_file_to_server(
            file_data, f"brief_plan/{room_id}/", f'{id}.{file_type}')
        # must changed for different where!
        BriefPlan.objects.filter(pk=id).update(
            picture=f"http://{MAIN_URL}/media/brief_plan/{room_id}/{file_path}")
        return Response({"success": "file successfully added"}, status=HTTP_201_CREATED)
    else:
        return Response({"fail": "bad params"} , status=HTTP_400_BAD_REQUEST)
    

# @api_view(["DELETE"])
# @permission_classes([IsAuthenticated])
# def remove_image(request):
#     delete_file_in_server(f'{settings.MEDIA_ROOT}/{where}/{id}.PNG')


@api_view(["GET"])
def Home(request):
    return Response({"success": "base is working"})


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def Profile(request):
    user = request.user
    if request.method == 'GET':
        jsonResponse = ProfileSerializer(
            user, fields=["username", "email", "first_name", "last_name", "bio", "picture_path"]).data
        return Response(jsonResponse)

    if request.method == 'PUT':
        data = ProfileSerializer(
            instance=user, data=request.data, partial=True)
        if data.is_valid():
            err = data.save()
            if err == -1:
                return Response({"message": "current password is incorrect"}, status=HTTP_400_BAD_REQUEST)
        jsonResponse = ProfileSerializer(
            user, fields=["username", "email", "first_name", "last_name", "bio"]).data
        return Response({"message": "profile edited successfully", "data": jsonResponse}, status=HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def randomlinks(request, hashid):
    try:
        room_id_version = base64.b64decode(hashid).decode("utf-8")
        listof = room_id_version.split('X')
        try:
            room_id = int(listof[0])
            version = listof[1]
        except:
            return Response({"fail": "wrong link"}, status=HTTP_406_NOT_ACCEPTABLE)
    except:
        return Response({"fail": "wrong link"}, status=HTTP_406_NOT_ACCEPTABLE)
    room = get_object_or_404(Room, id=room_id)
    user_id = request.user.id
    if Membership.objects.filter(room_id=room_id, member_id=user_id , is_member = True).exists():
        return Response({"fail": "already joined" , "id" : room_id}, status=HTTP_406_NOT_ACCEPTABLE)
    if room.link == hashid:
        all_serializers = RoomDynamicSerializer(
            room, context={'request': request, 'room_id': room_id}, fields=("title",  "start_date" , "end_date", "description", "categories", "main_picture_path" , "id" , "is_premium" , "room_type" , "open_status"))
        return Response(all_serializers.data, status=HTTP_202_ACCEPTED)
    else:
        return Response({"fail": "wrong link"}, status=HTTP_406_NOT_ACCEPTABLE)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def userInfo(request, username):  # get the info of the user
    user = get_object_or_404(User, username=username)
    user_serializer = UserSerializer(user)
    return Response(user_serializer.data, status=HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def userUpdate(request):
    id = request.user.id
    try:
        User.objects.filter(pk=id).update(usertype=1)
    except:
        return Response({"fail":"User not found"} , status=HTTP_404_NOT_FOUND)
    return Response({"success": "user promoted successfully"} , status=HTTP_200_OK)


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
        serializer_all = RoomDynamicSerializer(instance=userRooms, context={'request': request},  many=True, fields=(
            "id", "title", "description", "main_picture_path", "is_admin"))
        return Response(serializer_all.data, status=HTTP_200_OK)


class PublicMeetViewSet(APIView):
    permission_classes = [IsAuthenticated]
    serializers = RoomSerializers

    def get(self, request): # get all or some rooms - have params (room_name)
        room_name = request.GET.get('room_name')
        if room_name is None:
            # filter by category & time period & number of members

            # first need to filter valid events (events that have not started yet)
            rooms = Room.objects.filter(
                start_date__gte=datetime.datetime.now().date(), room_type=1)
            # rooms = Room.objects.all()
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
                    # rooms = rooms.annotate(sort_param=F(
                    #     'maximum_member_count')-Count('members'))
                    rooms = rooms.filter(membership__is_member=True).annotate(
                        sort_param=F('maximum_member_count')-Count('membership'))
                    if order == '1':
                        rooms = rooms.order_by('sort_param')
                        for room in rooms:
                            print(room.sort_param)
                    else:
                        rooms = rooms.order_by('-sort_param')

        # -------------------pagination---------------------------

            paginator = PageNumberPagination()
            paginator.page_size = 10
            jsonResponsePaginated = paginator.paginate_queryset(rooms, request)
            jsonResponse = RoomCardSerializers(
                jsonResponsePaginated, many=True).data
            return paginator.get_paginated_response(jsonResponse)
        else : 
            try :
                rooms = Room.objects.filter(title__startswith = room_name)
            except : 
                return Response({'fail' : 'Room not found'} , status=HTTP_404_NOT_FOUND)
            # breakpoint()
            paginator = PageNumberPagination()
            paginator.page_size = 10
            jsonResponsePaginated = paginator.paginate_queryset(rooms, request)
            jsonResponse = RoomCardSerializers(
                jsonResponsePaginated, many=True).data
            return paginator.get_paginated_response(jsonResponse)

    def post(self, request):  # create a room
        # breakpoint()
        if request.data["is_premium"] == 1 :
            if request.user.usertype == 0 : 
                return Response({'fail' : 'access denied'} , status=HTTP_406_NOT_ACCEPTABLE)
            if int(request.data["maximum_member_count"]) > 50 : 
                return Response({'fail' : 'maximum_member_count most lower 50'} , status=HTTP_400_BAD_REQUEST)
        if request.data["is_premium"] == 0 and int( request.data['maximum_member_count'] ) > 10 :
            return Response({'fail' : 'maximum_member_count most be lower 10'} , status= HTTP_406_NOT_ACCEPTABLE)
        room_serializers = RoomSerializers(data=request.data)
        if room_serializers.is_valid():
            room = room_serializers.save()
            data_string = str(room.id) + "X01"
            data_bytes = data_string.encode("utf-8")
            # hashing by id + X0x , x = version of hashing
            link_created = base64.b64encode(data_bytes)
            listofparams = link_created.decode("utf-8").split("'")
            Room.objects.filter(pk=room.id).update(link=listofparams[0])
            owner = Membership.objects.create(
                room_id=room.id, is_owner=True, is_member=True, member_id=request.user.id, is_requested=False, request_status=3)
            obj= Room.objects.last()
            # breakpoint()
            return Response({"success": link_created , "id" : obj.id }, status=HTTP_201_CREATED)
        else:
            return Response({"fail": "not valid data"}, status=HTTP_406_NOT_ACCEPTABLE)


class PublicMeetDeleteUpdate(APIView):
    serializer_class = RoomSerializers
    # check is authenticated & check the user sends & add the creator
    permission_classes = [IsAdmin, IsAuthenticated]

    def post(self, request, room_id):  # join room from main page
        user_id = request.user.id
        if Membership.objects.filter(room_id=room_id, member_id=user_id , is_member = True).exists():
            return Response({"fail": "already joined"}, status=HTTP_406_NOT_ACCEPTABLE)
        try:
            Membership.objects.create(member_id=user_id, room_id=room_id,
                                      is_owner=False, is_member=False, is_requested=True, request_status=0)
        except:
            Response({"fail": "already joined"},
                     status=HTTP_406_NOT_ACCEPTABLE)
        return Response({"success": "user request sent"}, status=HTTP_202_ACCEPTED)

    def get(self, request, room_id):  # see the room details
        if Membership.objects.filter(member_id=request.user.id, room_id=room_id , is_member = True).exists() == False:
            room = get_object_or_404(Room, id=room_id)
            all_serializers = RoomDynamicSerializer(
                room,  context={'request': request, 'room_id': room_id}, fields=("title",  "is_premium",  "start_date", "end_date", "description", "categories", "room_members", "maximum_member_count" , "tasks"))
            return Response(all_serializers.data, status=HTTP_202_ACCEPTED)
        else:
            room = get_object_or_404(Room, id=room_id)
            all_serializers = RoomDynamicSerializer(
                room,  context={'request': request, 'room_id': room_id})
            return Response(all_serializers.data, status=HTTP_202_ACCEPTED)

    def put(self, request, room_id):  # change the room / link of the room - have params (link)
        link = request.GET.get('link')
        if link is None:  # change infos
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
            return Response({"fail": car_serializer.errors}, status=HTTP_406_NOT_ACCEPTABLE)
        else:  # change the link
            room = get_object_or_404(Room, id=room_id)
            self.check_object_permissions(request, room)
            hashid = room.link
            room_id_version = base64.b64decode(hashid).decode("utf-8")
            listof = room_id_version.split('X')
            room_id = int(listof[0])
            version = listof[1]
            data_string = str(room_id) + 'X' + str(int(version) + 1)
            data_bytes = data_string.encode("utf-8")
            # hashing by id + X0x , x = version of hashing
            link_created = base64.b64encode(data_bytes)
            listofparams = link_created.decode("utf-8").split("'")
            Room.objects.filter(pk=room.id).update(link=listofparams[0])
            return Response({"success": link_created}, status=HTTP_201_CREATED)

    def delete(self, request, room_id):  # delete the room
        room = get_object_or_404(Room, id=room_id)
        self.check_object_permissions(request, room)
        room.delete()
        delete_file_in_server(f'{settings.MEDIA_ROOT}/room/{room_id}.PNG') # the foemat of the file may cuz problems
        delete_file_in_server(f'{settings.MEDIA_ROOT}/room/{room_id}.JPEG')
        delete_file_in_server(f'{settings.MEDIA_ROOT}/room/{room_id}.JPG')
        return Response({"success": "deleted!"}, status=HTTP_200_OK)


class ResponseToRequests(APIView):  # join the room must add
    permission_classes = [IsAdmin, IsAuthenticated]
    serializer_class = MembershipSerializer

    # def permission_classes(self, request, room):
    def post(self, request, room_id):  # add user to the room by owner - have params(username)
        username = request.GET.get('username')
        user = get_object_or_404(User, username=username)
        room = get_object_or_404(Room, id=room_id)
        self.check_object_permissions(request, room)
        maxmember = room.maximum_member_count
        if maxmember == Membership.objects.filter(room_id=room_id, is_member=True).count():
            return Response({"faild": "room is full"}, status=HTTP_406_NOT_ACCEPTABLE)
        if Membership.objects.filter(room_id=room_id, member_id=user.id , is_member = True).exists():
            return Response({"fail": "already joined"}, status=HTTP_406_NOT_ACCEPTABLE)
        Membership.objects.create(member_id=user.id, room_id=room_id,
                                  is_owner=False, is_member=True, is_requested=False, request_status=0)
        return Response({"success": "user added"}, status=HTTP_201_CREATED)

    def get(self, request, room_id): # get all of requests or members - have params(show_members , username)
        show_members = int(request.GET.get('show_members'))
        if show_members == 0:  # show the requests
            try:
                criterion1 = Q(room_id=room_id)
                criterion2 = Q(is_requested=True)
                requests = Membership.objects.filter(criterion2 & criterion1)
            except:
                return Response({"fail": "not found any requests"}, status=HTTP_404_NOT_FOUND)
            request_serializer = MembershipSerializer(requests, many=True)
            return Response(request_serializer.data, status=HTTP_202_ACCEPTED)
        else:  # show the members
            username = request.GET.get('username')
            if username is None:
                try:
                    members = Membership.objects.filter(
                        room_id=room_id).order_by('-is_owner', '-is_requested')
                except:
                    return Response({"fail": "not found any requests"}, status=HTTP_404_NOT_FOUND)
                entriesInString = request.GET.get('entries')
                entries = 0
                if entriesInString is None :
                    entries = 10
                else :
                    entries = int(entriesInString)
                paginator = PageNumberPagination()
                paginator.page_size = entries
                jsonResponsePaginated = paginator.paginate_queryset(members, request)
                member_serializer = ShowMembershipSerializer(
                    jsonResponsePaginated, many=True)
                return paginator.get_paginated_response(member_serializer.data)
            else:
                try:
                    users = User.objects.filter(username__startswith=username)
                except:
                    Response({"fail": "not found any member"},
                             status=HTTP_404_NOT_FOUND)
                user_serializer = UserSerializer(users, many=True, fields = ("first_name" , "last_name" , "picture_path" , "username" , "id"))
                return Response(user_serializer.data, status=HTTP_200_OK)

    def put(self, request, room_id): # accept or reject requests or promote a member - have params(add ,request_id )
        try:  
            add = request.GET.get('add')
        except:
            return Response({"fail": "bad params"}, status=HTTP_400_BAD_REQUEST)
        if add == '1':
            maxmember = room.maximum_member_count
            if maxmember == Membership.objects.filter(room_id=room_id, is_member=True).count():
                return Response({"faild": "room is full"}, status=HTTP_406_NOT_ACCEPTABLE)
            if Membership.objects.filter(room_id=room_id, member_id=request_id , is_member = True).exists():
                return Response({"fail": "already joined"}, status=HTTP_406_NOT_ACCEPTABLE)
        request_id = request.GET.get('request_id')
        room = get_object_or_404(Room, id=room_id)
        self.check_object_permissions(request, room)
        try:
            if add == '1':
                request_member = Membership.objects.get(member_id=int(request_id) , room_id=room_id)
            else : 
                request_member = Membership.objects.get(pk=int(request_id))
        except:
            return Response({"fail": "not found any request or member"}, status=HTTP_404_NOT_FOUND)
        requests_serializer = MembershipSerializer(
            instance=request_member, partial=True, data=request.data)
        if requests_serializer.is_valid():
            requests_serializer.save()
            # breakpoint()
            return Response({"success": "status changed successfully"}, status=HTTP_200_OK)
        else:
            return Response({"fail": requests_serializer.errors}, status=HTTP_406_NOT_ACCEPTABLE)

    def delete(self, request, room_id):  # delete a request or member from history or from room
        request_id = request.GET.get('request_id')
        room = get_object_or_404(Room, id=room_id)
        self.check_object_permissions(request, room)
        try:
            request_member = Membership.objects.get(pk=request_id)
        except:
            return Response({"fail": "not found any request"}, status=HTTP_404_NOT_FOUND)
        request_member.delete()
        return Response({"success": "deleted"}, status=HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def AlluserTasks(request):
    try:
        tasks = Task.objects.filter(user_id=request.user.id)
        tasks_serializer = TaskSerializerDynamic(tasks, many=True)
    except:
        return Response({"fail": "not found any tasks"}, status=HTTP_404_NOT_FOUND)
    return Response(tasks_serializer.data, status=HTTP_200_OK)


class taskResponse(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializerDynamic

    def get(self, request, room_id):  # get all or one task or an user task - have params(all , task_id , task_name)
        show_all = request.GET.get('show_all')
        task_name = request.GET.get("task_name")
        if task_name is not None:
            try :
                tasks = Task.objects.filter(title__startswith = task_name)
            except : 
                return Response({'fail' : 'Room not found'} , status=HTTP_404_NOT_FOUND)
            # breakpoint()
            serializer_all = TaskSerializerDynamic(tasks , many=True , fields = ("title","priority" , "description" , "done"))
            return Response(serializer_all.data, status=HTTP_200_OK)
        if show_all is not None:
            try:
                tasks = Task.objects.filter(room_id=room_id)
                tasks_serializer = TaskSerializerDynamic(tasks, many=True, fields=(
                    "id", "title", "priority", "description", "done", "user"))
            except:
                return Response({"fail": "not found any tasks"}, status=HTTP_404_NOT_FOUND)
            return Response(tasks_serializer.data, status=HTTP_200_OK)
        else:
            try:
                task_id = int(request.GET.get('task_id'))
            except:
                return Response({"fail": "params are not ok"}, status=HTTP_400_BAD_REQUEST)
            task = get_object_or_404(Task, id=task_id, room_id=room_id)
            tasks_serializer = TaskSerializerDynamic(task, fields=(
                "id", "title", "priority", "description", "done", "user"))
            return Response(tasks_serializer.data, status=HTTP_200_OK)

    def post(self, request, room_id): # have some hard codded thing for max of tasks
        room = get_object_or_404(Room, id=room_id)
        self.check_object_permissions(request, room)
        if room.is_premium == 1 and Task.objects.filter(room_id=room_id).count() > 30 : 
            return Response({"fail": "reach the limit of max number of tasks"}, status=HTTP_400_BAD_REQUEST)
        if room.is_premium == 0 and Task.objects.filter(room_id=room_id).count() > 15 :
            return Response({"fail": "reach the limit of max number of tasks"}, status=HTTP_400_BAD_REQUEST)
        task_serializer = TaskSerializer(data=request.data)
        if task_serializer.is_valid():
            task_serializer.save()
            return Response(task_serializer.data, status=HTTP_200_OK)
        else:
            return Response({"fail": "not valid data"}, status=HTTP_406_NOT_ACCEPTABLE)

    def put(self, request, room_id):  # have paramns (task_id)
        try:
            task_id = int(request.GET.get('task_id'))
        except:
            return Response({"fial": "bad params"}, status=HTTP_400_BAD_REQUEST)
        room = get_object_or_404(Room, id=room_id)
        task = get_object_or_404(Task, id=task_id)
        self.check_object_permissions(request, room)
        task_serializer = TaskSerializer(
            instance=task,
            data=request.data,
            partial=True,
        )
        # obj = User.objects.get(pk = request.data["user"] )
        # Task.objects.filter(id = task_id).update(user = obj)
        if task_serializer.is_valid():
            task_serializer.save()
            return Response({"success": "changed"}, status=HTTP_202_ACCEPTED)
        return Response({"fail": task_serializer.errors}, status=HTTP_406_NOT_ACCEPTABLE)

    def delete(self, request, room_id):  # have paramns (task_id)
        try:
            task_id = int(request.GET.get('task_id'))
        except:
            return Response({"fial": "bad params"}, status=HTTP_400_BAD_REQUEST)
        room = get_object_or_404(Room, id=room_id)
        self.check_object_permissions(request, room)
        try:
            task = Task.objects.get(id=task_id)
        except:
            return Response({"fail": "not found any request"}, status=HTTP_404_NOT_FOUND)
        task.delete()
        return Response({"success": "deleted"}, status=HTTP_200_OK)


@api_view(['POST', 'GET'])
def CRUDCategorey(request):
    if request.method == "GET":
        data = Category.objects.all()
        jsonResponse = categoriesSerializers(
            data, many=True, fields=["name"]).data
        return Response(jsonResponse)

    if request.method == "POST":
        data = categoriesSerializers(data=request.data, fields=["name"])
        if data.is_valid():
            if Category.objects.filter(name=request.data["name"]).exists():
                return Response({"error": "category with this name already exists"}, status=HTTP_400_BAD_REQUEST)
            else:
                data.save()
        else:
            return Response({"error": "invalid input"}, status=HTTP_400_BAD_REQUEST)
        return Response({"success": "category added"})
