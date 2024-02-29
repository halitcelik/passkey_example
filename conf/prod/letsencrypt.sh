./letsencrypt-auto certonly \
    --email marco@cruncher.ch \
    --fullchain-path /home/projects/passkeys_example/passkeys_example/conf/prod/ssl/fullchain.pem \
    --key-path /home/projects/passkeys_example/passkeys_example/conf/prod/ssl/privkey.pem \
    --webroot -w /home/projects/passkeys_example/passkeys_example/conf/prod/ssl/webroot/ \
    -d passkeys_example.com -d www.passkeys_example.com -d passkeys_example.cruncher.ch
