from rest_framework import serializers
from . import models
from authentication import models as  auth_models

class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

class UserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = auth_models.User
        fields = "__all__"

class ProfileSerializer(DynamicFieldsModelSerializer):
    username = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    picture_path = serializers.CharField(max_length=255)
    current_password = serializers.CharField(
        max_length=68, min_length=3)
    new_password = serializers.CharField(
        max_length=68, min_length=3)
    class Meta:
        model = auth_models.User
        fields=("username" , "email" , "first_name" , "last_name" , "bio" , "current_password" , "new_password" , "picture_path")
    def update(self,instance , validated_data):
        instance.bio = validated_data.get('bio' , instance.bio)
        instance.first_name = validated_data.get('first_name' , instance.first_name)
        instance.last_name =  validated_data.get('last_name' , instance.last_name)
        password = validated_data.get("current_password")
        if password is not None:
            if not instance.check_password(password):
                return -1
            else :
                instance.set_password(validated_data.get("new_password"))
                instance.save()
                return 1

        instance.save()
        return instance
class categoriesSerializers(DynamicFieldsModelSerializer):
    class Meta:
        model = models.Category
        fields = ("name" , "id") 
class TaskSerializerDynamic(DynamicFieldsModelSerializer):
    user = UserSerializer(many = True , read_only = True , fields=("username" , "picture_path" , "bio" , "first_name" , "last_name") )
    user_picture = UserSerializer(many = True , read_only = True , fields=("username" , "picture_path" ) )
    class Meta:
        model = models.Task
        fields = "__all__" 
class TaskSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=auth_models.User.objects.all(), many=True)
    class Meta:
        model = models.Task
        fields = "__all__"  
    def create(self, validated_data):
        users_data = validated_data.pop('user' , None)
        task = models.Task.objects.create(**validated_data)
        if users_data is not None :
            task.user.set(users_data)
        return task    
    def update(self, instance, validated_data):
        users_data = validated_data.pop('user' , None)
        instance = super().update(instance, validated_data)  
        if users_data is not None :
            instance.user.set(users_data)   
        return instance 

class RoomSerializers(serializers.ModelSerializer):
    categories = categoriesSerializers(many=True ) 
    class Meta:
        model = models.Room
        fields = ("title"  ,"room_type" , "password" , "main_picture_path", "description" ,"link" , "start_date" , "end_date" , "maximum_member_count" , "open_status" , "categories" ,"is_premium"  )
    def create(self, validated_data):
        category_data = validated_data.pop('categories')
        # link = validated_data.pop("link")
        room = models.Room.objects.create(**validated_data)
        for category in category_data:
            id_category = models.Category.objects.get(name=category["name"])
            room.categories.add(id_category)
        return room    
    def update(self,instance , validated_data):
        
        categories_data = validated_data.pop('categories')
        categories = instance.categories
        cate = []
        for data in categories_data:
            cate.append(models.Category.objects.get(name=data["name"]))
        categories.set(cate)

        instance.title = validated_data.get('title' , instance.title)
        instance.room_type = validated_data.get("room_type" , instance.room_type)
        instance.link = validated_data.get('link' , instance.link)
        instance.password = validated_data.get('password' , instance.password)
        instance.description = validated_data.get('description' , instance.description)
        instance.start_date = validated_data.get('start_date' , instance.start_date)
        instance.end_date = validated_data.get('end_date' , instance.end_date)
        instance.maximum_member_count = validated_data.get('maximum_member_count' , instance.maximum_member_count)
        instance.open_status = validated_data.get("open_status" , instance.open_status)
        instance.is_premium = validated_data.get("is_premium" , instance.is_premium)
        
        instance.save()
        
        return instance

class RoomDynamicSerializer(DynamicFieldsModelSerializer):
    categories = categoriesSerializers(many=True , read_only=True)
    room_members = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    tasks = TaskSerializerDynamic(many=True , read_only=True , fields = ("title" , "priority" , "description" , "user_picture" ))
    class Meta:
        model = models.Room
        # fields = "__all__"
        exclude = ('members', )
    def get_is_admin(self, instance):
        return instance.members.through.objects.filter(member_id = self.context['request'].user.id , room_id = instance.id ).values("is_owner")[0]["is_owner"]
    def get_room_members(self, instance):
        test = instance.members.through.objects.filter(is_member = True , room_id = self.context['room_id'] ).values("member_id")
        IDs = []
        for item in test:
            IDs.append(item["member_id"])
        member_infos = auth_models.User.objects.filter(id__in = IDs)
        test_serialized = UserSerializer(member_infos , many = True ,fields = ("username" , "picture_path" , "bio"))
        return test_serialized.data
class MembershipSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True , read_only=True)
    class Meta:
        model = models.Membership
        fields = "__all__"
        
class RoomCardSerializers(DynamicFieldsModelSerializer):
    categories = categoriesSerializers(many=True , fields=["name"] ) 
    member_count = serializers.SerializerMethodField()
    class Meta:
        model = models.Room
        fields = ("id" , "title" , "maximum_member_count","start_date","end_date","main_picture_path","categories","member_count")
    def get_member_count(self, instance):
        return  models.Membership.objects.filter(room_id=instance.id, is_member=True).count()
class ShowMembershipSerializer(DynamicFieldsModelSerializer):
    member = UserSerializer(read_only = True , fields=("username" , "picture_path" , "bio" , "first_name" , "last_name") )
    class Meta:
        model = models.Membership
        fields = ["is_owner" , "is_member" , "is_requested" ,"request_status" , "member" , "id" ]