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
    current_password = serializers.CharField(
        max_length=68, min_length=3)
    new_password = serializers.CharField(
        max_length=68, min_length=3)
    class Meta:
        model = auth_models.User
        fields=("username" , "email" , "first_name" , "last_name" , "bio" , "current_password" , "new_password")
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
# class TaskSerializer(DynamicFieldsModelSerializer):
#     class Meta:
#         models = models.Task
#         fields = "__all__"
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
        
        instance.save()
        
        return instance

class RoomDynamicSerializer(DynamicFieldsModelSerializer):
    categories = categoriesSerializers(many=True , read_only=True)
    members = UserSerializer(many=True , read_only=True , fields = ("username" , "picture_path" , "bio")) # fields = ("username", "password")
    is_admin = serializers.SerializerMethodField()
    # tasks = TaskSerializer(many=True , read_only=True , fields = ("title" , "priority"))
    class Meta:
        model = models.Room
        fields = "__all__"
    def get_is_admin(self, instance):
        return instance.members.through.objects.filter(member_id = self.context['request'].user.id , room_id = self.context['room_id'] ).values("is_owner")[0]["is_owner"]
class MembershipSerializer(serializers.ModelSerializer):
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
        return instance.members.count()