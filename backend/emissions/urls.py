from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.me),
    path('dashboard/stats/', views.DashboardStats.as_view()),
    path('upload/', views.UploadCSV.as_view()),
    path('sources/', views.DataSourceList.as_view()),
    path('records/', views.EmissionRecordList.as_view()),
    path('records/<int:pk>/', views.EmissionRecordDetail.as_view()),
    path('records/<int:pk>/review/', views.ReviewRecord.as_view()),
    path('records/<int:pk>/audit/', views.RecordAuditLog.as_view()),
]
