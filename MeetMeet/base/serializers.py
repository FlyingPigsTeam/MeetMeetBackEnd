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
        fields = "__all__"   
class RoomSerializers(serializers.ModelSerializer):
    categories = categoriesSerializers(many=True , read_only=True)
    class Meta:
        model = models.Room
        fields = ("title"  ,"room_type" ,"link" , "password" , "description"  , "view_count", "start_date" , "end_date" , "maximum_member_count" , "open_status" , "categories" )
    # def validate(self, data):
    #     if data.get('end', 0) > data.get('maximum_price', 0):
    #         error = 'Maximum should be greater than minimum'
    #         raise serializers.ValidationError(error)

    #     return data
