from django.urls import path
from users.admin_views import (
    UserLoginHistoryView, 
    BulkLoginHistoryExportView
)

app_name = 'users'

urlpatterns = [
    path('admin/user/<int:user_id>/login-history/', 
         UserLoginHistoryView.as_view(), 
         name='user_login_history'),
    path('admin/bulk-login-export/', 
         BulkLoginHistoryExportView.as_view(), 
         name='bulk_login_history_export'),
]
