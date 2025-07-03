import csv
import io
from datetime import datetime, timedelta
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, StreamingHttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from users.models import User
from users.mongo_login_service import MongoLoginService


@method_decorator(staff_member_required, name='dispatch')
class UserLoginHistoryView(View):
    """Custom admin view to display a user's complete login history."""
    
    template_name = 'admin/users/user_login_history.html'
    
    def get(self, request, user_id):
        """Display the login history for a specific user with pagination support."""
        user = get_object_or_404(User, id=user_id)
        mongo_service = MongoLoginService()
        
        # Get pagination parameters
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 50))  # Default 50 records per page
        per_page = min(per_page, 100)  # Cap at 100 records per page
        offset = (page - 1) * per_page
        
        try:
            # Get paginated login history
            paginated_result = mongo_service.get_user_login_history_paginated(
                user_id, limit=per_page, offset=offset
            )
            
            # Get summary statistics (limit to avoid memory issues for users with huge history)
            summary_history = mongo_service.get_user_login_history(user_id, limit=1000)
            total_logins = sum(entry['login_count'] for entry in summary_history)
            current_streak = mongo_service.get_user_login_streak(user_id)
            
            # Calculate pagination info
            total_records = paginated_result['total_count']
            total_pages = (total_records + per_page - 1) // per_page
            has_previous = page > 1
            has_next = paginated_result['has_more']
            
            context = {
                'user': user,
                'login_history': paginated_result['data'],
                'total_logins': total_logins,
                'total_days': len(summary_history),
                'current_streak': current_streak,
                'title': f'Login History for {user.get_full_name() or user.email}',
                # Pagination context
                'page': page,
                'per_page': per_page,
                'total_records': total_records,
                'total_pages': total_pages,
                'has_previous': has_previous,
                'has_next': has_next,
                'previous_page': page - 1 if has_previous else None,
                'next_page': page + 1 if has_next else None,
            }
            
        except Exception as e:
            messages.error(request, f'Error retrieving login history: {str(e)}')
            context = {
                'user': user,
                'login_history': [],
                'error': str(e),
                'title': f'Login History for {user.get_full_name() or user.email}',
                'page': page,
                'per_page': per_page,
                'total_records': 0,
                'total_pages': 0,
                'has_previous': False,
                'has_next': False,
            }
        
        return render(request, self.template_name, context)


@method_decorator(staff_member_required, name='dispatch')
class BulkLoginHistoryExportView(View):
    """View for bulk export of login history with date range filtering."""
    
    template_name = 'admin/users/bulk_login_export.html'
    
    def get(self, request):
        """Display the bulk export form or process export if parameters provided."""
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        # If both dates provided, proceed with export
        if start_date_str and end_date_str:
            return self._export_csv(request, start_date_str, end_date_str)
        
        # Otherwise show the form
        return self._render_form(request)
    
    def _render_form(self, request):
        """Helper method to render the form."""
        context = {
            'title': 'Bulk Login History Export',
            'today': timezone.now().date(),
            'default_start': timezone.now().date() - timedelta(days=30),
        }
        return render(request, self.template_name, context)
    
    def _export_csv(self, request, start_date_str: str, end_date_str: str):
        """Generate and return streaming CSV export for the given date range."""
        try:
            # Parse and validate dates
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            # Validation: start date cannot be after end date
            if start_date > end_date:
                messages.error(request, 'Start date cannot be after end date.')
                return self._render_form(request)
            
            # Validation: reasonable date range (not more than 1 year)
            if (end_date - start_date).days > 365:
                messages.error(request, 'Date range cannot exceed 365 days for performance reasons.')
                return self._render_form(request)
            
            # Validation: dates not in the future
            today = timezone.now().date()
            if start_date > today or end_date > today:
                messages.error(request, 'Export dates cannot be in the future.')
                return self._render_form(request)
            
            mongo_service = MongoLoginService()
            
            # Check if there's any data first
            initial_check = mongo_service.get_all_users_login_history(
                start_date, end_date, limit=1, offset=0
            )
            
            if initial_check['total_count'] == 0:
                messages.warning(request, f'No login data found for the period {start_date} to {end_date}.')
                return self._render_form(request)
            
            # Use streaming response for large datasets
            return self._create_streaming_csv_response(
                mongo_service, start_date, end_date, initial_check['total_count']
            )
            
        except ValueError as e:
            messages.error(request, f'Invalid date format. Please use YYYY-MM-DD format.')
            return self._render_form(request)
        except Exception as e:
            messages.error(request, f'Error exporting login history: {str(e)}')
            return self._render_form(request)
    
    def _create_streaming_csv_response(self, mongo_service, start_date, end_date, total_count):
        """Create a streaming CSV response that processes data in chunks."""

        
        def csv_generator():
            """Generator that yields CSV data in chunks."""
            # Create a pseudo-file for CSV writing
            pseudo_buffer = io.StringIO()
            writer = csv.writer(pseudo_buffer)
            
            # Write header information
            current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')
            writer.writerow([f'Export Date: {current_time}'])
            writer.writerow([f'Date Range: {start_date} to {end_date}'])
            writer.writerow([f'Total Records: {total_count}'])
            writer.writerow([])  # Empty row
            
            # Write CSV column headers
            writer.writerow([
                'User ID', 'Email', 'Full Name', 'Date', 'Login Count', 'Day of Week'
            ])
            
            # Yield header data
            data = pseudo_buffer.getvalue()
            pseudo_buffer.seek(0)
            pseudo_buffer.truncate(0)
            yield data
            
            # Process data in chunks
            chunk_size = 1000
            offset = 0
            user_cache = {}  # Cache user data to avoid repeated DB queries
            
            while offset < total_count:
                # Get chunk of login data
                chunk_result = mongo_service.get_all_users_login_history(
                    start_date, end_date, limit=chunk_size, offset=offset
                )
                
                if not chunk_result['data']:
                    break
                
                # Get user data for this chunk (only new user IDs)
                chunk_user_ids = set(entry['user_id'] for entry in chunk_result['data'])
                new_user_ids = chunk_user_ids - set(user_cache.keys())
                
                if new_user_ids:
                    users = User.objects.filter(id__in=new_user_ids).only('id', 'email', 'first_name', 'last_name')
                    for user in users:
                        user_cache[user.id] = user
                
                # Write chunk data to CSV
                for entry in chunk_result['data']:
                    user = user_cache.get(entry['user_id'])
                    date_str = entry['date_obj'].strftime('%Y-%m-%d')
                    day_of_week = entry['date_obj'].strftime('%A')
                    
                    writer.writerow([
                        entry['user_id'],
                        user.email if user else 'Unknown',
                        user.get_full_name() if user else 'Unknown',
                        date_str,
                        entry['login_count'],
                        day_of_week
                    ])
                
                # Yield the chunk data
                data = pseudo_buffer.getvalue()
                pseudo_buffer.seek(0)
                pseudo_buffer.truncate(0)
                yield data
                
                offset += chunk_size
                
                if not chunk_result['has_more']:
                    break
        
        # Create streaming response
        filename = f'bulk_login_history_{start_date}_{end_date}.csv'
        response = StreamingHttpResponse(
            csv_generator(),
            content_type='text/csv'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


@staff_member_required
def export_user_login_history(request, user_id):
    """Export user login history as CSV."""
    user = get_object_or_404(User, id=user_id)
    mongo_service = MongoLoginService()
    
    try:
        login_history = mongo_service.get_user_login_history(user_id)
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="login_history_{user.id}_{user.email}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Login Count', 'Day of Week'])
        
        for entry in login_history:
            date_str = entry['date_obj'].strftime('%Y-%m-%d')
            day_of_week = entry['date_obj'].strftime('%A')
            writer.writerow([date_str, entry['login_count'], day_of_week])
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error exporting login history: {str(e)}')
        return render(request, 'admin/users/user_login_history.html', {
            'user': user,
            'error': str(e),
            'title': f'Login History for {user.get_full_name() or user.email}',
        })
