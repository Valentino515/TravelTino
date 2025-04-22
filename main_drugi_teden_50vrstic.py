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



def baza_rezervacij():
    con = sqlite3.connect('baza_rezervacije.db')
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rezervacije (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ime TEXT NOT NULL,
            email TEXT NOT NULL,
            cas_rezervacije TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()
	
baza_rezervacij()