from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import csv
from datetime import datetime
import pdfkit
import io
from io import BytesIO

# Initialize Flask application
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://scardinal_user:Pq9CUtUCtrhouYgvkmYIAzTLHadU2hdT@dpg-cv2peijtq21c73f2ijj0-a.oregon-postgres.render.com/scardinal'
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
    phone = db.Column(db.String(20), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    date_added = db.Column(db.DateTime, default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

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

# Configure wkhtmltopdf for PDF export
# PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")

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
    return render_template('index.html', customers=customers, search_query=search_query, company_filter=company_filter, date_sort=date_sort)

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

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.email = request.form['email']
        customer.phone = request.form['phone']
        customer.company = request.form['company']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit_customer.html', customer=customer)

@app.route('/delete/<int:id>')
@login_required
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return redirect(url_for('index'))

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