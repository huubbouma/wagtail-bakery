import logging
import os

from bakery.views import BuildableDetailView
from django.conf import settings
from django.core.handlers.base import BaseHandler
from django.utils.six.moves.urllib.parse import urlparse
from wagtail.contrib.wagtailsitemaps.sitemap_generator import Sitemap
from wagtail.wagtailcore.models import Page, Site

logger = logging.getLogger(__name__)


class WagtailBakeryView(BuildableDetailView):
    """
    An abstract class that can be inherited to create a buildable view that can
    be added to BAKERY_VIEWS setting.
    """
    def __init__(self, *args, **kwargs):
        self.handler = BaseHandler()
        self.handler.load_middleware()

        self.site = self.get_site()

        super(WagtailBakeryView, self).__init__(*args, **kwargs)

    def get(self, request):
        response = self.handler.get_response(request)
        return response

    def get_site(self):
        """Return the site were to build the static pages from.

        By default this is the site marked as default with `is_default_site`
        set to `true`.

        In case of a multisite setup this site object will be ignored.

        Example:
            def get_site(self):
                return Site.objects.get(hostname='website.com')
        """
        return Site.objects.get(is_default_site=True)

    def get_build_path(self, obj):
        url = self.get_url(obj)

        if url.startswith('http'):
            url_parsed = urlparse(url)
            path = url_parsed.path
            hostname = url_parsed.hostname
            build_path = os.path.join(settings.BUILD_DIR, hostname, path[1:])
        else:
            build_path = os.path.join(settings.BUILD_DIR, url[1:])

        # Make sure the (deeply) directories are created
        os.path.exists(build_path) or os.makedirs(build_path)

        # Always append index.html at the end of the path
        return os.path.join(build_path, 'index.html')

    def get_url(self, obj):
        """Return Wagtail page url instead of Django's get_absolute_url."""
        return obj.url

    def get_path(self, obj):
        """Return Wagtail path to page."""
        return obj.path

    def build_queryset(self):
        for item in self.get_queryset().all():
            url = self.get_url(item)
            logger.info("Building %s" % url)
            if url is not None:
                self.build_object(item)

    class Meta:
        abstract = True


class AllPublishedPagesView(WagtailBakeryView):
    """
    Generates a seperate index.html page for each published wagtail page.

    Use this view to export your pages for production.

    Example:
        # File: settings.py
        BAKERY_VIEWS = (
            'wagtailbakery.views.AllPublishedPagesView',
        )
    """
    def get_queryset(self):
        return Page.objects.filter(depth__gt=1).public().live().specific()


class AllPagesView(WagtailBakeryView):
    """
    Generates a seperate index.html page for each (un)published wagtail page.

    Use this view to export your pages for acceptance/staging environments.

    Example:
        # File: settings.py
        BAKERY_VIEWS = (
            'wagtailbakery.views.AllPagesView',
        )
    """
    def get_queryset(self):
        return Page.objects.filter(depth__gt=1).public().specific()


class BuildableSitemapView(WagtailBakeryView):
    """
    Build the sitemap
    """

    build_path = 'sitemap.xml'

    def get_content(self):

        sitemap = Sitemap(self.site)
        return sitemap.render().encode()

    @property
    def build_method(self):
        return self.build

    def build(self):
        logger.debug("Building %s" % self.build_path)
        self.request = self.create_request(self.build_path)
        path = os.path.join(settings.BUILD_DIR, self.build_path)
        self.prep_directory(self.build_path)
        self.build_file(path, self.get_content())
