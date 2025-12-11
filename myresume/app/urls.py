# app/urls.py
# =========================================================================
from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('', views.resume_list_view, name='resume_list'),
    path('create/', views.resume_create_view, name='resume_create'),
    path('edit/<int:pk>/', views.resume_edit_view, name='resume_edit'),
    # This URL is for viewing a resume with a specific template.
    path('view/<int:pk>/<str:template_name>/', views.resume_detail_view, name='resume_detail'),
    # This URL is for selecting a template for a specific resume.
    path('templates/<int:pk>/', views.resume_template_select_view, name='template_select'),
    path('export/pdf/<int:pk>/<str:template_name>/', views.export_pdf_view, name='export_pdf'),
   # path('templates/<str:template_name>/', views.download_template_view, name='download_template'),
]




# # =========================================================================
# # File: app/urls.py
# # =========================================================================
# from django.urls import path
# from . import views

# app_name = 'app'

# urlpatterns = [
#     path('signup/', views.signup_view, name='signup'),
#     path('', views.resume_list_view, name='resume_list'),
#     path('create/', views.resume_create_view, name='resume_create'),
#     path('edit/<int:pk>/', views.resume_edit_view, name='resume_edit'),
#     path('view/<int:pk>/', views.resume_detail_view, name='resume_detail'),
#     path('view/<int:pk>/<str:template_name>/', views.resume_template_select_view, name='template_select'),
#     path('export/pdf/<int:pk>/<str:template_name>/', views.export_pdf_view, name='export_pdf'),
# ]
