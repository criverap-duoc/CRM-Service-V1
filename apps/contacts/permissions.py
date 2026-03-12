from rest_framework.permissions import BasePermission


class IsManager(BasePermission):
    """
    Permite acceso solo a usuarios en el grupo 'managers'.
    """
    message = "Solo los managers pueden realizar esta acción."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and (
                request.user.groups.filter(name="managers").exists()
                or request.user.is_superuser
            )
        )


class IsAgentOrManager(BasePermission):
    """
    Permite acceso a cualquier usuario autenticado.
    La restricción a nivel de objeto la maneja has_object_permission.
    """
    message = "No tienes permiso para acceder a este recurso."

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Managers ven todo
        if request.user.is_superuser or request.user.groups.filter(name="managers").exists():
            return True
        # Agentes solo ven sus propios contactos
        return obj.assigned_to == request.user
