from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import TemplateView
from tickets.views import *

urlpatterns = [
    # Examples:
    # url(r'^$', 'tutorial.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', TemplateView.as_view(template_name="tickets/loginpage.html")),
    url(r'^validate_user_pass$', validate_user_pass),
    url(r'^create_ticket_data$', CreateTicketData.as_view(), name="create_ticket"),
    url(r'^get_ticket_data$', GetTicketData.as_view(), name="get_ticket"),
    url(r'^update_ticket_data$', UpdateTicketData.as_view(), name="update_ticket"),
    #url(r'^delete_ticket_data$', DeleteTicketData.as_view(), name="delete_ticket")
]
