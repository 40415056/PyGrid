git init
git add .
git commit -am "init"
heroku create $GRID_NAME
heroku addons:create rediscloud
git push heroku master