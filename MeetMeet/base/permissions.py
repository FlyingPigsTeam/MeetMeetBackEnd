from rest_framework.permissions import BasePermission , SAFE_METHODS
import sys
sys.path.append("..") # Adds higher directory to python modules path.
from .models import Membership
from authentication.models import User

class IsAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = User.objects.get(username = request.user.username)
        theUser = Membership.objects.filter(room_id = obj.id , member_id = user.id )
        if theUser[0].is_owner == True :
            return True
        return False


