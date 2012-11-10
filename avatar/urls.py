from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('avatar.views',
    url('^add/$', 'add', name='avatar_add'),
    url('^change/$', 'change', name='avatar_add'),
    url('^render_primary/(?P<user>[\+\w]+)/(?P<size>[\d]+)/$', 'render_primary', name='avatar_render_primary'),
)
