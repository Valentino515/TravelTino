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