import os
from pathlib import Path
from urllib.parse import urlparse,unquote
from django.core.exceptions import ImproperlyConfigured

BASE_DIR=Path(__file__).resolve().parent.parent
DEBUG=os.getenv("DJANGO_DEBUG","false").lower()=="true"
SECRET_KEY=os.getenv("DJANGO_SECRET_KEY","development-only-not-for-production" if DEBUG else "")
if not SECRET_KEY:
    raise ImproperlyConfigured("Defina DJANGO_SECRET_KEY para produção ou DJANGO_DEBUG=true localmente.")
ALLOWED_HOSTS=[s.strip() for s in os.getenv("DJANGO_ALLOWED_HOSTS","localhost,127.0.0.1").split(",") if s.strip()]
CSRF_TRUSTED_ORIGINS=[f"https://{s}" for s in ALLOWED_HOSTS if s not in ("localhost","127.0.0.1")]
INSTALLED_APPS=["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","rest_framework","rest_framework.authtoken","social"]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware","whitenoise.middleware.WhiteNoiseMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF="config.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION="config.wsgi.application"
DATABASES={"default":{"ENGINE":"django.db.backends.sqlite3","NAME":BASE_DIR/"db.sqlite3"}}
if os.getenv("DATABASE_URL"):
    db=urlparse(os.environ["DATABASE_URL"])
    DATABASES={"default":{"ENGINE":"django.db.backends.postgresql","NAME":db.path.lstrip("/"),"USER":unquote(db.username or ""),"PASSWORD":unquote(db.password or ""),"HOST":db.hostname,"PORT":db.port or 5432,"CONN_MAX_AGE":60,"OPTIONS":{"sslmode":os.getenv("DB_SSLMODE","require")}}}
AUTH_PASSWORD_VALIDATORS=[{"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},{"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},{"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},{"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"}]
LANGUAGE_CODE="pt-br"
TIME_ZONE="America/Bahia"
USE_I18N=True
USE_TZ=True
STATIC_URL="/static/"
STATIC_ROOT=BASE_DIR/"staticfiles"
MEDIA_ROOT=Path(os.getenv("MEDIA_ROOT",str(BASE_DIR/"media")))
MEDIA_URL="/media/"
STORAGES={"default":{"BACKEND":"django.core.files.storage.FileSystemStorage"},"staticfiles":{"BACKEND":"whitenoise.storage.CompressedManifestStaticFilesStorage"}}
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
LOGIN_URL="/"
REST_FRAMEWORK={"DEFAULT_AUTHENTICATION_CLASSES":["rest_framework.authentication.SessionAuthentication","rest_framework.authentication.TokenAuthentication"],"DEFAULT_PERMISSION_CLASSES":["rest_framework.permissions.IsAuthenticatedOrReadOnly"],"DEFAULT_PAGINATION_CLASS":"rest_framework.pagination.PageNumberPagination","PAGE_SIZE":20,"DEFAULT_THROTTLE_CLASSES":["rest_framework.throttling.ScopedRateThrottle"],"DEFAULT_THROTTLE_RATES":{"auth":"20/min"}}
DATA_UPLOAD_MAX_MEMORY_SIZE=4*1024*1024
if not DEBUG:
    SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")
    SECURE_SSL_REDIRECT=True
    SESSION_COOKIE_SECURE=True
    CSRF_COOKIE_SECURE=True
    SECURE_CONTENT_TYPE_NOSNIFF=True
    X_FRAME_OPTIONS="DENY"
