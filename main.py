from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import smtplib
import ssl
from email.message import EmailMessage


app = Flask(__name__)
app.secret_key = 'skrivni-kljuc'

ADMIN_IME = "tino"
ADMIN_EMAIL = "admin@email.com"
ADMIN_GESLO = "admin123"


@app.route('/')
def domov():
    return render_template('index.html')

@app.route('/destinations', methods=["GET", "POST"])
def destinacije():
    if request.method == "POST":
        destination = request.form.get('q')  
        return render_template('destinacije.html', destination=destination)
    return render_template('destinacije.html', destination=None)

@app.route('/kontakt', endpoint="kontakt")
def kontakt():
    return render_template('kontakt.html')

def vzpostavi_povezavo_z_bazo():
    con = sqlite3.connect('zaposleni.db')
    con.row_factory = sqlite3.Row 
    return con

def inicializiraj_bazo():
    con = vzpostavi_povezavo_z_bazo()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS zaposleni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ime TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            geslo TEXT NOT NULL,
            admin INTEGER DEFAULT 0)""")
    con.commit()

    cur.execute("SELECT * FROM zaposleni WHERE email = ?", (ADMIN_EMAIL,))
    if not cur.fetchone():
        cur.execute("INSERT INTO zaposleni (ime, email, geslo, admin) VALUES (?, ?, ?, ?)", 
                    (ADMIN_IME, ADMIN_EMAIL, ADMIN_GESLO, 1))  
        con.commit()

    con.close()


inicializiraj_bazo()

@app.route("/registracija", methods=["GET", "POST"])
def registracija():
    if request.method == "POST":
        uporabnisko_ime = request.form["username"]
        eposta = request.form["email"]
        geslo = request.form["password"]

        con = vzpostavi_povezavo_z_bazo()
        cur = con.cursor()

        cur.execute("SELECT * FROM zaposleni WHERE email = ?", (eposta,))
        if cur.fetchone():
            con.close()
            napaka = "Uporabniški račun že obstaja."
            return render_template("registracija.html", napaka=napaka)
        
        poslji_email(eposta)

        cur.execute("INSERT INTO zaposleni (ime, email, geslo) VALUES (?, ?, ?)", 
                    (uporabnisko_ime, eposta, geslo))
        con.commit()
        con.close()

        return redirect(url_for("prijava"))

    return render_template("registracija.html")


def poslji_email(eposta):
    poslalec_emaila = 'traveltino515@gmail.com'
    geslo_emaila = 'cvfs hwxh nvxw sjgo'
    prejemnik_emaila = eposta  

    predmet = 'Potrditev registracije'
    telo = """
    Uspešno ste se registrirali v sistem. Dobrodošli!
    """

    em = EmailMessage()
    em['From'] = poslalec_emaila
    em['To'] = prejemnik_emaila
    em['Subject'] = predmet
    em.set_content(telo)


    kontekst = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=kontekst) as smtp:
        smtp.login(poslalec_emaila, geslo_emaila)
        smtp.sendmail(poslalec_emaila, prejemnik_emaila, em.as_string())



@app.route("/prijava", methods=["GET", "POST"])
def prijava():
    if request.method == "POST":
        eposta = request.form["email"]
        geslo = request.form["password"]

        con = vzpostavi_povezavo_z_bazo()
        cur = con.cursor()

        cur.execute("SELECT * FROM zaposleni WHERE email = ?", (eposta,))
        uporabnik = cur.fetchone()
        con.close()

        if uporabnik and uporabnik["geslo"] == geslo:
            if uporabnik["admin"] == 1:
                if uporabnik["ime"] != ADMIN_IME or uporabnik["email"] != ADMIN_EMAIL:
                    return "Neveljavna prijava kot admin", 403

            session["uporabnik"] = uporabnik["ime"]
            session["admin"] = uporabnik["admin"]

            if uporabnik["admin"] == 1:
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("nadzornaplosca"))

        napaka = "Napačni podatki! Poskusite znova."
        return render_template("prijava.html", napaka=napaka)

    return render_template("prijava.html")



@app.route("/nadzornaplosca",methods=["GET", "POST"])
def nadzornaplosca():
    if "uporabnik" in session:
        return render_template("nadzorna_plosca.html", uporabnik=session['uporabnik'])
    return redirect(url_for("prijava"))

@app.route("/odjava",methods=["GET", "POST"])
def odjava():
    session.pop("uporabnik", None)
    return redirect(url_for("prijava"))

@app.route("/admin")
def admin():
    if "uporabnik" not in session or session["admin"] != 1:
        return "Nimate dovoljenja za ogled uporabniških računov.", 403  

    con = vzpostavi_povezavo_z_bazo()
    cur = con.cursor()

    cur.execute("SELECT * FROM zaposleni")
    uporabniki = cur.fetchall()

    con.close()

    return render_template("narejen_uporabniski_racun.html", uporabniki=uporabniki)

if __name__ == "__main__":
    app.run(debug=True)
