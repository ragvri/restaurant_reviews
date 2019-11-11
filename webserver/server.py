
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


def get_username(userid):
    # returns the name of the userid
    cursor = g.conn.execute(f'''
    SELECT name
        FROM users
        WHERE userid = '{userid}'
    ''')
    for result in cursor:
        name = result[0]
    return name


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
    logged_in = False
    username = None
    if session['logged_in']:
        logged_in = True
        userid = session['userid']
        username = get_username(userid)

    if request.method == 'POST' and request.form["button"] == 'Search':
        search_name = request.form['name']  # name of the search query
        cursor = g.conn.execute(f"""
        SELECT * FROM restaurant_owns r
        WHERE LOWER(r.name) LIKE '%%{search_name}%%'
        ORDER BY lower(r.name) ASC 
        """
                                )
        names = []
        for result in cursor:
            names.append(result)
        cursor.close()

    else:
        cursor = g.conn.execute('''
        SELECT * FROM restaurant_owns r
        ORDER BY lower(r.name) ASC 
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
    context = {'data': names, 'logged_in': logged_in, 'username': username}
    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/restaurants.html
    #
    return render_template("restaurants.html", **context)

@app.route('/create_account/', methods = ['GET', 'POST'])
def create_new_account():
    created = False
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        typ = request.form['type']
        if str(typ).lower() == 'user':
            cursor =  g.conn.execute(f'''
            SELECT COUNT(*)
            FROM normal
            ''')
            for result in cursor:
                number = int(result[0])+1
            new_user = 'n' + str(number)

            # insert new user in database
            cursor = g.conn.execute(f"""
            INSERT INTO users VALUES (
                '{new_user}', '{name}', '{password}'
            )
            """)
            cursor = g.conn.execute(f""" 
            INSERT INTO normal VALUES (
                '{new_user}'
            )
            """)

        else: 
            cursor = g.conn.execute('''
            SELECT COUNT(*)
            FROM critic 
            ''')
            for result in cursor:
                number = int(result[0])+1
            new_user = 'c' + str(number)
            
            cursor = g.conn.execute(f"""
            INSERT INTO users VALUES (
                '{new_user}', '{name}', '{password}'
            )
            """)


            curors = g.conn.execute(f"""
            INSERT INTO critic VALUES (
                '{new_user}', 0 
            ) 
            """)
        created = True
        context = {'userid': new_user, 'password': password, 
        'created':created}
        return render_template('create_new_account.html', **context)
    context = {'created':created}
    return render_template('create_new_account.html', **context)


@app.route('/login/', methods=["GET", "POST"])
def login():
    error = False
    if(session['logged_in']):
        return redirect(url_for('restaurants'))
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        cursor = g.conn.execute(
            "SELECT * FROM users WHERE userid='{}' and password='{}'".format(username, password))
        counter = 0
        for _ in cursor:
            counter += 1
        if counter == 0:
            error = True
            return render_template('login.html', error=error)
        else:
            session['logged_in'] = True
            session['userid'] = request.form['username']
            return redirect(url_for('restaurants'))
    return render_template('login.html', error=error)


@app.route('/nearby/<lat>/<long>/')
def nearby(lat, long):
    logged_in = False
    username = None
    if(session['logged_in']):
        logged_in = True
        userid = session['userid']
        username = get_username(userid)
    cursor = g.conn.execute(f'''
        SELECT r.rid, r.name, l.building, l.capacity, l.city, l.state, l.zip, calculate_distance({lat}, {long}, l.lat, l.long, 'K') as distance
        FROM location_isat l, restaurant_owns r
        WHERE l.lat!='{lat}' and l.long!='{long}' and r.rid=l.rid
        ORDER BY distance
        LIMIT 5
    ''')

    class restaurant():
        def __init__(self, data):
            self.rid = data[0]
            self.name = data[1]
            self.building = data[2]
            self.capacity = data[3]
            self.city = data[4]
            self.state = data[5]
            self.zip = data[6]
            self.dis = round(data[7], 3)
    n_restaurants = []
    for results in cursor:
        n_restaurants.append(restaurant(results))

    context = {'nearby': n_restaurants, 'logged_in': logged_in, 'username': username}
    return render_template('nearby.html', **context)

@app.route('/add-<id>/', methods = ['POST', 'GET'])
def add(id):
    rest_id = id
    error = False
    cursor = g.conn.execute(f'''
        SELECT r.userid 
        FROM restaurant_owns r
        WHERE r.rid = '{rest_id}' 
    ''')
    for result in cursor:
        owner_id = result
    owner_id = owner_id['userid']
    userid = None
    username = None
    if session['logged_in']:
        userid = session['userid']
        username = get_username(userid)
    # only the owner should be able to access the page
    if str(userid)!=str(owner_id): 
        return redirect(url_for('restaurants'))

    if request.method =='POST':
        name = request.form['name']
        category = request.form['category']
        cost = request.form['cost']
        description = request.form['description']
        typ = request.form['type']

        try: 
            cursor  = g.conn.execute(f'''
            INSERT INTO menu_item 
            VALUES ('{name}', '{category}', {cost}, '{description}',
            '{typ}', '{rest_id}'
            )''') 
        except : 
            print(f'Unable to insert\n')
            error = True
            context = {'id': id, 'error': error}
            return render_template(f'add_menu.html', **context) 
        return redirect(f'/restaurants/{rest_id}/') 
     
    
    
    context = {'id': id, 'error': error, 'username': username}
    return render_template(f'add_menu.html', **context)

@app.route('/restaurants/<id>/', methods=['POST', 'GET'])
def restaurant_page(id):

    # check if logged in. If yes, get the userid
    logged_in = False
    user_critic_logged = False
    owner_logged = False
    userid = None
    username = None
    is_critic = False
    # get owner id of the restaurantcursor = g.conn.execute(f'''
    
    cursor = g.conn.execute(f""" 
        SELECT r.userid 
        FROM restaurant_owns r
        WHERE r.rid = '{id}' 
    """)
    for result in cursor:
        owner_id = result
    owner_id = owner_id['userid']
    userid = None
    
    if(session['logged_in']):
        logged_in = True
        userid = session['userid']
        username = get_username(userid)
        if str(userid).startswith('c'):
            is_critic = True
        if str(userid).startswith('n') or str(userid).startswith('c'):
            user_critic_logged = True
            # print(f'USER critic logged in')
        elif str(userid) == str(owner_id):
            owner_logged = True

    # handle the case when a review is liked.
    if request.method == 'POST':
        # print(f"{request.form['normal_like']} this is the data")
        if 'normal_like' in request.form:
            revid = request.form['normal_like']
            # print(f'revid is {revid}')
            cursor = g.conn.execute(f'''
                UPDATE reviews_gives   
                SET likes = likes+1
                WHERE revid = '{revid}' 
            ''')
        elif 'critic_like' in request.form:
            critic_id, revid = request.form['critic_like'].split('-')
            # print(f'critic_id: {critic_id}, revid:{revid}')
            cursor = g.conn.execute(f'''
                UPDATE reviews_gives 
                SET likes = likes+1
                WHERE revid = '{revid}' 
            ''')
            # update the average score of the critc
            cursor = g.conn.execute(f'''
                UPDATE critic
                SET score = 
                (
                    SELECT round(avg(t.likes),2)
                    FROM critic c, reviews_gives t
                    where t.userid = c.userid and 
                    c.userid = '{critic_id}'
                    group by c.userid 
                ) 
                WHERE userid = '{critic_id}'
            ''')
        elif 'critic_favourite' in request.form:
            critic_id, lat, long = request.form['critic_favourite'].split('/')
            # print(f'{critic_id} {lat} {long}')
            try: 
                cursor = g.conn.execute(f"""
                INSERT INTO favourite VALUES(
                    '{critic_id}', {lat}, {long}
                ) 
            """)
            except: 
                print('already exists?') 
    # get the name and the rid of the url
    cursor = g.conn.execute(f'''
        SELECT r.name, r.rid FROM restaurant_owns r 
        WHERE r.rid =  '{id}'
        ''')
    for result in cursor:
        restaurant_name = result[0]
        restaurant_id = result[1]

    # get the locations of the given rid
    locations = []
    cursor = g.conn.execute(f'''
        SELECT * from location_isat l
        WHERE l.rid = '{id}'
    ''')
    for location in cursor:
        locations.append(location)
    # get normal user reviews
    normal_reviews = []
    cursor = g.conn.execute(f'''
        SELECT r.text,r.likes, r.rating, u.name, u.userid, r.revid
        FROM reviews_gives r, users u
        WHERE r.userid IN 
        (SELECT n.userid FROM normal n)
        and r.userid = u.userid
        and r.rid ='{id}'
        ORDER BY r.likes DESC
    ''')
    for review in cursor:
        normal_reviews.append(review)

    # get critic reviews
    critic_reviews = []
    cursor = g.conn.execute(f'''
        SELECT r.text, r.likes, r.rating, u.name, u.userid, r.revid
        FROM reviews_gives r, users u
        WHERE r.userid IN 
        (SELECT c.userid FROM critic c ) and 
        r.userid = u.userid and 
        r.rid ='{id}'
        ORDER BY r.likes DESC
    ''')

    for review in cursor:
        critic_reviews.append(review)

    # get menu items
    menu_items = []
    cursor = g.conn.execute(f'''
        SELECT m.rid, m.name, m.category, m.cost, m.descr, m.typ
        FROM menu_item m
        WHERE m.rid = '{id}' 
    ''')

    for item in cursor:
        menu_items.append(item)

    # get similar restaurants
    similar_restaurants = []
    cursor = g.conn.execute(f'''
        SELECT s1.rid2, r1.name 
        from similar_rest s1, restaurant_owns r1 
        WHERE s1.rid1 = '{id}' 
        and r1.rid = s1.rid2
        UNION 
        SELECT s2.rid1, r2.name 
        from similar_rest s2, restaurant_owns r2 
        WHERE s2.rid2 = '{id}'
        and r2.rid = s2.rid1
    ''')

    for restaurant in cursor:
        similar_restaurants.append(restaurant)

    context = {'name': restaurant_name, 'id': restaurant_id, 'similar': similar_restaurants,
               'menu': menu_items, 'critic_reviews': critic_reviews,
               'normal_reviews': normal_reviews, 'locations': locations,
               'user_critic_logged_in': user_critic_logged, 'owner_logged': owner_logged,
               'logged_in': logged_in, 'user_id':userid, 'username': username, 
               'is_critic': is_critic}
    return render_template('restaurant_page.html', **context)


@app.route('/give_review/<id>/', methods=["GET", "POST"])
def give_review(id):
    username = None
    if(session['logged_in']):
        userid = session['userid']
        username = get_username(userid)
        if userid.startswith('r'):
            return redirect(url_for('restaurants'))
        if request.method == 'POST':
            cursor = g.conn.execute(f'''
                SELECT COUNT(*) 
                FROM reviews_gives
            ''')

            for results in cursor:
                revid = str(results[0]+1)

            text = request.form['text']
            rating = request.form['rating']
            cursor = g.conn.execute(f'''
                INSERT INTO reviews_gives
                VALUES ('{revid}', '{text}', 0, {rating}, '{userid}', '{id}')
            ''')

            cursor = g.conn.execute(f'''
                UPDATE restaurant_owns
                SET u_rating = (SELECT ROUND(AVG(rating), 2)
                                FROM reviews_gives
                                WHERE rid='{id}' and userid like 'n%%' 
                                GROUP BY rid),
                c_rating = (SELECT ROUND(AVG(rating), 2)
                                FROM reviews_gives
                                WHERE rid='{id}' and userid like 'c%%' 
                                GROUP BY rid)
                WHERE rid = '{id}'
            ''')
            return redirect(f'/restaurants/{id}/')
        else:
            return render_template('give_review.html')
    return redirect(url_for('restaurants'))


@app.route('/logout/', methods=["GET", "POST"])
def logout():
    if(session['logged_in']):
        if request.method == "POST":
            session['logged_in'] = False
            session['userid'] = None
            return redirect(url_for('restaurants'))
        else:
            userid = session['userid']
            cursor = g.conn.execute(f'''
                SELECT name
                FROM users
                WHERE userid = '{userid}'
            ''')
            for result in cursor:
                name = result[0]
            return render_template('logout.html', name=name)

    return redirect(url_for('restaurants'))


@app.route('/critics/<id>/')
def critic(id):
    logged_in = False
    username = None
    if session['logged_in']:
        logged_in = True
        userid = session['userid']
        username = get_username(userid)
    cursor = g.conn.execute(f'''
        SELECT u.name, c.score
        FROM critic as c, users as u
        WHERE c.userid = u.userid and c.userid = '{id}'
    ''')
    for result in cursor:
        critic_name = result[0]
        critic_score = result[1]

    cursor = g.conn.execute(f'''
        SELECT r.rid, r.name, rv.text, rv.likes, rv.rating
        FROM critic as c, reviews_gives as rv, restaurant_owns as r
        WHERE c.userid = rv.userid and c.userid = '{id}' and rv.rid = r.rid
        ORDER BY (rv.likes) DESC
    ''')

    reviews = []

    class review:
        def __init__(self, data):
            self.rid = data[0]
            self.name = data[1]
            self.text = data[2]
            self.likes = data[3]
            self.rating = data[4]

    for result in cursor:
        reviews.append(review(result))

    cursor = g.conn.execute(f'''
        SELECT r.rid, r.name, l.building, l.state, l.city, l.zip
        FROM  critic as c, favourite as f, location_isat as l, restaurant_owns as r
        WHERE c.userid = '{id}' and  c.userid = f.userid and f.lat = l.lat and f.long = l.long and l.rid = r.rid
    ''')

    fav = [] 
    critic_has_fav = False
    for result in cursor:
        fav.append(result) 
        critic_has_fav = True

    context = {'name': critic_name, 'score': critic_score, 'logged_in': logged_in,
               'favourite': fav, 'reviews': reviews, 'username': username,
               'critic_has_fav':critic_has_fav
               }
    return render_template('critics.html', **context)

@app.route('/restaurants/<id>/update/<item>/', methods=['POST', 'GET'])
def update_item(id, item):

    username = None
    if(session['logged_in']):
        userid = session['userid']
        username = get_username(userid)
        cursor = g.conn.execute(f'''
            SELECT *
            FROM restaurant_owns 
            WHERE userid = '{userid}' and rid = '{id}'
        ''')
        
        flag = 0
        for _ in cursor:
            flag+=1
        # print(flag)
        if(flag == 0):
            return redirect(url_for('restaurants'))

        if(request.method == 'POST'):
            category = request.form['category']
            cost = request.form['cost']
            desc = request.form['description']
            typ = request.form['type']

            cursor = g.conn.execute(f'''
                UPDATE menu_item
                SET category = '{category}', cost = {cost}, descr = '{desc}', typ = '{typ}'
                WHERE rid = '{id}' and name = '{item}'
            ''')
            return redirect(f'/restaurants/{id}')

        cursor = g.conn.execute(f'''
            SELECT category, cost, descr, typ 
            FROM menu_item
            WHERE rid = '{id}' and name = '{item}'
        ''')
        name = item
        # print(name)
        for result in cursor:
            # print('result', result)
            category = result[0]
            cost = result[1]
            desc = result[2]
            typ = result[3]
        # print('type', typ)
        context = {'name': name, 'category': category, 'cost': cost, 'desc': desc, 'type': typ, 'username': username}
        return render_template('update.html', **context)


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
        # debug = True
        HOST, PORT = host, port
        print("running on %s:%d" % (HOST, PORT))
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

    run()
