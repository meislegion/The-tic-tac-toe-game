from django.conf.urls import patterns, include, url
from mygame.views import *

#from django.conf.urls.static import static
#from django.conf import settings


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'test_task.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^$', home_page),
    url(r'^login/$', login_page),
    url(r'^logout/$', logout_user),
    url(r'^register/$', register),
    url(r'^api/set_user_online/$', set_user_online),
    url(r'^api/check_user_online/$', check_user_online),
    url(r'^api/get_user_online/$', get_user_online),
    url(r'^api/check_state/$', check_state),
    url(r'^api/get_invite/$', get_invite),
    url(r'^api/invite/$', invite_to_game),
    url(r'^game/$', game_page),
    ###



    url(r'^api/game/(\d{1,5})/$', api_game),
    url(r'^i18n/', include('django.conf.urls.i18n')),

) #+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

