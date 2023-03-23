from rest_framework.permissions import BasePermission , SAFE_METHODS
import sys
sys.path.append("..") # Adds higher directory to python modules path.
from .models import Membership
from authentication.models import User
from rest_framework.generics import get_object_or_404

class IsAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # user = User.objects.get(username = request.user.username)
        theUser = get_object_or_404(Membership , room_id = obj.id , member_id = request.user.id )
        if theUser.is_owner == True :
            return True
        return False


