#!/bin/bash

echo "Ξεκινάει το import δεδομένων..."

mongoimport --db smartcart_db --collection users --file /docker-entrypoint-initdb.d/smartcart_db.users.json --jsonArray
mongoimport --db smartcart_db --collection products --file /docker-entrypoint-initdb.d/smartcart_db.products.json --jsonArray
mongoimport --db smartcart_db --collection categories --file /docker-entrypoint-initdb.d/smartcart_db.categories.json --jsonArray
mongoimport --db smartcart_db --collection carts --file /docker-entrypoint-initdb.d/smartcart_db.carts.json --jsonArray
mongoimport --db smartcart_db --collection cart_items --file /docker-entrypoint-initdb.d/smartcart_db.cart_items.json --jsonArray

echo "Ολοκληρώθηκε το import δεδομένων."

