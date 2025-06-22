# Αυτό είναι το αρχείο εκκίνησης της Flask εφαρμογής SmartCart.
# Καλεί τη συνάρτηση create_app() από το app/__init__.py και ξεκινάει τον server.

from app import create_app

# Φτιάχνω το Flask app καλώντας τη συνάρτηση που έχω ορίσει στο app/__init__.py
app = create_app()

# Εκτελώ τον server στην πόρτα 5000 για να μιλάει σωστά με το UI
if __name__ == '__main__':
    app.run(debug=True, port=5000)