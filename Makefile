load_data:
	docker exec -it imageuploader-web-1 python manage.py loaddata fixtures/db.json
test:
	docker exec -it imageuploader-web-1 python manage.py test

.PHONY: load_data test