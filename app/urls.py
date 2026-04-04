from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import LoginForm
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("registro/", views.register_view, name="register"),
    path(
        "ingresar/",
        auth_views.LoginView.as_view(
            template_name="auth/login.html",
            authentication_form=LoginForm,
        ),
        name="login",
    ),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "recuperar-clave/",
        auth_views.PasswordResetView.as_view(
            template_name="auth/password_reset_form.html",
            email_template_name="auth/password_reset_email.txt",
            subject_template_name="auth/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "recuperar-clave/enviado/",
        auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "recuperar-clave/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(template_name="auth/password_reset_confirm.html"),
        name="password_reset_confirm",
    ),
    path(
        "recuperar-clave/completa/",
        auth_views.PasswordResetCompleteView.as_view(template_name="auth/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("bases/nueva/", views.database_create, name="database_create"),
    path("bases/<slug:slug>/", views.database_detail, name="database_detail"),
    path("bases/<slug:slug>/estadisticas/", views.database_statistics, name="database_statistics"),
    path("bases/<slug:slug>/estadisticas/guardar/", views.saved_statistic_create, name="saved_statistic_create"),
    path("bases/<slug:slug>/estadisticas/<int:statistic_id>/eliminar/", views.saved_statistic_delete, name="saved_statistic_delete"),
    path("bases/<slug:slug>/renombrar/", views.database_rename, name="database_rename"),
    path("bases/<slug:slug>/eliminar/", views.database_delete, name="database_delete"),
    path("bases/<slug:slug>/vistas/guardar/", views.saved_view_create, name="saved_view_create"),
    path("bases/<slug:slug>/campos/nuevo/", views.field_create, name="field_create"),
    path("bases/<slug:slug>/campos/principal/", views.field_set_primary_select, name="field_set_primary_select"),
    path("bases/<slug:slug>/campos/<int:field_id>/editar/", views.field_update, name="field_update"),
    path("bases/<slug:slug>/campos/<int:field_id>/principal/", views.field_set_primary, name="field_set_primary"),
    path("bases/<slug:slug>/campos/<int:field_id>/eliminar/", views.field_delete, name="field_delete"),
    path("bases/<slug:slug>/miembros/", views.member_create, name="member_create"),
    path("bases/<slug:slug>/registros/nuevo/", views.record_create, name="record_create"),
    path("bases/<slug:slug>/registros/importar/", views.records_import_start, name="records_import"),
    path("bases/<slug:slug>/registros/importar/mapear/", views.records_import_map, name="records_import_map"),
    path("bases/<slug:slug>/registros/exportar/", views.records_export, name="records_export"),
    path("bases/<slug:slug>/registros/<int:pk>/", views.record_detail, name="record_detail"),
    path("bases/<slug:slug>/registros/<int:pk>/editar/", views.record_edit, name="record_edit"),
    path("bases/<slug:slug>/registros/<int:pk>/eliminar/", views.record_delete, name="record_delete"),
]
