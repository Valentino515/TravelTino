from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime
import pytz

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
        if destination:
            return redirect(destination)  
    return render_template('destinacije.html')

@app.route('/kontakt', endpoint="kontakt")
def kontakt():
    return render_template('kontakt.html')

def vzpostavi_povezavo_z_bazo():
    con = sqlite3.connect('baza_uporabnikov.db')
    con.row_factory = sqlite3.Row 
    return con

def inicializiraj_bazo():
    con = sqlite3.connect('baza_uporabnikov.db')
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS baza_uporabnikov (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ime TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            geslo TEXT NOT NULL,
            admin INTEGER DEFAULT 0,
            cas_registracije TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    con.commit()

    lokalni_cas = datetime.now(pytz.timezone('Europe/Ljubljana')).strftime('%Y-%m-%d %H:%M:%S')

    cur.execute("SELECT * FROM baza_uporabnikov WHERE email = ?", ("admin@email.com",))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO baza_uporabnikov (ime, email, geslo, admin, cas_registracije) 
            VALUES (?, ?, ?, ?, ?)
        """, ("tino", "admin@email.com", "admin123", 1, lokalni_cas))
        con.commit()

    con.close()

inicializiraj_bazo()

def baza_posodobi_geslo():
    con = sqlite3.connect('posodobljenagesla.db')
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS posodobljenagesla_uporabniki (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ime TEXT NOT NULL,
            email TEXT NOT NULL,
            staro_geslo TEXT NOT NULL,
            novo_geslo TEXT NOT NULL,
            cas_posodobitve TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()

baza_posodobi_geslo()


def baza_rezervacij():

    con = sqlite3.connect('baza_rezervacije.db')
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rezervacije(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ime TEXT NOT NULL,
            priimek TEXT NOT NULL,
            email TEXT NOT NULL,
            telefon TEXT NOT NULL,
            cas_rezervacije TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    con.commit()
    con.close()

baza_rezervacij()

@app.route("/registracija", methods=["GET", "POST"])
def registracija():
    if request.method == "POST":
        uporabnisko_ime = request.form["username"]
        eposta = request.form["email"]
        geslo = request.form["password"]

        con = vzpostavi_povezavo_z_bazo()
        cur = con.cursor()

        cur.execute("SELECT * FROM baza_uporabnikov WHERE email = ?", (eposta,))
        if cur.fetchone():
            con.close()
            napaka = "Uporabniški račun že obstaja."
            return render_template("registracija.html", napaka=napaka)
        
        poslji_email(eposta)

        lokalni_cas = datetime.now(pytz.timezone('Europe/Ljubljana')).strftime('%Y-%m-%d %H:%M:%S')

        cur.execute("INSERT INTO baza_uporabnikov (ime, email, geslo, cas_registracije) VALUES (?, ?, ?, ?)", 
                    (uporabnisko_ime, eposta, geslo, lokalni_cas))
        con.commit()

        con.close()

        return redirect(url_for("prijava"))

    return render_template("registracija.html")

# Pošiljanje emaila
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
        uporabnisko_ime = request.form["username"]

        con = vzpostavi_povezavo_z_bazo()
        cur = con.cursor()

        cur.execute("SELECT * FROM baza_uporabnikov WHERE email = ?", (eposta,))
        uporabnik = cur.fetchone()
        con.close()

        if uporabnik and uporabnik["geslo"] == geslo:
            if uporabnik["admin"] == 1:
                if uporabnisko_ime != ADMIN_IME or eposta != ADMIN_EMAIL or geslo != ADMIN_GESLO:
                    napaka = "Ne morete se prijaviti kot admin!"
                    return render_template("prijava.html", napaka=napaka)

            session["uporabnik"] = uporabnik["ime"]
            session["admin"] = uporabnik["admin"]

            if uporabnik["admin"] == 1:
                return redirect(url_for("admin"))
            else:
                return redirect(url_for("nadzornaplosca"))

        napaka = "Napačni podatki! Poskusite znova."
        return render_template("prijava.html", napaka=napaka)

    return render_template("prijava.html")


@app.route("/nadzornaplosca", methods=["GET", "POST"])
def nadzornaplosca():
    if "uporabnik" in session:
        return render_template("nadzorna_plosca.html", uporabnik=session['uporabnik'])
    return redirect(url_for("prijava"))

@app.route("/odjava", methods=["GET", "POST"])
def odjava():
    session.pop("uporabnik", None)
    return redirect(url_for("prijava"))

@app.route("/admin")
def admin():
    if "uporabnik" not in session or session["admin"] != 1:
        return redirect(url_for("prijava", napaka="Ne morete se prijaviti kot admin!")) 

    con = vzpostavi_povezavo_z_bazo()
    cur = con.cursor()

    cur.execute("SELECT * FROM baza_uporabnikov")
    uporabniki = cur.fetchall()

    con.close()

    con2 = sqlite3.connect('posodobljenagesla.db')
    con2.row_factory = sqlite3.Row
    cur2 = con2.cursor()

    cur2.execute("SELECT * FROM posodobljenagesla_uporabniki")
    posodobljeni_uporabniki = cur2.fetchall()

    con2.close()

    con3 = sqlite3.connect('baza_rezervacije.db')
    con3.row_factory = sqlite3.Row
    cur3 = con3.cursor()
    
    cur3.execute("SELECT * FROM rezervacije")
    rezervacije_uporabnikov = cur3.fetchall()
    
    con3.close()


    return render_template("narejen_uporabniski_racun.html", uporabniki=uporabniki, posodobljeni_uporabniki=posodobljeni_uporabniki,rezervacije_uporabnikov=rezervacije_uporabnikov)

#drugi teden
@app.route("/posodobigeslo", methods=["GET", "POST"])
def posodobigeslo():
    if request.method == "POST":
        uporabnisko_ime = request.form["username"]
        eposta = request.form["email"]
        novo_geslo = request.form["new_password"]

        con = vzpostavi_povezavo_z_bazo()
        cur = con.cursor()

        cur.execute("SELECT * FROM baza_uporabnikov WHERE ime = ? AND email = ?", (uporabnisko_ime, eposta))
        uporabnik = cur.fetchone()

        if uporabnik:
            
            staro_geslo = uporabnik["geslo"]
                        
            cur.execute("UPDATE baza_uporabnikov SET geslo = ? WHERE ime = ? AND email = ?",
                        (novo_geslo, uporabnisko_ime, eposta))
            con.commit()

            con2 = sqlite3.connect('posodobljenagesla.db')
            cur2 = con2.cursor()

            lokalni_cas = datetime.now(pytz.timezone('Europe/Ljubljana')).strftime('%Y-%m-%d %H:%M:%S')

            cur2.execute("""INSERT INTO posodobljenagesla_uporabniki 
                (ime, email,staro_geslo, novo_geslo, cas_posodobitve) 
                VALUES (?, ?, ?, ?,?)""", 
                (uporabnisko_ime, eposta,staro_geslo,novo_geslo, lokalni_cas))

            con2.commit()
            con2.close()
            con.close()

            poslji_email_posodobitev(eposta, uporabnisko_ime)

            return redirect(url_for("prijava"))

        else:
            napaka = "Uporabnik s tem imenom in e-pošto ne obstaja!"
            con.close()
            return render_template("posodobitevgesla.html", napaka=napaka)

    return render_template("posodobitevgesla.html")



def poslji_email_posodobitev(eposta, ime):
    poslalec_emaila = 'traveltino515@gmail.com'
    geslo_emaila = 'cvfs hwxh nvxw sjgo'
    prejemnik_emaila = eposta

    predmet = 'Uspešna posodobitev gesla'
    telo = f"""
    Pozdravljeni, {ime}!

    Vaše geslo je bilo uspešno posodobljeno.
    Če tega niste storili vi, se čim prej obrnite na našo podporo.

    Lep pozdrav,
    TravelTino ekipa 
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


@app.route('/pariz',endpoint="pariz")
def pariz():
    return render_template('pariz.html')

@app.route('/barcelona',endpoint="barcelona")
def barcelona():
    return render_template('barcelona.html')

@app.route('/rim',endpoint="rim")
def rim():
    return render_template('rim.html')

@app.route('/london',endpoint="london")
def london():
    return render_template('london.html')

@app.route('/amsterdam',endpoint="amsterdam")
def amsterdam():
    return render_template('amsterdam.html')

@app.route('/praga',endpoint="praga")
def praga():
    return render_template('praga.html')


@app.route("/poslji_mail", methods=["POST"])
def poslji_mail():
    ime = request.form["name"]
    email = request.form["email"]
    telefon = request.form["phone"]
    predmet = request.form["subject"]
    sporocilo = request.form["message"]
   
    vsebina = f"""
    Novo Sporočilo:

    Ime: {ime}
    Email: {email}
    Telefon: {telefon}
    Predmet: {predmet}

    Sporočilo:
    {sporocilo}
    """

    msg = EmailMessage()
    msg.set_content(vsebina)
    msg["Subject"] = f"Sporočilo: {predmet}"
    msg["From"] = "traveltino515@gmail.com"
    msg["To"] = "traveltino515@gmail.com"

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login("traveltino515@gmail.com", "cvfs hwxh nvxw sjgo")
        smtp.send_message(msg)

    return redirect("/kontakt")


#tretji teden
@app.route("/rezervacija", methods=["GET", "POST"])
def rezervacija():
    
    if request.method == "POST":
        ime = request.form["ime"]
        priimek = request.form["priimek"]
        email = request.form["email"]
        telefon = request.form["telefon"]
        cas_rezervacije = datetime.now(pytz.timezone('Europe/Ljubljana')).strftime('%Y-%m-%d %H:%M:%S')

        con = sqlite3.connect('baza_uporabnikov.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM baza_uporabnikov WHERE ime = ? AND email = ?", (ime, email))
        uporabnik = cur.fetchone()
        con.close()

        if not uporabnik:
            
            napaka = "Morate se najprej registrirati/prijaviti kot uporabnik!"
            return render_template("rezervacija.html", napaka=napaka)
        
        session["ime"] = ime

        con = sqlite3.connect('baza_rezervacije.db')
        cur = con.cursor()
        cur.execute(""" 
            SELECT * FROM rezervacije 
            WHERE ime = ? AND priimek = ? AND email = ? AND telefon = ?
        """, (ime, priimek, email, telefon))
        rezervacija_obstaja = cur.fetchone()
        con.close()

        if rezervacija_obstaja:
            napaka = "Rezervacija s temi podatki že obstaja. Preverite ali ste že izvedli rezervacijo."
            return render_template("rezervacija.html", napaka=napaka)

        con = sqlite3.connect('baza_rezervacije.db')
        cur = con.cursor()
        cur.execute("""
            INSERT INTO rezervacije (ime, priimek, email, telefon, cas_rezervacije)
            VALUES (?, ?, ?, ?, ?)
        """, (ime, priimek, email, telefon, cas_rezervacije))
        con.commit()
        con.close()

        poslji_email_potrditve(ime, email)
        return redirect(url_for("nadzornaploscarezervacij"))

    return render_template("rezervacija.html")




@app.route("/nadzornaploscarezervacij", methods=["GET", "POST"])
def nadzornaploscarezervacij():
    if "uporabnik" in session:
        return render_template("nadzorna_plosca_rezervacij.html", uporabnik=session['uporabnik'])
    return redirect(url_for("rezervacija"))


def poslji_email_potrditve(ime, email):
    vsebina = f"""
    Pozdravljeni {ime},

    Vaša rezervacija je bila uspešno zabeležena.

    Hvala za vašo prijavo!
    Ekipa
    """

    sporocilo = EmailMessage()
    sporocilo["Subject"] = "Potrditev rezervacije"
    sporocilo["From"] = "traveltino515@gmail.com"
    sporocilo["To"] = email
    sporocilo.set_content(vsebina)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login("traveltino515@gmail.com", "cvfs hwxh nvxw sjgo")
        smtp.send_message(sporocilo)


@app.route('/iskanjedestinacij', methods=["GET"])
def search():
    destinacije = ["pariz", "barcelona", "rim", "london", "amsterdam", "praga"]
    iskano = request.args.get("q", "").strip().lower()

    if iskano in destinacije:
        return render_template(f"{iskano}.html")
    
    if iskano: 
        return render_template("napaka.html", napaka=f"Destinacija '{iskano}' ni bila najdena.")
    
    return render_template("destinacije.html", seznam=destinacije)




if __name__ == "__main__":
    app.run(debug=True)
