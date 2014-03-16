#!/bin/bash
php composer.phar create-project --prefer-source --no-dev --no-interaction imbo/imbolauncher imbolauncher dev-develop
./integration/imbolauncher/imbolauncher/imbolauncher start-servers --config=$TRAVIS_BUILD_DIR/imboclient/test/integration/imbolauncher/config.json --install-path=/tmp/imbo-servers --no-interaction -vvv ; cat /tmp/imbo-servers/dev-develop/httpd.log
nosetests
OUT=$?

if [ $OUT -eq 0 ];then
    echo "Tests successful!"
else
    echo "Tests failed, httpd log: "
    cat /tmp/imbo-servers/dev-develop/httpd.log
    ps aux | grep php
    curl http://127.0.0.1:9012/users/test
fi

./integration/imbolauncher/imbolauncher kill-servers --no-interaction -vvv

exit $OUT

