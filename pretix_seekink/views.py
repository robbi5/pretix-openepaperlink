from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _, gettext_noop  # NoQA
from pretix.base.forms import SettingsForm, SecretKeySettingsField
from pretix.base.models import Event, Question
from pretix.control.views.event import EventSettingsFormView, EventSettingsViewMixin


class SeekInkSettingsForm(SettingsForm):
    seekink_push_badges = forms.BooleanField(
        label=_("Enable integration"),
        required=False,
        initial=False,
    )

    seekink_server_address = forms.CharField(
        label=_('Server Address'),
        initial='http://iot.seekink.com',
        help_text=_('Address to the control-interface, without the /cloudPlatform/'),
    )

    seekink_username = forms.CharField(
        label=_('Username'),
        required=False,
    )

    seekink_password = SecretKeySettingsField(
        label=_('Password'),
        required=False,
    )

    seekink_dithering_mode = forms.ChoiceField(
        label=_('Dithering Mode'),
        choices=[
            ('0', _('Threshold processing')),
            ('1', _('Gradient processing')),
        ],
        initial=0,
    )


class SeekInkSettings(EventSettingsViewMixin, EventSettingsFormView):
    model = Event
    form_class = SeekInkSettingsForm
    template_name = "pretix_seekink/settings.html"
    permission = "can_change_settings"

    def get_success_url(self) -> str:
        return reverse(
            "plugins:pretix_seekink:settings",
            kwargs={
                "organizer": self.request.event.organizer.slug,
                "event": self.request.event.slug,
            },
        )

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)

        question, created = Question.objects.get_or_create(
            identifier="pretix_seekink_question",
            event=self.request.event,
            defaults={
                "type": Question.TYPE_STRING,
                "question": gettext("SeekInk eInk Badge MAC-Address"),
                "required": self.request.event.settings.seekink_push_badges,
                "help_text": gettext(
                    "This question has been created automatically by the SeekInk eInk Badges plugin. "
                    "Please do not change its internal identifier."
                ),
                "ask_during_checkin": True,
                "hidden": True,
            },
        )
        if not created:
            question.required = (
                self.request.event.settings.seekink_push_badges
            )
            question.save(update_fields=["required"])

        messages.warning(
            request,
            _("Please select the products that should use the eInk badges."),
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
