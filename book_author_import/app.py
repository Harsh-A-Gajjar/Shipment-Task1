from flask import Flask, render_template, request, redirect, url_for, flash, g, session
import pandas as pd
import os
import psycopg2
from psycopg2 import sql

app = Flask(__name__)
app.secret_key = '3b2d49a252718d31c4c4a2c21a5f9a38a1c275f3541e5988'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create the uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# PostgreSQL database configuration
DATABASE = {
    'dbname': 'books_authors_db',
    'user': 'postgres',
    'password': 'HG040401',
    'host': 'localhost',
    'port': '5432'
}

def connect_db():
    conn = psycopg2.connect(**DATABASE)
    return conn

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = connect_db()
        cursor = db.cursor()
        with app.open_resource('schema.sql', mode='r') as f:
            cursor.execute(f.read())
        db.commit()
        cursor.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and file.filename.endswith(('.xls', '.xlsx')):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        session['uploaded_file'] = file.filename  # Store filename in session
        flash('File successfully uploaded')

        try:
            data = pd.read_excel(file_path)
            return render_template('review.html', data=data.to_html(index=False))
        except Exception as e:
            flash(f'Error processing file: {e}')
            return redirect(url_for('index'))
    else:
        flash('Invalid file type. Please upload an Excel file.')
        return redirect(request.url)

@app.route('/confirm', methods=['POST'])
def confirm_upload():
    filename = session.get('uploaded_file')
    if not filename:
        flash('No file uploaded')
        return redirect(url_for('index'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.isfile(file_path):
        flash('Uploaded file not found')
        return redirect(url_for('index'))

    try:
        data = pd.read_excel(file_path)
        cursor = g.db.cursor()

        for index, row in data.iterrows():
            cursor.execute(
                'INSERT INTO authors (name, email, date_of_birth) VALUES (%s, %s, %s) RETURNING id',
                (row['Author Name'], row['Author Email'], row['Author DOB'])
            )
            author_id = cursor.fetchone()[0]

            cursor.execute(
                'INSERT INTO books (name, isbn_code, author_id) VALUES (%s, %s, %s)',
                (row['Book Name'], row['ISBN Code'], author_id)
            )

        g.db.commit()
        cursor.close()

        flash('Data successfully saved to the database!')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error processing file: {e}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
