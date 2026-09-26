class RolePermission:
    allowed_roles = {'Admin', 'Dispatcher', 'Driver', 'Mechanic', 'Viewer'}
    def has_permission(self, role):
        return role in self.allowed_roles
