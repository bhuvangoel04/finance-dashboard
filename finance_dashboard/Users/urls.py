from django.urls import path
from .views import (
    MeView,
    UserListCreateView,
    UserDetailView,
    UserPasswordChangeView,
    UserDeactivateView,
)

urlpatterns = [
    path('me/', MeView.as_view(), name='user-me'),
    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/set-password/', UserPasswordChangeView.as_view(), name='user-set-password'),
    path('<int:pk>/deactivate/', UserDeactivateView.as_view(), {'action': 'deactivate'}, name='user-deactivate'),
    path('<int:pk>/activate/', UserDeactivateView.as_view(), {'action': 'activate'}, name='user-activate'),
]