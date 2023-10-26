import demjson
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views import View
from notifications.models import Notification

from utils.exception.types.bad_request import BadRequestException
from utils.exception.types.unauthorized import UnauthorizedException
from utils.token import get_request_user
from website.notification.dto import notification_normal
from website.views import sendNotification


class Notifications(View):
    # WS0801 send notification
    def post(self, request):
        user = get_request_user(request)
        if not user.id:
            raise UnauthorizedException()
        body = demjson.decode(request.body)
        if len(body["recipients"]) == 1 and body["recipients"][0] == -1:
            recipients = None
        else:
            recipients = User.objects.filter(id__in=body["recipients"])
        title = body["title"] if "title" in body else None
        notifications = sendNotification(user, recipients, body["content"], title=title)
        return JsonResponse({"notifications": notifications}, status=200)

    # WS0802 filter notifications
    def get(self, request):
        notifications = Notification.objects.all()
        from_person = request.GET["from"]
        to_person = request.GET["to"]
        unread = request.GET["unread"]
        page = request.GET["page"]
        pageSize = request.GET["pageSize"]
        filters = {}
        result = []
        amount = 0
        if not page:
            page = 1
        if not pageSize:
            pageSize = 10
        if from_person:
            filters["actor_object_id"] = from_person
        if to_person:
            filters["recipient_id"] = to_person
        if unread:
            if unread in ["True", "true", "1"]:
                filters["unread"] = True
            elif unread in ["False", "false", "0"]:
                filters["unread"] = False
            else:
                raise BadRequestException("unread should be True or False")
        notifications_result = Notification.objects.filter(**filters)

        for notification in notifications_result:
            result.append((notification_normal(notification)))
            amount +=1
        paginator = Paginator(notifications_result, pageSize)
        current_page = paginator.get_page(page)
        return JsonResponse(
                {
                    "notifications": result,
                    "total": amount,
                    "pages_count": amount,
                    "page": current_page.number,
                    "pageSize": pageSize
                },
                status=200,
            )

