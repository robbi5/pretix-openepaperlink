from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _, gettext_noop  # NoQA
from pretix.base.forms import SecretKeySettingsField, SettingsForm
from pretix.base.models import Event, Question
from pretix.control.views.event import EventSettingsFormView, EventSettingsViewMixin


class OpenEPaperLinkSettingsForm(SettingsForm):
    openepaperlink_push_badges = forms.BooleanField(
        label=_("Enable integration"),
        required=False,
        initial=False,
    )

    openepaperlink_server_address = forms.CharField(
        label=_("Server Address"),
        initial="http://192.168.4.1",
        help_text=_("Address to the OpenEPaperlink Access Point"),
    )

    openepaperlink_dithering_mode = forms.ChoiceField(
        label=_("Dithering"),
        choices=[
            ("0", _("No Dithering")),
            ("1", _("Enable Dithering")),
        ],
        initial=0,
    )


class OpenEPaperLinkSettings(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = OpenEPaperLinkSettingsForm
    template_name = "pretix_openepaperlink/settings.html"
    permission = "can_change_settings"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_openepaperlink:settings",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        question, created = Question.objects.get_or_create(
            identifier="pretix_openepaperlink_question",
            event=self.request.event,
            defaults={
                "type": Question.TYPE_STRING,
                "question": gettext("OpenEPaperLink Badge MAC address"),
                "required": self.request.event.settings.openepaperlink_push_badges,
                "help_text": gettext(
                    "This question has been created automatically by the OpenEPaperLink Badges plugin. "
                    "Please do not change its internal identifier."
                ),
                "ask_during_checkin": True,
                "hidden": True,
            },
        )
        if not created:
            question.required = self.request.event.settings.openepaperlink_push_badges
            question.save(update_fields=["required"])

        messages.warning(
            request,
            _("Please select the products that should use the OpenEPaperLink badges."),
        )

        return redirect(
            reverse(
                "control:event.items.questions.edit",
                kwargs={
                    "organizer": self.request.organizer.slug,
                    "event": self.request.event.slug,
                    "question": question.pk,
                },
            )
        )
