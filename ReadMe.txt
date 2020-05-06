1) Check you are using python >= 3.6
2) git clone, cd into concerto
3) python -m venv venv
4) source venv/bin/activate
5) pip install -r requirements.txt

Depending on OS, set environment variables. In linux can do the following:
6) DATABASE_URL=sqlite:///concertodb.sqlite PORT=1234 GRAPHENEDB_BOLT_URL=bolt://hobby-mabefkdfpfnpgbkeidfjibel.dbs.graphenedb.com:24787 GRAPHENEDB_BOLT_USER=app165797402-whlMBz GRAPHENEDB_BOLT_PASSWORD=b.haIfSFb0QIdh.OKaTA6wEgyIoz3nf python app.py
7) Visit 127.0.0.1:1234 in browser
8) Logins: admin, other, everythinglover, poplover, rocklover. All passwords are 123.
9) Search for a concert, click carpool. Find it in the carpool tab. Use incognito mode to repeat steps on another account.

You can use SQlite db viewer to see the database, open concertodb.sqlite.