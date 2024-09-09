import tempfile
from json import JSONDecodeError

from django_scopes import scopes_disabled
from pdf2image.pdf2image import convert_from_bytes

from pretix.base.models import OrderPosition, Event
from pretix.celery_app import app
from pretix.plugins.badges.exporters import render_pdf, OPTIONS
from .client import SeekInkClient


@app.task()
@scopes_disabled()
def send_badge_picture(orderposition, mac):
    orderpositions = OrderPosition.objects.filter(pk__in=[orderposition])
    order = orderpositions.first().order
    event = orderpositions.first().event

    if not (
            event.settings.get("seekink_server_address", as_type=str)
            and event.settings.get("seekink_username", as_type=str)
            and event.settings.get("seekink_password", as_type=str)
    ):
        return

    with tempfile.TemporaryFile() as tmp_file_pdf, tempfile.TemporaryFile() as tmp_file_png:
        render_pdf(event, orderpositions, opt=OPTIONS['one'], output_file=tmp_file_pdf)
        tmp_file_pdf.seek(0)

        image = convert_from_bytes(tmp_file_pdf.read(), first_page=1, last_page=1, fmt="png", size=(240, 416), use_pdftocairo=True)[0]

        image.save(tmp_file_png, format='PNG')
        tmp_file_png.seek(0)

        try:
            client = SeekInkClient(
                event.settings.seekink_server_address,
                event.settings.seekink_username,
                event.settings.seekink_password,
            )

            ret = client.send_picture(
                mac,
                event.settings.seekink_dithering_mode,
                tmp_file_png.read(),
            )

            if ret['code'] == 200:
                order.log_action(
                    "pretix_seekink.send_picture.success",
                    data=ret,
                )
            else:
                order.log_action(
                    "pretix_seekink.send_picture.failed",
                    data=ret,
                )
        except (JSONDecodeError, IOError, AttributeError) as e:
            order.log_action(
                "pretix_seekink.send_picture.failed",
                data={'error': str(e)},
            )
