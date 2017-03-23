from django.conf.urls import include, url
from django.views.generic import TemplateView
from wagtail.contrib.wagtailsitemaps.views import sitemap
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtailcore import urls as wagtail_urls


urlpatterns = [
    url(r'^admin/', include(wagtailadmin_urls)),
    url('^sitemap\.xml$', sitemap),
    url(r'^robots\.txt$', TemplateView.as_view(
        template_name='robots.txt', content_type='text/plain')),
    url(r'', include(wagtail_urls)),
]
