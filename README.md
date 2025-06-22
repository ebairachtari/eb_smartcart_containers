# SmartCart Containers: Ολοκληρωμένο Πληροφοριακό Σύστημα με ML Service, Jenkins & Node-RED Integration

**Επέκταση του project**: [eb\_Smartcart](https://github.com/ebairachtari/eb_Smartcart)

Αυτή η εργασία αποτελεί **επεκταμένη υλοποίηση** του SmartCart. Περιλαμβάνει:

* **Ολοκληρωμένη containerized αρχιτεκτονική** με backend, frontend, MongoDB, ML Service, Node-RED και Jenkins.
* **Machine Learning υπηρεσία** που αναλύει patterns αγορών από πραγματικά δεδομένα χρηστών και προβλέπει τον cluster τύπο ενός νέου καλαθιού.
* **Node-RED Integration** που τρέχει σε real-time την ML πρόβλεψη.
* **Jenkins Pipeline** για αυτοματοποίηση και δοκιμή της υποδομής.

---

## Containers

| Container              | Περιγραφή                                                    |
| ---------------------- | ------------------------------------------------------------ |
| `smartcart_backend`    | RESTful API για αυθεντικοποίηση και καλάθια                  |
| `smartcart_frontend`   | Streamlit διεπαφή για χρήση από χρήστη                       |
| `smartcart_mongo`      | MongoDB βάση με όλα τα δεδομένα προϊόντων/καλαθιών           |
| `smartcart_ml_service` | ML υπηρεσία με KMeans μοντέλο πρόβλεψης αγοραστικών patterns |
| `smartcart_nodered`    | Node-RED integration UI για real-time ροές                   |
| `smartcart_jenkins`    | Jenkins CI για έλεγχο & deployment                           |

---

## Οδηγίες Εκτέλεσης

```bash
git clone https://github.com/ebairachtari/eb_smartcart-containers.git
cd eb_smartcart-containers
docker compose up --build -d
```

![image](https://github.com/user-attachments/assets/dd580915-491e-4c18-a69b-4ec4220c7084)

---

## Έλεγχος συστήματος

### Test των endpoints:

```bash
./curl_test.sh
```
![image](https://github.com/user-attachments/assets/ef5eb13c-04fd-4d22-9ce9-8e26320e576b)


### MongoDB:

```bash
docker exec -it smartcart_mongo mongo
use smartcart_db
show collections
db.products.find().pretty()
```

![image](https://github.com/user-attachments/assets/fa1bcdc6-2a5b-4d8d-9890-162253d56e5f)


### Frontend:

[http://localhost:8501](http://localhost:8501)

> Στοιχεία Σύνδεδης: Username : `demo_user@unipi.gr`  , Password  : `qqQQ11!!`

![image](https://github.com/user-attachments/assets/8f438bdc-f5d7-4d80-b3d8-30a92aa2cda7)

### Backend login:

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo_user@unipi.gr", "password": "qqQQ11!!"}'
```
![image](https://github.com/user-attachments/assets/26bf5866-cdbe-433f-929f-4a038d15c576)

---

## ML Service: Πρόβλεψη τύπου χρήστη

Το αρχείο `train_from_mongo.py` ανακτά **user baskets** από τη MongoDB, δημιουργεί πίνακα `user_id × product_id` και εφαρμόζει KMeans.

```bash
docker compose run --rm ml_service python train_from_mongo.py
```

```bash
curl -X POST http://localhost:5001/predict \
  -H "Content-Type: application/json" \
  -d '{"basket": [1,0,0,0,1,0,0,1,0,0,0,1,0,0,1,0,0,0,1,0]}'
```

![image](https://github.com/user-attachments/assets/e3d6390a-7c66-4de2-9912-3f91759c211e)

---

## Node-RED Flow για πρόβλεψη από ML Service

Το SmartCart περιλαμβάνει και Node-RED integration που επιτρέπει **real-time πρόβλεψη** μέσω `/predict`.

### Οδηγίες:

1. Ανοίξτε: [http://localhost:1880](http://localhost:1880)
2. **Import** το αρχείο `smartcart_nodered_predict_flow.json`
3. Πατήστε **Deploy**
4. Πατήστε το κουμπί `Send Basket` και δίτε το αποτέλεσμα

Το flow στέλνει δεδομένα καλαθιού στο `http://smartcart_ml_service:5001/predict` και εμφανίζει την απάντηση στο sidebar.

![image](https://github.com/user-attachments/assets/8afaa912-4aea-4dbc-adb9-6a068280c67c)


---

## Jenkins (Pipeline από SCM)

1. Εκκίνηση:

```bash
docker compose -f jenkins-standalone.yml up -d
```

2. Άνοιγμα: [http://localhost:8080](http://localhost:8080)

3. Ανάκτηση κωδικού:

```bash
docker exec smartcart_jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

4. Δημιουργία Pipeline:

   * Τύπος: **Pipeline**
   * Definition: *Pipeline script from SCM*
   * SCM: Git
   * Repo URL: `https://github.com/ebairachtari/eb_smartcart_containers`
   * Script Path: `Jenkinsfile`
   * Branch: `*/main`

5. Build now!


>*Αναπτύχθηκε αποκλειστικά για εκπαιδευτικούς σκοπούς.*
