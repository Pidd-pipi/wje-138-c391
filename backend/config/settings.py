import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv('JWT_SECRET', 'fleet-dispatch-secret')
DEBUG = True
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'rest_framework', 'corsheaders', 'fleet_app']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware', 'fleet_app.middleware.request_logger.RequestLoggerMiddleware', 'fleet_app.middleware.audit_log.AuditLogMiddleware', 'fleet_app.middleware.error_handler.ErrorHandlerMiddleware', 'django.middleware.common.CommonMiddleware']
ROOT_URLCONF = 'config.urls'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = True
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'fleet_dispatch'),
        'USER': os.getenv('DB_USER', 'fleet_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'fleet_password'),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',)}
