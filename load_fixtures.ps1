Write-Host "Cargando fixtures..."
python manage.py loaddata apps/contacts/fixtures/initial_users.json
python manage.py loaddata apps/contacts/fixtures/initial_contacts.json
python manage.py loaddata apps/interactions/fixtures/initial_interactions.json
Write-Host "Fixtures cargados correctamente."
