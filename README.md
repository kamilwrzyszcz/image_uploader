### Image uploader DRF app.

run with `docker compose up`

Then you can run make command `make load_data` to load fixtures.  
Fixtures contain:
 - Two thumbnail resolutions [200x200, 400x400]
 - Three account tiers [Basic, Premium, Enterprise]
 - Four users:
    - admin - username: admin, password: admin. Enterprise account
    - user1 - username: user1, password: password. Basic account
    - user2 - username: user2, password: password. Premium account
    - user3 - username: user3, password: password. Enterprise account
  
Run tests with `make test`  
Thumbnail resolutions and account tiers do not have views and can be created only via admin panel.