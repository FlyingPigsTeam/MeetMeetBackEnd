from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def Home(request):
    return Response({"success" : "base is working"})