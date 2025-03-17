import pytest
from app import app, db, Users, Customer, Transaction
from flask_bcrypt import Bcrypt
from flask_login import login_user

bcrypt = Bcrypt(app)

@pytest.fixture
def client():
    """Setup Flask test client"""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"  # Use in-memory DB for tests
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing forms
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.session.rollback()  # Ensure rollback before teardown
            db.drop_all()

@pytest.fixture
def init_database():
    """Initialize the database with test data"""
    with app.app_context():
        # Ensure test user does not already exist
        user = Users.query.filter_by(username="testuser").first()
        if not user:
            hashed_password = bcrypt.generate_password_hash("testpassword").decode("utf-8")
            user = Users(username="testuser", password=hashed_password)
            db.session.add(user)
            db.session.commit()

        customer = Customer(name="John Doe", email="john@example.com", phone="1234567890", company="TestCorp")
        db.session.add(customer)
        db.session.commit()

        order = Transaction(customer_id=customer.id, product="Laptop", amount=1000.0, status="Completed")
        db.session.add(order)
        db.session.commit()

@pytest.fixture
def login(client, init_database):
    """Login the test user"""
    return client.post("/login", data={"username": "testuser", "password": "testpassword"}, follow_redirects=True)

def test_homepage_redirect(client):
    """Ensure homepage redirects if not logged in"""
    response = client.get("/", follow_redirects=True)
    assert b"Login" in response.data

def test_login_success(client, init_database):
    """Test successful login"""
    response = client.post("/login", data={"username": "testuser", "password": "testpassword"}, follow_redirects=True)
    assert b"Welcome" in response.data

def test_login_failure(client, init_database):
    """Test failed login"""
    response = client.post("/login", data={"username": "wronguser", "password": "wrongpassword"}, follow_redirects=True)
    assert b"Invalid username or password" in response.data

def test_logout(client, login):
    """Test logout functionality"""
    response = client.get("/logout", follow_redirects=True)
    assert b"Logged out successfully" in response.data or b"Login" in response.data  # Adjust based on redirect behavior

def test_register(client):
    """Test user registration"""
    response = client.post("/register", data={"username": "newuser", "password": "newpassword"}, follow_redirects=True)
    assert b"User registered successfully!" in response.data

def test_add_customer(client, login):
    """Test adding a new customer"""
    response = client.post("/add", data={"name": "Alice", "email": "alice@example.com", "phone": "9876543210", "company": "AliceCorp"}, follow_redirects=True)
    assert b"Alice" in response.data

def test_edit_customer(client, login, init_database):
    """Test editing customer information"""
    with app.app_context():
        customer = Customer.query.first()

    response = client.post(f"/edit_customer/{customer.id}", data={"name": "Updated Name", "email": "updated@example.com", "phone": "1112223333", "company": "UpdatedCorp"}, follow_redirects=True)
    assert b"Updated Name" in response.data

def test_delete_customer(client, login, init_database):
    """Test deleting a customer"""
    with app.app_context():
        customer = Customer.query.first()

    response = client.post(f"/delete_customer/{customer.id}", follow_redirects=True)
    assert b"Welcome" in response.data

def test_add_order(client, login, init_database):
    """Test adding a new order"""
    with app.app_context():
        customer = Customer.query.first()

    response = client.post("/add_order", data={"customer_id": customer.id, "product": "Phone", "amount": "500", "status": "Pending"}, follow_redirects=True)
    assert b"Phone" in response.data

def test_edit_order(client, login, init_database):
    """Test editing an order"""
    with app.app_context():
        order = Transaction.query.first()

    response = client.post(f"/edit_order/{order.id}", data={"customer_id": order.customer_id, "product": "Updated Product", "amount": "600", "status": "Shipped"}, follow_redirects=True)
    assert b"Updated Product" in response.data

def test_delete_order(client, login, init_database):
    """Test deleting an order"""
    with app.app_context():
        order = Transaction.query.first()

    response = client.post(f"/delete_order/{order.id}", follow_redirects=True)
    assert b"Welcome" in response.data

def test_export_csv(client, login, init_database):
    """Test CSV export"""
    response = client.get("/export/csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert b"Name,Email,Phone,Company" in response.data

def test_export_pdf(client, login, init_database):
    """Test PDF export"""
    response = client.get("/export/pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
