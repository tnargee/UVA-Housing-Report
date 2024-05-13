"""
URL configuration for mysite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView
from loginApp import views as loginAppView, views
from loginApp.views import delete_all_complaints
from machina import urls as machina_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name="loginApp/index.html")),
    path('accounts/', include('allauth.urls')),
    path('logout', LogoutView.as_view(), name="logout"),
    path('dashboard/', loginAppView.dashboard, name='dashboard'),
    path('complaint/', views.complaint_form, name='complaint_form'),
    path('complaint_success/', views.complaint_success, name='complaint_success'),
    path('anonymous_complaint/', views.anonymous_complaint_view, name='anonymous_complaint_form'),
    path('delete_complaint/<int:complaint_id>/', views.deletecomplaintcommon, name='delete_complaint'),
    path('edit_complaint/<int:complaint_id>/', views.editcomplaintcommon, name='edit_complaint'),
    path('forums/',views.ThreadListView.as_view(),name='forums'),
    path('forum/', include(machina_urls)),
    path('complaints/<int:complaint_id>/', views.handle_complaint_click, name='complaints'),
    path('about/', views.about, name='about'),
    path('delete-all-complaints/', delete_all_complaints, name='delete_all_complaints'),
]

