#!/bin/bash
virtualenv --no-site-packages --distribute .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
git submodule add --  https://github.com/stephband/bolt.git passkeys_example/static/bolt
git submodule update --init --recursive
cd passkeys_example
createdb passkeys_example
python manage.py collectstatic --noinput
python manage.py syncdb
mkdir -p ../tmp/media
mkdir /var/tmp/letsencrypt-auto

cd
mkdir -p backup
(crontab -l ; echo "@daily ~/passkeys_example/.venv/bin/python ~/passkeys_example/passkeys_example/manage.py clearsessions") | crontab -
(crontab -l ; echo "@daily pg_dump -f ~/backup/passkeys_example.sql passkeys_example") | crontab -

cd passkeys_example/conf/prod
echo
echo "sudo ln -s $PWD/supervisord.gunicorn.conf /etc/supervisord.d/passkeys_example.conf"
echo "sudo ln -s $PWD/nginx.conf /etc/nginx/sites-enabled/passkeys_example.conf"
echo "sudo supervisorctl update"
echo "sudo service nginx configtest"
echo
cd
