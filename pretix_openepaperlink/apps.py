from django.conf import settings
from django.utils.translation import gettext_lazy

from . import __version__

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")


class PluginApp(PluginConfig):
    default = True
    name = "pretix_openepaperlink"
    verbose_name = "OpenEPaperLink Badges"

    class PretixPluginMeta:
        name = gettext_lazy("OpenEPaperLink Badges")
        author = "Maximilian Richt, Martin Gross"
        description = gettext_lazy("Use OpenEPaperLink compatible E-Paper tags as Badges for your events")
        visible = True
        version = __version__
        category = "INTEGRATION"
        compatibility = "pretix>=2.7.0"
        experimental = True

    def ready(self):
        from . import signals  # NOQA
