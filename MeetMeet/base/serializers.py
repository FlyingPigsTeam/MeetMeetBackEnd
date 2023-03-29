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
        fields="__all__"     
class categoriesSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = ("name" , "id")   
class RoomSerializers(serializers.ModelSerializer):
    categories = categoriesSerializers(many=True ) 
    class Meta:
        model = models.Room
        fields = ("title"  ,"room_type" ,"link" , "password" , "description" , "start_date" , "end_date" , "maximum_member_count" , "open_status" , "categories" , "is_premium" )
    def create(self, validated_data):
        category_data = validated_data.pop('categories')
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