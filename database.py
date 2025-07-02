import sqlite3 #database
from datetime import datetime # Zaman Modülü
import os

def veritabaniOlustur():
    conn = sqlite3.connect("database.db") # Database Bağlantısını gerçekleştirdik
    cursor = conn.cursor() # Database üzerinde gezmek için imleç 
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kullanicilar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_adi TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        olusturma_tarihi TEXT,
        sifre TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gorevler (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kullanici_id INTEGER,
        kullanici_adi TEXT, 
        baslik TEXT NOT NULL,
        aciklama TEXT,
        olusturma_tarihi TEXT,
        bitis_tarihi TEXT,
        oncelik TEXT,
        durum TEXT,
        atanan_kullanici_adi TEXT,
        FOREIGN KEY(kullanici_id) REFERENCES kullanicilar(id)
    )
    """)

    conn.commit()
    conn.close()
    print("Veritabanı Başarılı Bir Şekilde Oluşturuldu!")


def kullanici_Olustur(kullanici_adi, email, olusturma_tarihi, sifre):
    conn = sqlite3.connect("database.db") # Database Bağlantısını gerçekleştirdik
    cursor = conn.cursor() # Database üzerinde gezmek için imleç
    try:
        cursor.execute("""INSERT INTO kullanicilar (kullanici_adi, email, olusturma_tarihi, sifre)VALUES (?, ?, ?, ?)""", (kullanici_adi, email, olusturma_tarihi, sifre))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def kullanici_getir(kullanici_adi, sifre):
    conn = sqlite3.connect("database.db") # Database Bağlantısını gerçekleştirdik
    cursor = conn.cursor() # Database üzerinde gezmek için imleç
    cursor.execute("SELECT id, kullanici_adi, email FROM kullanicilar WHERE kullanici_adi=? AND sifre=?", (kullanici_adi, sifre))
    sonuc = cursor.fetchone()
    conn.close()
    return sonuc

def kullanici_adi_getir(kullanici_id):
    conn = sqlite3.connect("database.db") # Database Bağlantısını gerçekleştirdik
    cursor = conn.cursor() # Database üzerinde gezmek için imleç
    cursor.execute("SELECT kullanici_adi FROM kullanicilar WHERE id = ?", (kullanici_id,))
    sonuc = cursor.fetchone()
    conn.close()
    return sonuc[0] if sonuc else None

def gorev_ekle(kullanici_id, kullanici_adi, baslik, aciklama, bitis_tarihi, oncelik, atanan_kullanici_adi):
    conn = sqlite3.connect("database.db") # Database Bağlantısını gerçekleştirdik
    cursor = conn.cursor() # Database üzerinde gezmek için imleç
    try:
        olusturma_tarihi = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        durum = "Tamamlanmadı"
        cursor.execute("""
            INSERT INTO gorevler (kullanici_id, kullanici_adi, baslik, aciklama, olusturma_tarihi, bitis_tarihi, oncelik, durum, atanan_kullanici_adi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (kullanici_id, kullanici_adi, baslik, aciklama, olusturma_tarihi, bitis_tarihi, oncelik, durum, atanan_kullanici_adi))
        conn.commit()
        gorev_id = cursor.lastrowid  # görev id
        gorev_txt_olustur(gorev_id,kullanici_adi,atanan_kullanici_adi,baslik,aciklama,olusturma_tarihi,bitis_tarihi,oncelik,durum)

        return True
    except Exception as e:
        return False
    finally: 
        conn.close()

def gorevleri_getir(sayfa=1, sayfa_basi=3, arama="", oncelik="tümü", durum="tümü"):
    offset = (sayfa - 1) * sayfa_basi
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    query = """ SELECT id, kullanici_id, kullanici_adi, baslik, aciklama, olusturma_tarihi, bitis_tarihi, oncelik, durum, atanan_kullanici_adi FROM gorevler WHERE 1=1"""
    params = []

    #  Arama ID ya da başlığa göre
    if arama:
        if arama.isdigit():
            query += " AND id = ?"
            params.append(int(arama))
        else:
            query += " AND LOWER(baslik) LIKE ?"
            params.append(f"%{arama}%")

    #  Öncelik filtresi
    if oncelik != "tümü":
        query += " AND LOWER(oncelik) = ?"
        params.append(oncelik)

    # Durum filtresi
    if durum != "tümü":
        query += " AND LOWER(durum) = ?"
        params.append(durum)

    # 🔁 Sıralama ve sayfalama
    query += " ORDER BY bitis_tarihi ASC LIMIT ? OFFSET ?"
    params += [sayfa_basi, offset]

    cursor.execute(query, params)
    gorevler = cursor.fetchall()
    conn.close()
    return gorevler

def tum_kullanicilar():
    conn = sqlite3.connect("database.db") # Database Bağlantısını gerçekleştirdik
    cursor = conn.cursor() # Database üzerinde gezmek için imleç
    cursor.execute("SELECT id, kullanici_adi FROM kullanicilar")
    sonuc = cursor.fetchall()
    conn.close()
    return sonuc

def gorev_sil_db(gorev_id):
    print(f"GÖREV SİL ÇAĞRILDI — ID: {gorev_id}")  # debug
    conn = sqlite3.connect("database.db") # Database Bağlantısını gerçekleştirdik
    cursor = conn.cursor() # Database üzerinde gezmek için imleç
    cursor.execute("DELETE FROM gorevler WHERE id = ?", (int(gorev_id),))
    conn.commit()
    conn.close()
    gorev_txt_sil(gorev_id)

def gorev_guncelle(gorev_id, baslik, aciklama, bitis_tarihi, oncelik, durum, atanan_kullanici):
    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        # .txt için: kullanici_adi ve olusturma_tarihi lazım
        cursor.execute("""SELECT kullanici_adi, olusturma_tarihi FROM gorevler WHERE id = ?""", (gorev_id,))
        sonuc = cursor.fetchone()
        if not sonuc:
            conn.close()
            return False

        kullanici_adi, olusturma_tarihi = sonuc

        # Güncelle
        cursor.execute("""UPDATE gorevler SET baslik = ?, aciklama = ?, bitis_tarihi = ?, oncelik = ?, durum = ?, atanan_kullanici_adi = ? WHERE id = ?""", (baslik, aciklama, bitis_tarihi, oncelik, durum, atanan_kullanici, gorev_id))
        conn.commit()
        conn.close()

        # .txt dosyasını güncelle
        gorev_txt_guncelle(gorev_id, kullanici_adi, atanan_kullanici, baslik, aciklama, olusturma_tarihi, bitis_tarihi, oncelik, durum)
        return True
    except Exception as e:
        print("Güncelleme Hatası:", e)
        return False

def gorev_txt_olustur(gorev_id, kullanici_adi, atanan_kullanici_adi, baslik, aciklama, olusturma_tarihi, bitis, oncelik, durum):
    with open(f"Görev Numarası - {gorev_id}.txt", "w", encoding="utf-8") as f:
        f.write(f"Görev ID: '{gorev_id}'\n")
        f.write(f"Oluşturan Kullanıcı: '{kullanici_adi}'\n")
        f.write(f"Atanan Kullanıcı: '{atanan_kullanici_adi}'\n")
        f.write(f"Başlık: '{baslik}'\n")
        f.write(f"Açıklama: '{aciklama}'\n")
        f.write(f"Oluşturma Tarihi: '{olusturma_tarihi}'\n")
        f.write(f"Bitiş Tarihi: '{bitis}'\n")
        f.write(f"Öncelik: '{oncelik}'\n")
        f.write(f"Durum: '{durum}'\n")

def gorev_txt_guncelle(gorev_id, kullanici_adi, atanan_kullanici_adi, baslik, aciklama, olusturma_tarihi, bitis, oncelik, durum):
    gorev_txt_olustur(gorev_id, kullanici_adi, atanan_kullanici_adi, baslik, aciklama, olusturma_tarihi, bitis, oncelik, durum)


def gorev_txt_sil(gorev_id):
    try:
        os.remove(f"Görev Numarası - {gorev_id}.txt")
    except FileNotFoundError:
        pass


def tum_gorev_ozeti(kullanici_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Toplam
    cursor.execute("SELECT COUNT(*) FROM gorevler WHERE kullanici_id = ?", (kullanici_id,))
    toplam = cursor.fetchone()[0]

    # Bekleyen
    cursor.execute("SELECT COUNT(*) FROM gorevler WHERE kullanici_id = ? AND LOWER(durum) = 'tamamlanmadı'", (kullanici_id,))
    bekleyen = cursor.fetchone()[0]

    # Tamamlanan
    cursor.execute("SELECT COUNT(*) FROM gorevler WHERE kullanici_id = ? AND LOWER(durum) = 'tamamlandı'", (kullanici_id,))
    tamamlanan = cursor.fetchone()[0]

    # Acil görev (öncelik = yüksek)
    cursor.execute("SELECT COUNT(*) FROM gorevler WHERE kullanici_id = ? AND LOWER(oncelik) = 'yüksek'", (kullanici_id,))
    acil = cursor.fetchone()[0]

    # Önceliklere göre sayılar
    cursor.execute("SELECT COUNT(*) FROM gorevler WHERE kullanici_id = ? AND LOWER(oncelik) = 'düşük'", (kullanici_id,))
    dusuk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM gorevler WHERE kullanici_id = ? AND LOWER(oncelik) = 'orta'", (kullanici_id,))
    orta = cursor.fetchone()[0]

    conn.close()

    return {
        "toplam": toplam,
        "bekleyen": bekleyen,
        "tamamlanan": tamamlanan,
        "acil": acil,
        "dusuk": dusuk,
        "orta": orta,
    }
