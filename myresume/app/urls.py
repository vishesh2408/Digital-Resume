# app/urls.py
# =========================================================================
from django.urls import path
from . import views

app_name = 'app'

urlpatterns = [
   
    path('', views.home_view, name='home'),
    path('signup/', views.signup_view, name='signup'),
    
    path('resumes/', views.resume_list_view, name='resume_list'),
    path('create/', views.resume_create_view, name='resume_create'),
    path('edit/<int:pk>/', views.resume_edit_view, name='resume_edit'),
   
    path('view/<int:pk>/<str:template_name>/', views.resume_detail_view, name='resume_detail'),
   
    path('templates/<int:pk>/', views.resume_template_select_view, name='template_select'),
    path('export/pdf/<int:pk>/<str:template_name>/', views.export_pdf_view, name='export_pdf'),
    path('ats/', views.ats_analysis_view, name='ats_analysis'),
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
