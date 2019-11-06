
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
# accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session, url_for

tmpl_dir = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = "super secret key"

# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@35.243.220.243/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@35.243.220.243/proj1part2"
#
DATABASEURI = "postgresql://mg4106:0411@35.243.220.243/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute(
    """INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")



@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request 
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request.

    The variable g is globally accessible.
    """
    if 'logged_in' not in session:
        session['logged_in'] = False 

    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't, the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/', methods=['GET', 'POST'])
def restaurants():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2
    """
    if session['logged_in']:
        print(session['userid'])

    if request.method == 'POST' and request.form["button"] == 'Search':
        print(request.form['button'])
        print(f'The method is post')
        search_name = request.form['name']  # name of the search query
        print(f'search name is : {search_name}')
        cursor = g.conn.execute(f"""
        SELECT * FROM Restaurant_owns r
        WHERE LOWER(r.name) LIKE '%%{search_name}%%'"""
                                )
        names = []
        for result in cursor:
            names.append(result)  # can also be accessed using result[0]
        cursor.close()

        # name = request.form['name']
        # g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)

    #

    #
    # example of a database query
    #
    # cursor = g.conn.execute("SELECT name FROM test")
    else:
        cursor = g.conn.execute('''
        SELECT * FROM Restaurant_owns r 
        ''')
        names = []
        for result in cursor:
            names.append(result)
        cursor.close()

    #
    # Flask uses Jinja templates, which is an extension to HTML where you can
    # pass data to a template and dynamically generate HTML based on the data
    # (you can think of it as simple PHP)
    # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
    #
    # You can see an example template in templates/index.html
    #
    # context are the variables that are passed to the template.
    # for example, "data" key in the context variable defined below will be
    # accessible as a variable in index.html:
    #
    #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
    #     <div>{{data}}</div>
    #
    #     # creates a <div> tag for each element in data
    #     # will print:
    #     #
    #     #   <div>grace hopper</div>
    #     #   <div>alan turing</div>
    #     #   <div>ada lovelace</div>
    #     #
    #     {% for n in data %}
    #     <div>{{n}}</div>
    #     {% endfor %}
    #
    context = dict(data=names)

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/restaurants.html
    #
    return render_template("restaurants.html", **context)


@app.route('/login', methods=["GET", "POST"])
def login():
    # abort(401)
    # this_is_never_executed()
    error = False
    if(session['logged_in']):
        return redirect(url_for('restaurants'))
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        print("Details", username, password)
        cursor = g.conn.execute(
            "SELECT * FROM Users WHERE userid='{}' and password='{}'".format(username, password))
        counter = 0
        for _ in cursor:
            counter += 1
        if counter == 0:
            print("curson None")
            error = True
            return render_template('login.html', error=error)
        else:
            print("Logged In")
            session['logged_in'] = True
            session['userid'] = request.form['username']
            return redirect(url_for('restaurants'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session['logged_in'] = False
    session['userid'] = None
    return redirect(url_for('restaurants'))


@app.route('/restaurants/<id>')
def another(id):

    # get the name and the rid of the url
    cursor = g.conn.execute(f'''
        SELECT r.name, r.rid FROM Restaurant_owns r 
        WHERE r.rid =  '{id}'
        ''')
    for result in cursor:
        restaurant_name = result[0]
        restaurant_id = result[1]

    # get the locations of the given rid
    locations = []
    cursor = g.conn.execute(f'''
        SELECT * from Location_isat l
        WHERE l.rid = '{id}'
    ''')
    for location in cursor:
        locations.append(location)

    # get normal user reviews
    normal_reviews = []
    cursor = g.conn.execute(f'''
        SELECT * FROM reviews_gives r
        WHERE r.userid IN 
        (SELECT n.userid FROM normal n)
        and r.rid ='{id}'
    ''')
    for review in cursor:
        normal_reviews.append(review)

    # get critic reviews
    critic_reviews = []
    cursor = g.conn.execute(f'''
        SELECT * FROM reviews_gives r
        WHERE r.userid IN 
        (SELECT c.userid FROM critic c ) and r.rid ='{id}'
    ''')

    for review in cursor:
        critic_reviews.append(review)

    # get menu items
    menu_items = []
    cursor = g.conn.execute(f'''
        SELECT m.name, m.category, m.cost, m.descr, m.type
        FROM menu_item m
        WHERE m.rid = '{id}' 
    ''')

    for item in cursor:
        food_type = item['']

    context = {'name': restaurant_name, 'id': restaurant_id}
    return render_template('restaurant_page.html', **context)

    print(id)
    return render_template('another.html')


if __name__ == "__main__":
    import click

    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using:

            python server.py

        Show the help text using:

            python server.py --help

        """

        # HARD CODED. REMOVE AFTER DEBUGGING
        debug = True
        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

    run()
