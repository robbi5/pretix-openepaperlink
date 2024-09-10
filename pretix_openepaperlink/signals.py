from django.db.models import Q
from django.dispatch import receiver
from django.urls import resolve, reverse
from django.utils.translation import gettext_lazy as _  # NoQA
from pretix.base.models import QuestionAnswer
from pretix.base.settings import settings_hierarkey
from pretix.base.signals import checkin_created
from pretix.control.signals import nav_event_settings

from .tasks import send_badge_picture


@receiver(nav_event_settings, dispatch_uid="pretix_openepaperlink_nav_event_settings")
def nav_event_settings(sender, request=None, **kwargs):
    url = resolve(request.path_info)
    p = request.user.has_event_permission(
        request.organizer, request.event, "can_change_settings", request
    )
    if not p:
        return []
    return [
        {
            "label": _("OpenEPaperLink Badges"),
            "url": reverse(
                "plugins:pretix_openepaperlink:settings",
                kwargs={
                    "event": request.event.slug,
                    "organizer": request.event.organizer.slug,
                },
            ),
            "active": url.namespace == "plugins:pretix_openepaperlink"
            and url.url_name == "settings",
        }
    ]


@receiver(checkin_created, dispatch_uid="pretix_openepaperlink_checkin_created")
def checkin_created(sender, checkin, **kwargs):
    if not sender.settings.get("openepaperlink_push_badges", as_type=bool, default=False):
        return

    if not checkin.position_id:
        return
    for qa in QuestionAnswer.objects.filter(
        orderposition_id=checkin.position_id,
        question__identifier="pretix_openepaperlink_question",
    ).filter(
        Q(orderposition__item__badge_assignment__isnull=True)
        | Q(orderposition__item__badge_assignment__layout__isnull=False)
    ):
        send_badge_picture.apply_async(args=(qa.orderposition.pk, qa.answer))


settings_hierarkey.add_default("openepaperlink_push_badges", False, bool)
