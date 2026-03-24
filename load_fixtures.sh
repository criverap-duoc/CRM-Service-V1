#!/bin/bash
echo "Cargando fixtures..."
python manage.py loaddata apps/contacts/fixtures/initial_users.json
python manage.py loaddata apps/contacts/fixtures/initial_contacts.json
python manage.py loaddata apps/interactions/fixtures/initial_interactions.json
echo "Fixtures cargados correctamente."
