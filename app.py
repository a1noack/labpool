from collections import OrderedDict
from flask import Flask, Response, request, render_template, redirect, make_response, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import io
import mysql.connector
import numpy as np
import pandas as pd


# Create a Flask app object
app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address
)

DEV = False

# Configure the app to connect to the MySQL database
if DEV:
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'hormone_levels'
else:
    app.config['MYSQL_HOST'] = 'anoack.mysql.pythonanywhere-services.com'
    app.config['MYSQL_USER'] = 'anoack'
    app.config['MYSQL_PASSWORD'] = 'V*bmEFdi#NN4GF'
    app.config['MYSQL_DB'] = 'anoack$hormone_levels'
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'mHPEE5K!WnF4@Y'

# Create a MySQL connection object
mysql = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)

display_names = {
    'hdl': 'HDL Cholesterol (mg/dL)',
    'ldl': 'LDL Cholesterol (mg/dL)',
    'luteinizing_hormone': 'Luteinizing Hormone (mIU/mL)',
    'total_testosterone': 'Total Testosterone (ng/dL)',
    'shbg': 'Sex Horm Binding Glob, Serum (nmol/L)',
    'free_testosterone': 'Free Testosterone (pg/mL)',
    'igf1': 'Insulin-Like Growth Factor I (ng/mL)'
}

# Set up the routes for the website
@app.route('/', methods=['GET', 'POST'])
@limiter.limit("1/second")
def index():
    # If the user has submitted the form, save the hormone levels to the database
    if request.method == 'POST':

        # get the data from the form
        hdl = request.form['hdl']
        ldl = request.form['ldl']
        luteinizing_hormone = request.form['luteinizing_hormone']
        total_testosterone = request.form['total_testosterone']
        shbg = request.form['shbg']
        free_testosterone = request.form['free_testosterone']
        igf1 = request.form['igf1']

        # save data in session variable for use on other pages
        session['data'] = {'hdl':hdl, 'ldl':ldl, 'luteinizing_hormone':luteinizing_hormone,
            'total_testosterone': total_testosterone, 'shbg': shbg,
            'free_testosterone':free_testosterone, 'igf1': igf1
        }

        cursor = mysql.cursor()
        cursor.execute("""INSERT INTO levels (hdl, ldl, luteinizing_hormone, total_testosterone, shbg, free_testosterone, igf1) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (hdl, ldl, luteinizing_hormone, total_testosterone, shbg, free_testosterone, igf1))
        mysql.commit()
        cursor.close()

        return redirect('/graph')

    # Otherwise, render the form template
    return render_template('form.html', display_names=display_names)

def get_population_data():
    # load reference ranges
    df = pd.read_csv('static/data/ref_ranges.csv')
    # else:
    #     df = pd.read_csv('labpool/static/data/ref_ranges.csv')
    df['mean'] = (df['high'] + df['low']) / 2
    df['std'] = (df['high'] - df['low']) / 4
    n_markers = len(df.marker)

    # generate data
    n_points = 10000
    n_bins = 100
    decimal_digits = 2  # the number of digits after the decimal to keep
    population_data = {}
    for row, marker in enumerate(df.marker, start=1):
        mean = df.loc[df['marker'] == marker]['mean'].item()
        std = df.loc[df['marker'] == marker]['std'].item()
        # dist = [int(std * random.random() + mean) for _ in range(n_points)]
        arr = np.random.normal(mean, std, n_points)
        arr.sort()

        min_val = arr.min()
        max_val = arr.max()
        range_val = max_val - min_val
        section_size = range_val / n_bins

        counts = OrderedDict()
        for value in arr:
            # Calculate the index of the section
            section_index = int((value - min_val) / section_size) * section_size
            section_index = round(section_index, decimal_digits)

            # Increment the count for the section
            if section_index in counts:
                counts[section_index] += 1/n_points
            else:
                counts[section_index] = 1/n_points

        x = list(counts.keys())
        y = list(counts.values())

        population_data[marker] = [x, y]

        # dist = [int(i) for i in dist if i > 0]
        # jump = (max(dist) - min(dist)) / n_bins

        # x = []
        # y = []
        # for i in np.arange(min(dist), max(dist)+1, jump):
        #     num_i = 0
        #     for j in dist:
        #         if j < i+jump and j >= i:
        #             num_i += 1
        #     x.append(i)
        #     y.append(num_i/n_points)
        #
        # population_data[marker] = [x, y]

    return population_data

@app.route('/graph')
def render_plot():
    population_data = get_population_data()
    return render_template("graph.html", population_data=population_data, user_data=session['data'], display_names=display_names)
