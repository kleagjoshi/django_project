# Django Permissions System for Course Management System

This document describes the comprehensive authorization system implemented using Django permissions to control access for different user roles.

## User Roles

The system supports three main user roles:

1. **Admin** - System administrators (is_staff=True)
2. **Lecturer** - Course instructors 
3. **Student** - Course participants

## Permission Classes

### Core Permission Classes

#### `IsAdminOnly`
- Restricts access to admin users only
- Used for sensitive system-level operations

#### `IsAdminOrReadOnly`
- Allows read access to authenticated users
- Restricts write operations to admin users only
- Used for system resources like courses

#### `IsLecturerOrAdmin`
- Allows access to lecturers and admin users
- Used for lecturer-specific functionality

#### `IsStudentOrAdmin`
- Allows access to students and admin users
- Used for student-specific functionality

### Object-Level Permission Classes

#### `IsOwnerLecturerOrAdmin`
- Allows access to the lecturer who owns the resource or admin
- Used for group-specific operations where lecturer ownership matters

#### `IsOwnerStudentOrAdmin`
- Allows access to the student who owns the resource or admin
- Used for student-specific data access

#### `CanManagePayments`
- Complex permission for payment management
- Lecturers can manage payments for their groups
- Students can view their own payments (read-only)
- Admin can do everything

#### `CanViewOwnData`
- Allows users to view their own data and related information
- Students can view their groups and materials
- Lecturers can view their groups and students

## Endpoint Permissions by ViewSet

### GroupViewSet
- **Create**: `IsLecturerOrAdmin` - Only lecturers and admin can create groups
- **Update/Delete**: `IsOwnerLecturerOrAdmin` - Only the group's lecturer or admin can modify
- **List/Retrieve**: `IsAuthenticated` - All authenticated users can view
- **by_lecturer/by_student**: `CanViewOwnData` - Users can view their own data

### StudentViewSet
- **Create/Delete**: `IsLecturerOrAdmin` - Only lecturers and admin can manage students
- **Update**: `IsOwnerStudentOrAdmin` - Students can update their own data
- **List/Statistics**: `IsLecturerOrAdmin` - Only lecturers and admin can view lists
- **Retrieve**: `CanViewOwnData` - Students can view their own data

### PaymentViewSet
- **get_payments**: `IsOwnerStudentOrAdmin` - Students can view their own payments
- **confirm_payment/block_student**: `IsLecturerOrAdmin` - Only lecturers and admin can manage
- **List/Reports**: `IsLecturerOrAdmin` - Only lecturers and admin can view reports
- **Update/Delete**: `IsLecturerOrAdmin` - Only lecturers and admin can modify records

### MaterialViewSet
- **Create/Update/Delete**: `IsOwnerLecturerOrAdmin` - Only lecturers can manage materials for their groups
- **List/Retrieve**: `CanViewOwnData` - Students can view materials for their groups
- **Statistics**: `IsLecturerOrAdmin` - Only lecturers and admin can view statistics

### CourseViewSet
- **List/Retrieve**: `IsAuthenticated` - All authenticated users can view courses
- **Create/Update/Delete**: `IsAdminOrReadOnly` - Only admin can manage courses
- **Passive courses**: `IsLecturerOrAdmin` - Only lecturers and admin can view inactive courses

## Data Filtering by Role

Each ViewSet implements `get_queryset()` to filter data based on user role:

### Admin Users
- Can access all data across the system
- No restrictions on any resources

### Lecturers
- Can access:
  - Groups they teach
  - Students enrolled in their groups
  - Materials for their groups
  - Payments for students in their groups

### Students
- Can access:
  - Groups they're enrolled in
  - Their own student record
  - Materials for their groups
  - Their own payments

## Middleware

### UserRoleMiddleware
Adds convenient role attributes to request objects:
- `request.user_role` - String indicating user role ('admin', 'lecturer', 'student', 'user', 'anonymous')
- `request.is_admin` - Boolean
- `request.is_lecturer` - Boolean  
- `request.is_student` - Boolean

To enable, add to Django settings:
```python
MIDDLEWARE = [
    # ... other middleware
    'cms_api.middleware.UserRoleMiddleware',
]
```

## Security Features

### Object-Level Permissions
- Lecturers can only modify groups they own
- Students can only access their own data
- Payment access is strictly controlled by ownership

### Automatic Filtering
- Querysets are automatically filtered based on user role
- Users cannot access data outside their scope even if they know IDs

### Role-Based Access Control
- Different permission classes for different types of operations
- Granular control over who can perform what actions

## Usage Examples

### Checking Permissions in Views
```python
from cms_api.permissions import IsLecturerOrAdmin

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsLecturerOrAdmin]
```

### Using Middleware in Views
```python
def my_view(request):
    if request.is_lecturer:
        # Lecturer-specific logic
        pass
    elif request.is_student:
        # Student-specific logic
        pass
```

### Custom Permission Logic
```python
from cms_api.permissions import CanViewOwnData

class CustomViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action == 'special_action':
            return [CanViewOwnData()]
        return super().get_permissions()
```

## Testing Permissions

When testing the API:

1. **As Admin**: Create a superuser and test full access
2. **As Lecturer**: Create a lecturer user and test group-specific access
3. **As Student**: Create a student user and test restricted access
4. **Cross-Role Testing**: Ensure lecturers can't access other lecturers' data

## Best Practices

1. Always use the most restrictive permission that allows the required functionality
2. Implement both view-level and object-level permissions where appropriate
3. Filter querysets in `get_queryset()` to prevent data leakage
4. Use the middleware for consistent role checking across the application
5. Test permissions thoroughly with different user roles 