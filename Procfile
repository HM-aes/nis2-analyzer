release: python backend/manage.py migrate --noinput && python backend/manage.py collectstatic --noinput
web: gunicorn --chdir backend nis2_analyzer.wsgi --bind 0.0.0.0:$PORT --workers 2 --log-file -
