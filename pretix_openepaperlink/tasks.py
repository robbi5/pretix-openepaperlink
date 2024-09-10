import tempfile
from django_scopes import scopes_disabled
from json import JSONDecodeError
from pdf2image.pdf2image import convert_from_bytes
from pretix.base.models import OrderPosition
from pretix.celery_app import app
from pretix.plugins.badges.exporters import OPTIONS, render_pdf

from .client import OpenEPaperLinkClient


@app.task()
@scopes_disabled()
def send_badge_picture(orderposition, mac):
    orderpositions = OrderPosition.objects.filter(pk__in=[orderposition])
    order = orderpositions.first().order
    event = orderpositions.first().event

    if not event.settings.get("openepaperlink_server_address", as_type=str):
        return

    with tempfile.TemporaryFile() as tmp_file_pdf, tempfile.TemporaryFile() as tmp_file_image:
        render_pdf(event, orderpositions, opt=OPTIONS["one"], output_file=tmp_file_pdf)
        tmp_file_pdf.seek(0)

        image = convert_from_bytes(
            tmp_file_pdf.read(),
            first_page=1,
            last_page=1,
            fmt="jpeg", 
            jpegopt={"quality": 100, "progressive": "n"}, 
            # FIXME make configurable - or pull from pdf size?
            # 152x152 pixels for 1.54", 296x128 pixels for 2.9", and 400x300 pixels for 4.2".
            size=(296, 128),
            use_pdftocairo=True,
        )[0]

        rgb_image = image.convert('RGB')
        rgb_image.save(tmp_file_image, format='JPEG', quality="maximum")
        tmp_file_image.seek(0)

        try:
            client = OpenEPaperLinkClient(event.settings.openepaperlink_server_address)

            ret = client.send_picture(
                mac,
                event.settings.openepaperlink_dithering_mode,
                tmp_file_image.read(),
            )

            if ret is not None and ret["code"] == 200:
                order.log_action(
                    "pretix_openepaperlink.send_picture.success",
                    data=ret,
                )
            else:
                order.log_action(
                    "pretix_openepaperlink.send_picture.failed",
                    data=ret,
                )
        except (JSONDecodeError, IOError, AttributeError) as e:
            order.log_action(
                "pretix_openepaperlink.send_picture.failed",
                data={"error": str(e)},
            )
