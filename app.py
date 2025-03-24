from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import csv
from datetime import datetime, UTC
import pdfkit
import io
from io import BytesIO

# Initialize Flask application
app = Flask(__name__)

# Docker Database
app.config.from_prefixed_env()

# Preprod Database
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/crm'

# Production Database
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://crm_4uxp_user:apQQwtlQnA9lxK3URcnsjaw01M77fAQF@dpg-cv25525ds78s73e5r200-a.oregon-postgres.render.com/crm_4uxp'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model for authentication
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

# Customer model for CRM
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    company = db.Column(db.String(100))
    date_added = db.Column(db.DateTime, default=datetime.now(UTC))
    orders = db.relationship('Transaction', backref='customer', lazy=True)  # Relationship with Order table

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pending")
    date_ordered = db.Column(db.DateTime, default=datetime.now(UTC))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id))

# Create the database tables
with app.app_context():
    db.create_all()

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Users.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

# Route for user logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    session.clear()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        new_user = Users(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/export/csv')
@login_required
def export_csv():
    search_query = request.args.get('search', '')
    company_filter = request.args.get('company', '')
    date_sort = request.args.get('date_sort', 'desc')

    query = Customer.query
    if search_query:
        query = query.filter(Customer.name.ilike(f'%{search_query}%') |
                             Customer.email.ilike(f'%{search_query}%') |
                             Customer.company.ilike(f'%{search_query}%'))
    if company_filter:
        query = query.filter(Customer.company.ilike(f'%{company_filter}%'))
    if date_sort == 'asc':
        query = query.order_by(Customer.date_added.asc())
    else:
        query = query.order_by(Customer.date_added.desc())

    customers = query.all()

    # Use StringIO to handle text data
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Company', 'Date Added'])

    for customer in customers:
        writer.writerow([customer.id, customer.name, customer.email, customer.phone, customer.company,
                         customer.date_added.strftime('%Y-%m-%d %H:%M:%S')])

    # Convert StringIO to BytesIO for Flask response
    output.seek(0)
    byte_output = io.BytesIO(output.getvalue().encode('utf-8'))

    return send_file(byte_output, mimetype='text/csv', as_attachment=True, download_name='customers.csv')

# Windows configuration wkhtmltopdf for PDF export
# PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

# Docker configuration wkhtmltopdf for PDF export
PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')

# Route for exporting customer data as a styled PDF
@app.route('/export/pdf')
@login_required
def export_pdf():
    search_query = request.args.get('search', '')
    company_filter = request.args.get('company', '')
    date_sort = request.args.get('date_sort', 'desc')

    query = Customer.query
    if search_query:
        query = query.filter(Customer.name.ilike(f'%{search_query}%') |
                             Customer.email.ilike(f'%{search_query}%') |
                             Customer.company.ilike(f'%{search_query}%'))
    if company_filter:
        query = query.filter(Customer.company.ilike(f'%{company_filter}%'))
    if date_sort == 'asc':
        query = query.order_by(Customer.date_added.asc())
    else:
        query = query.order_by(Customer.date_added.desc())

    customers = query.all()
    rendered = render_template('export_pdf.html', customers=customers, branding=True, now=datetime.now())
    pdf = pdfkit.from_string(rendered, False, configuration=PDFKIT_CONFIG)
    pdf_output = BytesIO(pdf)
    return send_file(pdf_output, mimetype='application/pdf', as_attachment=True, download_name='customers.pdf')

# Home page displaying customer records
@app.route('/')
@login_required
def index():
    search_query = request.args.get('search', '')
    company_filter = request.args.get('company', '')
    date_sort = request.args.get('date_sort', 'desc')

    query = Customer.query

    if search_query:
        query = query.filter(Customer.name.ilike(f'%{search_query}%') |
                             Customer.email.ilike(f'%{search_query}%') |
                             Customer.company.ilike(f'%{search_query}%'))
    if company_filter:
        query = query.filter(Customer.company.ilike(f'%{company_filter}%'))
    if date_sort == 'asc':
        query = query.order_by(Customer.date_added.asc())
    else:
        query = query.order_by(Customer.date_added.desc())

    customers = query.all()
    orders = Transaction.query.all()
    return render_template('index.html', customers=customers, orders=orders, search_query=search_query, company_filter=company_filter, date_sort=date_sort)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        company = request.form['company']
        new_customer = Customer(name=name, email=email, phone=phone, company=company)
        db.session.add(new_customer)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_customer.html')


# Edit Customer Route
@app.route('/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
def edit_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    if request.method == 'POST':
        customer.name = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form['phone']
        customer.company = request.form['company']

        db.session.commit()
        flash("Customer updated successfully!", "success")
        return redirect(url_for('index'))

    return render_template('edit_customer.html', customer=customer)

@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    customer = db.session.get(Customer, customer_id)

    # Prevent deletion if customer has existing orders
    if customer.orders:
        flash("Cannot delete customer with existing orders!", "danger")
        return redirect(url_for('index'))

    db.session.delete(customer)
    db.session.commit()
    flash("Customer deleted successfully!", "danger")
    return redirect(url_for('index'))

# Route to display customers
@app.route('/customers')
@login_required
def customer():
    customers = Customer.query.order_by(Customer.date_added.desc()).all()
    return render_template('customers.html', customers=customers)

# Add Order Route
@app.route('/add_order', methods=['GET', 'POST'])
def add_order():
    customers = Customer.query.all()
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product = request.form['product']
        amount = request.form['amount']
        status = request.form['status']

        new_order = Transaction(customer_id=customer_id, product=product, amount=amount, status=status)
        db.session.add(new_order)
        db.session.commit()
        flash("Order added successfully!", "success")
        return redirect(url_for('index'))

    return render_template('add_order.html', customers=customers)

# Edit Order Route
@app.route('/edit_order/<int:order_id>', methods=['GET', 'POST'])
def edit_order(order_id):
    order = db.session.get(Transaction, order_id)
    customers = Customer.query.all()

    if request.method == 'POST':
        order.customer_id = request.form['customer_id']
        order.product = request.form['product']
        order.amount = request.form['amount']
        order.status = request.form['status']

        db.session.commit()
        flash("Order updated successfully!", "success")
        return redirect(url_for('index'))

    return render_template('edit_order.html', order=order, customers=customers)

# Delete Order Route
@app.route('/delete_order/<int:order_id>', methods=['POST', 'GET'])
def delete_order(order_id):
    order = db.session.get(Transaction, order_id)
    db.session.delete(order)
    db.session.commit()
    flash("Order deleted successfully!", "danger")
    return redirect(url_for('index'))

# Route to display orders
@app.route('/orders')
@login_required
def order():
    orders = Transaction.query.order_by(Transaction.date_ordered.desc()).all()
    return render_template('orders.html', orders=orders)

# Route for generating reports
@app.route('/report')
@login_required
def report():
    total_customers = Customer.query.count()
    companies = db.session.query(Customer.company, db.func.count(Customer.id)).group_by(Customer.company).all()
    recent_customers = Customer.query.order_by(Customer.date_added.desc()).limit(5).all()
    return render_template('report.html', total_customers=total_customers, companies=companies, recent_customers=recent_customers)

# Run the application
if __name__ == '__main__':
    app.run(debug=True)