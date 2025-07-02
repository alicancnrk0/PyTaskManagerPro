import customtkinter as ctk # UI Arayüz Modülü
from database import veritabaniOlustur, kullanici_Olustur, kullanici_getir, kullanici_adi_getir, gorev_ekle, gorevleri_getir, tum_kullanicilar, gorev_sil_db, gorev_guncelle, tum_gorev_ozeti # Database Modülü Sqlite3 kullandım basit ve işlevli
from tkinter import messagebox  # Verilerin boş olmaması ve kontrolü için mesaj kutusu
from datetime import datetime # Zaman Modülü
from tkcalendar import Calendar # Takvim Modülü
import re # Kelime vs. aramak için gerekli fonksiyon mail doğrulamada kullandım
import os # Os fonksyion
import sys # Sys fonksiyonu


veritabaniOlustur() # Uygulama Çalıştığında veritabanı tabloları oluşturulması için
ctk.set_appearance_mode("black") # Tema
ctk.set_default_color_theme("green")  # blue, green, dark-blue

app = None # Global uygulama değişkeni
aktif_kullanici_id = None # global kullanıcı ID 
content_frame = None # Global menü içeriği yakalamak için
takvim_frame = None # Takvim eklemek için
aktif_kullanici_bilgi = {}
giris = None
kayitol = None

def uygulamaKapat(): # Uygulama kapatma fonksiyonu 
    app.destroy() # destroy uygulama kapatır

def resource_path(relative_path): # Pyınstaller için fixledim dosya yolunu bulamıyor bazen
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path) # os ile aldım
    return os.path.join(os.path.abspath("."), relative_path)

def takvim_ac(entry_widget, anchor_widget=None): # Takvim oluşturmak için fonksiyon
    global takvim_frame

    if takvim_frame:
        takvim_frame.destroy()
        takvim_frame = None
        return

    # Takvim konumu: anchor_widget varsa ona göre, yoksa entry'ye göre konum al
    target = anchor_widget if anchor_widget else entry_widget
    x = target.winfo_rootx()
    y = target.winfo_rooty() + target.winfo_height()

    takvim_frame = ctk.CTkToplevel()
    takvim_frame.overrideredirect(True)  # kenarlık vs. yok
    takvim_frame.geometry(f"+{x}+{y}") # x+y pozisoynu ayarladım
    takvim_frame.configure(fg_color="white") #beyaz olsun arka planı

    cal = Calendar(takvim_frame, selectmode='day', date_pattern='dd-mm-yyyy', locale='tr_TR') # gün ay yıl 
    cal.pack(padx=5, pady=5)

    def tarih_sec(event=None):
        secilen_tarih = cal.get_date()
        entry_widget.configure(state="normal")
        entry_widget.delete(0, "end")
        entry_widget.insert(0, secilen_tarih)
        entry_widget.configure(state="readonly")
        takvim_frame.destroy()

    cal.bind("<<CalendarSelected>>", tarih_sec)

def email_dogrula(email): # email @gmail.com vs. gibi algılanması için
    desen = r"^[\w\.-]+@[\w\.-]+\.\w{2,}$" 
    return re.match(desen, email) is not None

def kart_hover_efekti(kart): # detaylar üzerinde gezerken kart hover yaptım
    def hover_acik(_):
        kart.configure(fg_color="#3a3a3a")

    def hover_kapali(_):
        # Mouse hala kart içindeyse çıkmasın diye kontrol ettim
        x, y = kart.winfo_pointerxy()
        widget = kart.winfo_containing(x, y)
        try:
            if widget is None or not str(widget).startswith(str(kart)):
                kart.configure(fg_color="#2e2e2e")
        except:
            kart.configure(fg_color="#2e2e2e")

    kart.bind("<Enter>", hover_acik) # buna göre bind atandı
    kart.bind("<Leave>", hover_kapali) # bind atanması

def gorev_sil(gorev_id): # Görev Silme fonksyionu
    onay = messagebox.askyesno("Görev Sil", f"ID {gorev_id} olan görevi silmek istiyor musunuz?") # onay ekranı gönderdim
    if not onay: #kontrol onayı
        return

    try:
        gorev_sil_db(gorev_id) # database çağırıp görevi siliyorum
        messagebox.showinfo("Silindi", f"ID {gorev_id} başarıyla silindi.") #üyeye bilgisi veriliyor
        GorevleriSil()  # listeyi güncelledim
    except Exception as e:
        print("HATA:", e)
        messagebox.showerror("Hata", f"Silme sırasında hata oluştu:\n{str(e)}")

def GorevEkle(): # Görev ekleme fonksyionu
    global gir_bitis_tarihi, takvim_frame # global değişkenleri çağırdım

    for widget in content_frame.winfo_children(): # Önce içerik temizlenir var olan
        widget.destroy()

    ctk.CTkLabel(master=content_frame, text="Yeni Görev Ekle", font=("Segoe UI Black", 20)).pack(pady=20,padx=50)

    ctk.CTkLabel(master=content_frame, text="Görev Başlığı", anchor="w", font=("Segoe UI Black", 13)).pack(pady=(10, 0), padx=5, fill="x")
    gir_baslik = ctk.CTkEntry(master=content_frame, placeholder_text="Başlık")
    gir_baslik.pack(fill="x", padx=20, pady=1)

    ctk.CTkLabel(master=content_frame, text="Görev Açıklaması", anchor="w", font=("Segoe UI Black", 13)).pack(pady=(10, 0), padx=5, fill="x")
    gir_aciklama = ctk.CTkTextbox(master=content_frame, height=230)
    gir_aciklama.pack(fill="x", padx=20, pady=1)

    ctk.CTkLabel(master=content_frame, text="Görev Bitiş Tarihi", anchor="w", font=("Segoe UI Black", 13)).pack(pady=(10, 0), padx=5, fill="x")
    bitis_entry = ctk.CTkEntry(master=content_frame, placeholder_text="Bitiş Tarihi (GG-AA-YYYY)")
    bitis_entry.pack(fill="x", padx=20, pady=1)
    bitis_entry.configure(state="readonly") # Bitiş Tarihini Manuel Olarak Yazdırmak İstemedim Hatalı Giriş İçin Engelledim
    bitis_entry.bind("<Button-1>", lambda e: takvim_ac(bitis_entry)) # Bitiş Tarihi üzerine tıkladığımızda bir tıklama butonu çalıştıracak fonksiyon ile tarihi açacağız.


    kullanicilar = tum_kullanicilar()
    kullanici_adlari = [k[1] for k in kullanicilar]

    ctk.CTkLabel(master=content_frame, text="Görev Atanacak Kullanıcı", anchor="w", font=("Segoe UI Black", 13)).pack(pady=(10, 0), padx=5, fill="x")
    secili_kullanici = ctk.CTkOptionMenu(master=content_frame, values=kullanici_adlari,  fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12))
    secili_kullanici.set(kullanici_adlari[0])
    secili_kullanici.pack(fill="x", padx=20, pady=1)

    ctk.CTkLabel(master=content_frame, text="Görev Öncelik Durumu", anchor="w", font=("Segoe UI Black", 13)).pack(pady=(10, 0), padx=5, fill="x")
    gir_oncelik_secim = ctk.CTkOptionMenu(master=content_frame, values=["Düşük", "Orta", "Yüksek"],  fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12))
    gir_oncelik_secim.set("Düşük")
    gir_oncelik_secim.pack(fill="x", padx=20, pady=1)

    def kaydet(): 
        baslik = gir_baslik.get() # Başlık değerini aldık
        aciklama = gir_aciklama.get("1.0", "end").strip() # Açıklamada TestBox Kullandık 1.0 başlangıç satırı end son satırına kadar olan datayı alır
        bitis_tarihi = bitis_entry.get()  # Bitiş değerini aldık
        oncelik = gir_oncelik_secim.get() # Öncelik Durumunu aldık
        atanan_kullanici_adi = secili_kullanici.get() 

        if not baslik or not aciklama or not bitis_tarihi or not oncelik:
            messagebox.showerror("HATA", "Tüm Alanları Doldurmanız Gerekmektedir!")
            return
        
        kullanici_adi = kullanici_adi_getir(aktif_kullanici_id)

        basarili = gorev_ekle(aktif_kullanici_id, kullanici_adi, baslik, aciklama, bitis_tarihi, oncelik, atanan_kullanici_adi)

        if basarili:
            messagebox.showinfo("Başarı", "Görev Eklendi!")
            GorevleriListele()
        else:
            messagebox.showerror("Hata", "Görev Eklenemdi!")
    
    ctk.CTkButton(master=content_frame, text="Kaydet", font=("Segoe UI Black", 13), command=kaydet).pack(pady=15)

def AnaSayfa():
    for widget in content_frame.winfo_children():
        widget.destroy()

    oncelik = tum_gorev_ozeti(aktif_kullanici_id)
    dusuk = oncelik["dusuk"]
    orta = oncelik["orta"]
    yuksek = oncelik["acil"]
    biten = oncelik["tamamlanan"]
    bitmeyen = oncelik["bekleyen"]
    toplam = oncelik["toplam"]
    # Başlık
    baslik = ctk.CTkLabel(
        master=content_frame,
        text="👋 Hoş geldin!",
        font=("Segoe UI Black", 28),
        text_color="#facc15"
    )
    baslik.pack(pady=(40, 10))

    # Kullanıcı Bilgisi
    kullanici_bilgi_frame = ctk.CTkFrame(content_frame, fg_color="#1e1e1e", corner_radius=10)
    kullanici_bilgi_frame.pack(pady=10, padx=30, fill="x")

    ctk.CTkLabel(
        master=kullanici_bilgi_frame,
        text=f"🆔 Kullanıcı ID: {aktif_kullanici_id}",
        font=("Segoe UI", 14),
        text_color="white"
    ).pack(pady=(10, 0), anchor="w", padx=20)

    ctk.CTkLabel(
        master=kullanici_bilgi_frame,
        text=f"👤 Kullanıcı Adı: {aktif_kullanici_bilgi['kullanici_adi']}",
        font=("Segoe UI", 14),
        text_color="white"
    ).pack(pady=(0, 0), anchor="w", padx=20)

    ctk.CTkLabel(
        master=kullanici_bilgi_frame,
        text=f"📧 Email: {aktif_kullanici_bilgi['email']}",
        font=("Segoe UI", 14),
        text_color="white"
    ).pack(pady=(0, 10), anchor="w", padx=20)

    # Görev Özeti Kutusu
    gorev_frame = ctk.CTkFrame(content_frame, fg_color="#272727", corner_radius=10)
    gorev_frame.pack(pady=10, padx=30, fill="x")

    ctk.CTkLabel(
        master=gorev_frame,
        text="📊 Görev Özeti",
        font=("Segoe UI Black", 16),
        text_color="#93c5fd"
    ).pack(pady=(10, 5))

    ctk.CTkLabel(gorev_frame, text=f"✅ Toplam Görev: {toplam}", font=("Segoe UI", 13), text_color="#e4e4e7").pack(anchor="w", padx=20)
    ctk.CTkLabel(gorev_frame, text=f"🕒 Bekleyen Görev: {bitmeyen}", font=("Segoe UI", 13), text_color="#e4e4e7").pack(anchor="w", padx=20)
    ctk.CTkLabel(gorev_frame, text=f"☑️ Tamamlanan Görev: {biten}", font=("Segoe UI", 13), text_color="#e4e4e7").pack(anchor="w", padx=20, pady=(0, 10))
    ctk.CTkLabel(gorev_frame, text=f"🔥 Yüksek Öncelikli Görev: {yuksek}", font=("Segoe UI", 13), text_color="#e4e4e7").pack(anchor="w", padx=20)
    ctk.CTkLabel(gorev_frame, text=f"⚠️ Orta Öncelikli Görev: {orta}", font=("Segoe UI", 13), text_color="#e4e4e7").pack(anchor="w", padx=20)
    ctk.CTkLabel(gorev_frame, text=f"🧊 Düşük Öncelikli Görev: {dusuk}", font=("Segoe UI", 13), text_color="#e4e4e7").pack(anchor="w", padx=20)

    # Motivasyon Kutusu
    motivasyon_frame = ctk.CTkFrame(content_frame, fg_color="#1f2937", corner_radius=10)
    motivasyon_frame.pack(pady=10, padx=30, fill="x")

    ctk.CTkLabel(
        motivasyon_frame,
        text="💡 Günün Sözü",
        font=("Segoe UI Black", 16),
        text_color="#fca5a5"
    ).pack(pady=(10, 5))

    ctk.CTkLabel(
        motivasyon_frame,
        text="“Başlamak için mükemmel olmak zorunda değilsin,\n ama mükemmel olmak için başlamalısın.”",
        font=("Segoe UI Italic", 13),
        text_color="#d1d5db",
        justify="center"
    ).pack(pady=(0, 10))

    # Versiyon Bilgisi
    surum = ctk.CTkLabel(
        content_frame,
        text="🔧 v1.0 - Developed by Alican Çınarkuyu",
        font=("Segoe UI", 12, "italic"),
        text_color="#6b7280"
    )
    surum.pack(side="bottom", pady=10)


def ana_uygulama(): # Ana uygulama paneli 
    global app, content_frame, aktif_kullanici_id
    app = ctk.CTk()
    app.geometry("900x700")
    app.title("Alican Çınarkuyu - Görev Uygulaması")
    app.iconbitmap(resource_path("image/favicon.ico"))

    # Sol Menü Paneli
    menu_frame = ctk.CTkFrame(master=app, width=240, fg_color="#1f1f1f")
    menu_frame.pack(side="left", fill="y")

    # Kullanıcı Kartı (PACK ile yerleştirildi)
    kullanici_card = ctk.CTkFrame(
        master=menu_frame,
        fg_color="#1f1f1f",
        corner_radius=8,
        border_color="#3b3b3b",
        border_width=1.5,
        width=190,
        height=70
    )
    kullanici_card.pack(padx=10, pady=(10, 5), anchor="nw", fill = "x")  # Burada pack kullandık

    # Kart içi elemanlar (bunlar grid ile olabilir çünkü iç frame içinde)
    kullanici_id_label = ctk.CTkLabel(
        master=kullanici_card,
        text=f"Kullanıcı ID: {aktif_kullanici_id}",
        font=("Segoe UI", 12, "bold"),
        text_color="white"
    )
    kullanici_id_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

    kullanici_adi = ctk.CTkLabel(
        master=kullanici_card,
        text=f"Kullanıcı Adı: {aktif_kullanici_bilgi['kullanici_adi']}",
        font=("Segoe UI", 12, "bold"),
        text_color="#cfcfcf"
    )
    kullanici_adi.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 0))

    kullanici_email_label = ctk.CTkLabel(
        master=kullanici_card,
        text=f"Mail: {aktif_kullanici_bilgi['email']}",
        font=("Segoe UI", 12, "bold"),
        text_color="#cfcfcf"
    )
    kullanici_email_label.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 10))

    buton_opts = {
        "master": menu_frame,
        "fg_color": "#f59e0b",
        "hover_color": "#d97706",
        "text_color": "white",
        "font": ("Segoe UI Black", 14)
    }

    ctk.CTkButton(**buton_opts, text="Ana Sayfa", command=AnaSayfa).pack(padx=10, pady=10)
    ctk.CTkButton(**buton_opts, text="Görevleri Listele", command=GorevleriListele).pack(padx=10, pady=10)
    ctk.CTkButton(**buton_opts, text="Görev Ekle", command=GorevEkle).pack(padx=10, pady=10)
    ctk.CTkButton(**buton_opts, text="Görev Düzenle", command=GorevleriDuzenle).pack(padx=10, pady=10)
    ctk.CTkButton(**buton_opts, text="Görev Sil", command=GorevleriSil).pack(padx=10, pady=10)

    # Çıkış butonu ayrı sabit
    ctk.CTkButton(**buton_opts, text="Çıkış", command=uygulamaKapat).pack(side="bottom", padx=10, pady=10)


    # Sağ Content Paneli
    content_frame = ctk.CTkFrame(master=app, fg_color="#2a2a2a")
    content_frame.pack(side="left", fill="both", expand=True)
    AnaSayfa()
    app.mainloop()

def kayitOl_ekrani(): # Kayıt ol ekranı oluşturma
    global kayitol, giris
    try:
        if giris.winfo_exists():
            giris.destroy()
    except:
        pass

    # kayıt ol ekranı oluşturma
    kayitol = ctk.CTk()
    kayitol.geometry("400x300")
    kayitol.minsize(500, 400)
    kayitol.title("Kayıt Ol")
    kayitol.iconbitmap(resource_path("image/favicon.ico"))


    # Ana çerçeve (hepsi bunun içinde)
    ana_frame = ctk.CTkFrame(master=kayitol)
    ana_frame.pack(expand=True, fill="both", padx=20, pady=30)

    # Başlık
    ctk.CTkLabel(ana_frame, text="Kayıt Ol", font=("Segoe UI Black", 24)).pack(pady=(40, 10))

    # Kullanıcı Adı
    gir_kullanici_adi = ctk.CTkEntry(master=ana_frame, placeholder_text="Kullanıcı Adı")
    gir_kullanici_adi.pack(pady=10, fill="x", padx=65)

    # E-posta
    gir_email = ctk.CTkEntry(master=ana_frame, placeholder_text="E-posta")
    gir_email.pack(pady=10, fill="x", padx=65)

    # Şifre
    gir_sifre = ctk.CTkEntry(master=ana_frame, placeholder_text="Şifre", show="*")
    gir_sifre.pack(pady=10, fill="x", padx=65)

    # Buton
    def kullanici_ekle(): # değerleri alıyorum database göndermek için datetime modülünü de ekstra olarak kullandım tarihi almak için
        kullanici_adi = gir_kullanici_adi.get()
        email = gir_email.get()
        sifre = gir_sifre.get()
        olusturma_tarihi = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        if not kullanici_adi or not email or not sifre: # mail, şifre kullanıcı adı boş mu kontrolü
            messagebox.showerror("Hata", "Tüm Alanlar Doldurulmalı!")
            return

        if not email_dogrula(email): # mail doğru mu diye girilen fonksiyonu çağırıyorum
            messagebox.showerror("Hatalı E-posta", "Lütfen geçerli bir e-posta adresi girin.")
            return

        try: # eğer doğru ise bilgiler oluşturuyorum
            basarili = kullanici_Olustur(kullanici_adi, email, olusturma_tarihi, sifre)
            if basarili:
                messagebox.showinfo("Başarı", "Kayıt Tamamlandı!")
                kayitol.destroy()
                giris_ekrani()
            else: # eğer database tarafında kayıtlı ise hata verdiriyorum
                messagebox.showerror("Hata", "Kullanıcı Adı ve E-posta Zaten Kayıtlı!")
        except Exception as e: # beklenmeyen databaseler hatası için kontrol
            messagebox.showerror("Hata", f"Beklenmeyen bir hata oluştu:\n{str(e)}")

    kayitol_buton = ctk.CTkButton(master=ana_frame, text="Kayıt Ol",font=("Segoe UI Black", 13), command=kullanici_ekle)
    kayitol_buton.pack(pady=20)

    giris_buton = ctk.CTkButton(ana_frame, text="Giriş Yap", font=("Segoe UI Black", 13), command=giris_ekrani, fg_color="#64748b", hover_color="#475569")
    giris_buton.pack(pady=0)

    kayitol.mainloop()

def giris_ekrani(): # Giriş ekranı Oluşturma
    global aktif_kullanici_id, giris, aktif_kullanici_bilgi, kayitol
    
    try: #kayıtol ekranı açık ise kapatma
        if kayitol.winfo_exists():
            kayitol.destroy()
    except:
        pass
    
    #giriş ekranı oluşturma
    giris = ctk.CTk()
    giris.title("Görev Uygulaması - Giriş Yap")
    giris.geometry("400x300")
    giris.minsize(500, 400)
    giris.iconbitmap(resource_path("image/favicon.ico"))


    # Satır ve sütunları orantılı genişlet
    giris.grid_columnconfigure((0, 2), weight=1)  # Kenar boşlukları
    giris.grid_columnconfigure(1, weight=3)       # Ortadaki giriş paneli
    giris.grid_rowconfigure((0, 6), weight=1)     # Üst-alt boşluk
    for i in range(1, 6):
        giris.grid_rowconfigure(i, weight=0)

    # Giriş paneli (ortadaki kutu)
    giris_frame = ctk.CTkFrame(giris, corner_radius=10)
    giris_frame.grid(row=1, column=1, rowspan=5, sticky="nsew", padx=20, pady=20)
    

    giris_frame.grid_columnconfigure(0, weight=1)
    giris_frame.grid_rowconfigure((0, 6), weight=1)

    # Başlık
    ctk.CTkLabel(giris_frame, text="Giriş Yap", font=("Segoe UI Black", 24)).grid(row=0, column=0, pady=(20, 10))

    # Kullanıcı Adı
    gir_kullanici_adi = ctk.CTkEntry(giris_frame, placeholder_text="Kullanıcı Adı")
    gir_kullanici_adi.grid(row=1, column=0, padx=30, pady=10, sticky="ew")

    # Şifre
    gir_sifre = ctk.CTkEntry(giris_frame, placeholder_text="Şifre", show="*")
    gir_sifre.grid(row=2, column=0, padx=30, pady=10, sticky="ew")

    # Giriş Yap Butonu
    def giris_yap(): #giriş bilgilerini formdan çekiyorum
        global aktif_kullanici_id, aktif_kullanici_bilgi
        kullanici_adi = gir_kullanici_adi.get()
        sifre = gir_sifre.get()

        sonuc = kullanici_getir(kullanici_adi, sifre)

        if sonuc: #databaseden bilgileri çekiyorum ve kontrol ediyoruz
            aktif_kullanici_id = sonuc[0]
            aktif_kullanici_bilgi["kullanici_adi"] = sonuc[1]
            aktif_kullanici_bilgi["email"] = sonuc[2]
            messagebox.showinfo("Başarılı", "Giriş Başarılı")
            giris.destroy()
            ana_uygulama()
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre hatalı!")

    girisyap_buton = ctk.CTkButton(giris_frame, text="Giriş Yap", font=("Segoe UI Black", 13), command=giris_yap)
    girisyap_buton.grid(row=3, column=0, padx=30, pady=15, sticky="ew")

    # Kayıt Ol Butonu
    kayitol_buton = ctk.CTkButton(giris_frame, text="Kayıt Ol", font=("Segoe UI Black", 13), command=kayitOl_ekrani, fg_color="#64748b", hover_color="#475569")
    kayitol_buton.grid(row=4, column=0, padx=30, pady=(0, 20), sticky="ew")

    giris.mainloop()

def gorev_txt_oku(gorev_id): #basit bir görev txt okuma fonksiyonu butona atayacağım
    dosya_adi = f"Görev Numarası - {gorev_id}.txt"
    if os.path.exists(dosya_adi):
        os.startfile(dosya_adi)
    else:
        messagebox.showerror("Hata", f"{dosya_adi} bulunamadı.")

def GorevleriListele(sayfa=1, sayfa_basi=3, filtre_arama="", filtre_oncelik="tümü", filtre_durum="tümü"): # Görevleri Listeleyip okuma butonu
    global content_frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    ust_panel = ctk.CTkFrame(master=content_frame, fg_color="transparent")
    ust_panel.pack(fill="x", padx=20, pady=10)

    arama_entry = ctk.CTkEntry(master=ust_panel,fg_color="#374151", text_color="white", font=("Segoe UI Black", 12), placeholder_text="Görev Başlığı veya ID ara...", width=250)
    arama_entry.pack(side="left", padx=5)
    if filtre_arama: 
        arama_entry.insert(0, filtre_arama)

    oncelik_menu = ctk.CTkOptionMenu(master=ust_panel, fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12), values=["Tümü", "Yüksek", "Orta", "Düşük"])
    oncelik_menu.pack(side="left", padx=5)
    oncelik_menu.set(filtre_oncelik.capitalize() if filtre_oncelik != "tümü" else "Öncelik")

    durum_menu = ctk.CTkOptionMenu(master=ust_panel, fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12), values=["Tümü", "Tamamlandı", "Tamamlanmadı"])
    durum_menu.pack(side="left", padx=5)
    durum_menu.set(filtre_durum.capitalize() if filtre_durum != "tümü" else "Durum")

    def filtre_uygula():
        arama = arama_entry.get().strip().lower()
        oncelik = oncelik_menu.get().lower()
        durum = durum_menu.get().lower()

        if oncelik == "öncelik":
            oncelik = "tümü"
        if durum == "durum":
            durum = "tümü"

        GorevleriListele(1, sayfa_basi, filtre_arama=arama, filtre_oncelik=oncelik, filtre_durum=durum)

    ctk.CTkButton(master=ust_panel, text="Filtrele",fg_color="#374151", hover_color="#4B5563",text_color="white", font=("Segoe UI Black", 12), command=filtre_uygula).pack(side="left", padx=10)

    gorevler = gorevleri_getir(sayfa, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)

    if not gorevler:
        ctk.CTkLabel(master=content_frame, text="Hiç görev bulunamadı.", font=("Segoe UI", 12)).pack(pady=20)
        return

    for gorev in gorevler:
        id, kullanici_id, kullanici_adi, baslik, aciklama, olusturma, bitis, oncelik, durum, atanan_kullanici_adi = gorev

        kart = ctk.CTkFrame(master=content_frame, fg_color="#2e2e2e", corner_radius=10)
        kart.pack(fill="x", expand=True, padx=10, pady=5)
        kart_hover_efekti(kart)


        üst_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        üst_satir.pack(fill="x", padx=10, pady=(6, 0))

        ctk.CTkLabel(master=üst_satir, text=f"ID: {id}", font=("Segoe UI", 12, "bold")).pack(side="left")
        ctk.CTkLabel(master=üst_satir, text=baslik, text_color="#e11d48", font=("Segoe UI", 20, "bold")).pack(side="left", expand=True)

        duzenle_buton = ctk.CTkButton(
            master=üst_satir,
            text="Oku",
            width=40,
            fg_color="#6B7280", 
            hover_color="#9CA3AF",
            text_color="white",
            font=("Segoe UI", 11, "bold"),
            command=lambda gid=gorev[0]: gorev_txt_oku(gid)
        )
        duzenle_buton.pack(side="right") 
        duzenle_buton.bind("<Button-1>", lambda e: "break") #Burada ki fonksiyonda kart içerisinde düzenle tıklarsak otomatik detay açıyordu bu şekilde fixledim

        tarih_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        tarih_satir.pack(fill="x", padx=10, pady=(2, 0))
        ctk.CTkLabel(master=tarih_satir, text=f"Oluşturma: {olusturma}", font=("Segoe UI", 12)).pack(side="left")
        ctk.CTkLabel(master=tarih_satir, text=f"Bitiş: {bitis}", font=("Segoe UI", 12)).pack(side="right")

        kisi_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        kisi_satir.pack(fill="x", padx=10, pady=(1, 0))
        ctk.CTkLabel(master=kisi_satir, text=f"Oluşturan: {kullanici_adi}", font=("Segoe UI", 12)).pack(side="left")
        ctk.CTkLabel(master=kisi_satir, text=f"Atanan: {atanan_kullanici_adi}", font=("Segoe UI", 12)).pack(side="right")

        detay_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        detay_satir.pack(fill="x", padx=10, pady=(1, 2))

        oncelik_rengi = {
            "yüksek": "#dc2626",
            "orta": "#8b5cf6",
            "düşük": "#6b7280"
        }.get(oncelik.lower(), "#9ca3af")

        durum_rengi = "#3b82f6" if durum.lower() == "tamamlandı" else "#f97316"

        ctk.CTkLabel(
            master=detay_satir,
            text=f"Öncelik: {oncelik.capitalize()}",
            font=("Segoe UI", 12, "bold"),
            text_color=oncelik_rengi,
            fg_color="transparent"
        ).pack(side="left", padx=(0, 5))

        ctk.CTkLabel(
            master=detay_satir,
            text=f"Durum: {durum.capitalize()}",
            font=("Segoe UI", 12, "bold"),
            text_color=durum_rengi,
            fg_color="transparent"
        ).pack(side="left")

        aciklama_duz = aciklama.replace("\n", " ").replace("\t", " ")
        max_karakter = 120
        kisa_aciklama = aciklama_duz[:max_karakter - 3] + "..." if len(aciklama_duz) > max_karakter else aciklama_duz

        # Açıklama Başlığı
        ctk.CTkLabel(
            master=kart,
            text="Açıklama:",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
            justify="left"
        ).pack(fill="x", padx=10, pady=(0, 2))  # 2px alt boşluk

        # Açıklama Detayı
        ctk.CTkLabel(
            master=kart,
            text=kisa_aciklama,
            font=("Segoe UI", 11),
            anchor="w",
            justify="left",
            wraplength=700
        ).pack(fill="x", padx=10, pady=(0, 4))  # Alt boşluğu da azalttım


        kart.bind("<Button-1>", lambda e, g=gorev: gorev_detay_goster(g))

        for child in kart.winfo_children():
            child.bind("<Button-1>", lambda e, g=gorev: gorev_detay_goster(g))
            # Eğer child içinde alt frame'ler varsa onların çocuklarına da:
            for sub in child.winfo_children():
                sub.bind("<Button-1>", lambda e, g=gorev: gorev_detay_goster(g))

    butonlar = ctk.CTkFrame(master=content_frame)
    butonlar.pack(pady=10)

    def ileri():
        sonraki_gorevler = gorevleri_getir(sayfa + 1, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)
        if sonraki_gorevler:  
            GorevleriListele(sayfa + 1, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)

    def geri():
        if sayfa > 1:
            GorevleriListele(sayfa - 1, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)


    ctk.CTkButton(master=butonlar, text="Geri", fg_color="#4B5563", hover_color="#6B7280", text_color="white", font=("Segoe UI Black", 12),command=geri).pack(side="left", padx=10)
    ctk.CTkButton(master=butonlar, text="İleri", fg_color="#4B5563", hover_color="#6B7280", text_color="white", font=("Segoe UI Black", 12), command=ileri).pack(side="right", padx=10)

def gorev_duzenle_penceresi(gorev): # Görev Düzenleme fonksiyonu ve düzenleme 
    id, kullanici_id, kullanici_adi, baslik, aciklama, olusturma, bitis, oncelik, durum, atanan_kullanici_adi = gorev

    pencere = ctk.CTkToplevel()
    pencere.title(f"Görev Düzenle - ID {gorev[0]}")
    pencere.geometry("600x600")
    pencere.minsize(400, 500)
    pencere.lift()
    pencere.focus_force()
    pencere.attributes("-topmost", True)
    pencere.after(300, lambda: pencere.attributes("-topmost", False))
    pencere.grid_rowconfigure(0, weight=1)
    pencere.grid_columnconfigure(0, weight=1)

    pencere.after(250, lambda: pencere.iconbitmap(resource_path("image/favicon.ico")))  # Bunun için githubda baya dolaşmam gerekti açıkçası popup icon sorunlu o yüzden 250ms sonra ekliyorum


    frame = ctk.CTkFrame(pencere)
    frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    frame.grid_columnconfigure(0, weight=1)

    def label_ve_widget(label_text, widget, pady=(8, 3)):
        row = label_ve_widget.row
        ctk.CTkLabel(master=frame, text=label_text, anchor="w", font=("Segoe UI Black", 16)).grid(row=row, column=0, sticky="ew", pady=pady, padx=10)
        widget.grid(row=row + 1, column=0, sticky="ew", pady=(0, 5), padx=10)
        label_ve_widget.row += 2
    label_ve_widget.row = 0

    baslik_entry = ctk.CTkEntry(frame)
    baslik_entry.insert(0, baslik)
    label_ve_widget("Başlık", baslik_entry)

    aciklama_entry = ctk.CTkTextbox(frame, height=100)
    aciklama_entry.insert("1.0", aciklama)
    label_ve_widget("Açıklama", aciklama_entry)

    bitis_entry = ctk.CTkEntry(frame, placeholder_text="GG-AA-YYYY")
    bitis_entry.insert(0, bitis)
    bitis_entry.configure(state="readonly")
    bitis_entry.bind("<Button-1>", lambda e: takvim_ac(bitis_entry))
    label_ve_widget("Bitiş Tarihi", bitis_entry)

    oncelik_sec = ctk.CTkOptionMenu(frame, values=["Yüksek", "Orta", "Düşük"], fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12))
    oncelik_sec.set(oncelik.capitalize())
    label_ve_widget("Öncelik", oncelik_sec)

    durum_sec = ctk.CTkOptionMenu(frame, values=["Tamamlandı", "Tamamlanmadı"], fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12))
    durum_sec.set(durum.capitalize())
    label_ve_widget("Durum", durum_sec)

    kullanicilar = tum_kullanicilar()
    kullanici_adlari = [k[1] for k in kullanicilar]

    atanan_entry = ctk.CTkOptionMenu(master=frame, values=kullanici_adlari,  fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12))
    if atanan_kullanici_adi in kullanici_adlari:
        atanan_entry.set(atanan_kullanici_adi)
    else:
        atanan_entry.set(kullanici_adlari[0])
    label_ve_widget("Atanan Kullanıcı", atanan_entry)


    def kaydet():
        yeni_baslik = baslik_entry.get()
        yeni_aciklama = aciklama_entry.get("1.0", "end").strip()
        yeni_bitis = bitis_entry.get()
        yeni_oncelik = oncelik_sec.get().lower()
        yeni_durum = durum_sec.get().lower()
        yeni_atanan = atanan_entry.get()

        basarili = gorev_guncelle(id, yeni_baslik, yeni_aciklama, yeni_bitis, yeni_oncelik, yeni_durum, yeni_atanan)
        if basarili:
            messagebox.showinfo("Başarılı", "Görev güncellendi.")
            pencere.destroy()
            GorevleriListele()
        else:
            messagebox.showerror("Hata", "Görev güncellenemedi.")

    kaydet_btn = ctk.CTkButton(frame, text="Kaydet", command=kaydet)
    kaydet_btn.grid(row=label_ve_widget.row, column=0, sticky="ew", pady=(20, 0), padx=140)

def GorevleriDuzenle(sayfa=1, sayfa_basi=3, filtre_arama="", filtre_oncelik="tümü", filtre_durum="tümü"): # Görevleri düzenle listelenen bölüm
    global content_frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    ust_panel = ctk.CTkFrame(master=content_frame, fg_color="transparent")
    ust_panel.pack(fill="x", padx=20, pady=10)

    arama_entry = ctk.CTkEntry(master=ust_panel,fg_color="#374151", text_color="white", font=("Segoe UI Black", 12), placeholder_text="Görev Başlığı veya ID ara...", width=250)
    arama_entry.pack(side="left", padx=5)
    if filtre_arama:
        arama_entry.insert(0, filtre_arama)

    oncelik_menu = ctk.CTkOptionMenu(master=ust_panel, fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12), values=["Tümü", "Yüksek", "Orta", "Düşük"])
    oncelik_menu.pack(side="left", padx=5)
    oncelik_menu.set(filtre_oncelik.capitalize() if filtre_oncelik != "tümü" else "Öncelik")

    durum_menu = ctk.CTkOptionMenu(master=ust_panel, fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12), values=["Tümü", "Tamamlandı", "Tamamlanmadı"])
    durum_menu.pack(side="left", padx=5)
    durum_menu.set(filtre_durum.capitalize() if filtre_durum != "tümü" else "Durum")

    def filtre_uygula():
        arama = arama_entry.get().strip().lower()
        oncelik = oncelik_menu.get().lower()
        durum = durum_menu.get().lower()

        if oncelik == "öncelik":
            oncelik = "tümü"
        if durum == "durum":
            durum = "tümü"

        GorevleriDuzenle(1, sayfa_basi, filtre_arama=arama, filtre_oncelik=oncelik, filtre_durum=durum)

    ctk.CTkButton(master=ust_panel, text="Filtrele",fg_color="#374151", hover_color="#4B5563",text_color="white", font=("Segoe UI Black", 12), command=filtre_uygula).pack(side="left", padx=10)

    gorevler = gorevleri_getir(sayfa, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)

    if not gorevler:
        ctk.CTkLabel(master=content_frame, text="Hiç görev bulunamadı.", font=("Segoe UI", 12)).pack(pady=20)
        return

    for gorev in gorevler:
        id, kullanici_id, kullanici_adi, baslik, aciklama, olusturma, bitis, oncelik, durum, atanan_kullanici_adi = gorev

        kart = ctk.CTkFrame(master=content_frame, fg_color="#2e2e2e", corner_radius=10)
        kart.pack(fill="x", expand=True, padx=10, pady=5)
        kart_hover_efekti(kart)


        üst_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        üst_satir.pack(fill="x", padx=10, pady=(6, 0))

        ctk.CTkLabel(master=üst_satir, text=f"ID: {id}", font=("Segoe UI", 12, "bold")).pack(side="left")
        ctk.CTkLabel(master=üst_satir, text=baslik, text_color="#e11d48", font=("Segoe UI", 20, "bold")).pack(side="left", expand=True)

        duzenle_buton = ctk.CTkButton(
            master=üst_satir,
            text="Düzenle",
            width=40,
            fg_color="#F59E0B",
            hover_color="#FBBF24",
            text_color="black",
            font=("Segoe UI", 11, "bold"),
            command=lambda g=gorev: gorev_duzenle_penceresi(g),
        )
        duzenle_buton.pack(side="right") 
        duzenle_buton.bind("<Button-1>", lambda e: "break") #Burada ki fonksiyonda kart içerisinde düzenle tıklarsak otomatik detay açıyordu bu şekilde fixledim


        tarih_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        tarih_satir.pack(fill="x", padx=10, pady=(2, 0))
        ctk.CTkLabel(master=tarih_satir, text=f"Oluşturma: {olusturma}", font=("Segoe UI", 12)).pack(side="left")
        ctk.CTkLabel(master=tarih_satir, text=f"Bitiş: {bitis}", font=("Segoe UI", 12)).pack(side="right")

        kisi_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        kisi_satir.pack(fill="x", padx=10, pady=(1, 0))
        ctk.CTkLabel(master=kisi_satir, text=f"Oluşturan: {kullanici_adi}", font=("Segoe UI", 12)).pack(side="left")
        ctk.CTkLabel(master=kisi_satir, text=f"Atanan: {atanan_kullanici_adi}", font=("Segoe UI", 12)).pack(side="right")

        detay_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        detay_satir.pack(fill="x", padx=10, pady=(1, 2))

        oncelik_rengi = {
            "yüksek": "#dc2626",
            "orta": "#8b5cf6",
            "düşük": "#6b7280"
        }.get(oncelik.lower(), "#9ca3af")

        durum_rengi = "#3b82f6" if durum.lower() == "tamamlandı" else "#f97316"

        ctk.CTkLabel(
            master=detay_satir,
            text=f"Öncelik: {oncelik.capitalize()}",
            font=("Segoe UI", 12, "bold"),
            text_color=oncelik_rengi,
            fg_color="transparent"
        ).pack(side="left", padx=(0, 5))

        ctk.CTkLabel(
            master=detay_satir,
            text=f"Durum: {durum.capitalize()}",
            font=("Segoe UI", 12, "bold"),
            text_color=durum_rengi,
            fg_color="transparent"
        ).pack(side="left")

        aciklama_duz = aciklama.replace("\n", " ").replace("\t", " ")
        max_karakter = 120
        kisa_aciklama = aciklama_duz[:max_karakter - 3] + "..." if len(aciklama_duz) > max_karakter else aciklama_duz

        # Açıklama Başlığı
        ctk.CTkLabel(
            master=kart,
            text="Açıklama:",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
            justify="left"
        ).pack(fill="x", padx=10, pady=(0, 2))  # 2px alt boşluk

        # Açıklama Detayı
        ctk.CTkLabel(
            master=kart,
            text=kisa_aciklama,
            font=("Segoe UI", 11),
            anchor="w",
            justify="left",
            wraplength=700
        ).pack(fill="x", padx=10, pady=(0, 4))  # Alt boşluğu da azalttım

        kart.bind("<Button-1>", lambda e, g=gorev: gorev_detay_goster(g))

        for child in kart.winfo_children():
            child.bind("<Button-1>", lambda e, g=gorev: gorev_detay_goster(g))
            # Eğer child içinde alt frame'ler varsa onların çocuklarına da:
            for sub in child.winfo_children():
                sub.bind("<Button-1>", lambda e, g=gorev: gorev_detay_goster(g))

    butonlar = ctk.CTkFrame(master=content_frame)
    butonlar.pack(pady=10)

    def ileri():
        sonraki_gorevler = gorevleri_getir(sayfa + 1, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)
        if sonraki_gorevler:  
            GorevleriDuzenle(sayfa + 1, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)

    def geri():
        if sayfa > 1:
            GorevleriDuzenle(sayfa - 1, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)

    ctk.CTkButton(master=butonlar, text="Geri", fg_color="#4B5563", hover_color="#6B7280", text_color="white", font=("Segoe UI Black", 12),command=geri).pack(side="left", padx=10)
    ctk.CTkButton(master=butonlar, text="İleri", fg_color="#4B5563", hover_color="#6B7280", text_color="white", font=("Segoe UI Black", 12), command=ileri).pack(side="right", padx=10)

def GorevleriSil(sayfa=1, sayfa_basi=3, filtre_arama="", filtre_oncelik="tümü", filtre_durum="tümü"): # Görevleri Sil listelenen bölüm
    global content_frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    ust_panel = ctk.CTkFrame(master=content_frame, fg_color="transparent")
    ust_panel.pack(fill="x", padx=20, pady=10)

    arama_entry = ctk.CTkEntry(master=ust_panel,fg_color="#374151", text_color="white", font=("Segoe UI Black", 12), placeholder_text="Görev Başlığı veya ID ara...", width=250)
    arama_entry.pack(side="left", padx=5)
    if filtre_arama:
        arama_entry.insert(0, filtre_arama)

    oncelik_menu = ctk.CTkOptionMenu(master=ust_panel, fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12), values=["Tümü", "Yüksek", "Orta", "Düşük"])
    oncelik_menu.pack(side="left", padx=5)
    oncelik_menu.set(filtre_oncelik.capitalize() if filtre_oncelik != "tümü" else "Öncelik")

    durum_menu = ctk.CTkOptionMenu(master=ust_panel, fg_color="#374151", button_color="#1F2937", button_hover_color="#4B5563", text_color="white", font=("Segoe UI Black", 12), values=["Tümü", "Tamamlandı", "Tamamlanmadı"])
    durum_menu.pack(side="left", padx=5)
    durum_menu.set(filtre_durum.capitalize() if filtre_durum != "tümü" else "Durum")

    def filtre_uygula():
        arama = arama_entry.get().strip().lower()
        oncelik = oncelik_menu.get().lower()
        durum = durum_menu.get().lower()

        if oncelik == "öncelik":
            oncelik = "tümü"
        if durum == "durum":
            durum = "tümü"

        GorevleriSil(1, sayfa_basi, filtre_arama=arama, filtre_oncelik=oncelik, filtre_durum=durum)

    ctk.CTkButton(master=ust_panel, text="Filtrele",fg_color="#374151", hover_color="#4B5563",text_color="white", font=("Segoe UI Black", 12), command=filtre_uygula).pack(side="left", padx=10)

    gorevler = gorevleri_getir(sayfa, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)

    if not gorevler:
        ctk.CTkLabel(master=content_frame, text="Hiç görev bulunamadı.", font=("Segoe UI", 12)).pack(pady=20)
        return

    for gorev in gorevler:
        id, kullanici_id, kullanici_adi, baslik, aciklama, olusturma, bitis, oncelik, durum, atanan_kullanici_adi = gorev

        kart = ctk.CTkFrame(master=content_frame, fg_color="#2e2e2e", corner_radius=10)
        kart.pack(fill="x", expand=True, padx=10, pady=5)
        kart_hover_efekti(kart)


        üst_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        üst_satir.pack(fill="x", padx=10, pady=(6, 0))

        ctk.CTkLabel(master=üst_satir, text=f"ID: {id}", font=("Segoe UI", 12, "bold")).pack(side="left")
        ctk.CTkLabel(master=üst_satir, text=baslik, text_color="#e11d48", font=("Segoe UI", 20, "bold")).pack(side="left", expand=True)

        sil_buton = ctk.CTkButton(
            master=üst_satir,
            text="Sil",
            width=40,
            fg_color="#ef4444",
            hover_color="#dc2626",
            text_color="black",
            font=("Segoe UI", 11, "bold"),
            command=lambda gid=id: gorev_sil(gid),
        )
        sil_buton.pack(side="right")
        sil_buton.bind("<Button-1>", lambda e: "break")

        tarih_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        tarih_satir.pack(fill="x", padx=10, pady=(2, 0))
        ctk.CTkLabel(master=tarih_satir, text=f"Oluşturma: {olusturma}", font=("Segoe UI", 12)).pack(side="left")
        ctk.CTkLabel(master=tarih_satir, text=f"Bitiş: {bitis}", font=("Segoe UI", 12)).pack(side="right")

        kisi_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        kisi_satir.pack(fill="x", padx=10, pady=(1, 0))
        ctk.CTkLabel(master=kisi_satir, text=f"Oluşturan: {kullanici_adi}", font=("Segoe UI", 12)).pack(side="left")
        ctk.CTkLabel(master=kisi_satir, text=f"Atanan: {atanan_kullanici_adi}", font=("Segoe UI", 12)).pack(side="right")

        detay_satir = ctk.CTkFrame(master=kart, fg_color="transparent")
        detay_satir.pack(fill="x", padx=10, pady=(1, 2))

        oncelik_rengi = {
            "yüksek": "#dc2626",
            "orta": "#8b5cf6",
            "düşük": "#6b7280"
        }.get(oncelik.lower(), "#9ca3af")

        durum_rengi = "#3b82f6" if durum.lower() == "tamamlandı" else "#f97316"

        ctk.CTkLabel(
            master=detay_satir,
            text=f"Öncelik: {oncelik.capitalize()}",
            font=("Segoe UI", 12, "bold"),
            text_color=oncelik_rengi,
            fg_color="transparent"
        ).pack(side="left", padx=(0, 5))

        ctk.CTkLabel(
            master=detay_satir,
            text=f"Durum: {durum.capitalize()}",
            font=("Segoe UI", 12, "bold"),
            text_color=durum_rengi,
            fg_color="transparent"
        ).pack(side="left")

        aciklama_duz = aciklama.replace("\n", " ").replace("\t", " ")
        max_karakter = 120
        kisa_aciklama = aciklama_duz[:max_karakter - 3] + "..." if len(aciklama_duz) > max_karakter else aciklama_duz

        # Açıklama Başlığı
        ctk.CTkLabel(
            master=kart,
            text="Açıklama:",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
            justify="left"
        ).pack(fill="x", padx=10, pady=(0, 2))  # 2px alt boşluk

        # Açıklama Detayı
        ctk.CTkLabel(
            master=kart,
            text=kisa_aciklama,
            font=("Segoe UI", 11),
            anchor="w",
            justify="left",
            wraplength=700
        ).pack(fill="x", padx=10, pady=(0, 4))  # Alt boşluğu da azalttım

        kart.bind("<Button-1>", lambda e, g=gorev: gorev_detay_goster(g))

        for child in kart.winfo_children():
            child.bind("<Button-1>", lambda e, g=gorev: gorev_detay_goster(g))
            # Eğer child içinde alt frame'ler varsa onların çocuklarına da:
            for sub in child.winfo_children():
                sub.bind("<Button-1>", lambda e, g=gorev: gorev_detay_goster(g))

    butonlar = ctk.CTkFrame(master=content_frame)
    butonlar.pack(pady=10)

    def ileri():
        sonraki_gorevler = gorevleri_getir(sayfa + 1, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)
        if sonraki_gorevler:  
            GorevleriListele(sayfa + 1, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)

    def geri():
        if sayfa > 1:
            GorevleriListele(sayfa - 1, sayfa_basi, filtre_arama, filtre_oncelik, filtre_durum)

    ctk.CTkButton(master=butonlar, text="Geri", fg_color="#4B5563", hover_color="#6B7280", text_color="white", font=("Segoe UI Black", 12),command=geri).pack(side="left", padx=10)
    ctk.CTkButton(master=butonlar, text="İleri", fg_color="#4B5563", hover_color="#6B7280", text_color="white", font=("Segoe UI Black", 12), command=ileri).pack(side="right", padx=10)

def gorev_detay_goster(gorev): # Görevin üstüne tıkladığında detay oluşturulan bölüm
    detay_pencere = ctk.CTkToplevel()
    detay_pencere.iconbitmap(resource_path("image/favicon.ico"))
    detay_pencere.title(f"Görev Detayı - ID {gorev[0]}")
    detay_pencere.geometry("600x600")
    detay_pencere.minsize(500, 500)
    detay_pencere.lift()
    detay_pencere.focus_force()
    detay_pencere.attributes("-topmost", True)
    detay_pencere.after(300, lambda: detay_pencere.attributes("-topmost", False))
    detay_pencere.after(250, lambda: detay_pencere.iconbitmap(resource_path("image/favicon.ico"))) # Bunun için githubda baya dolaşmam gerekti açıkçası popup icon sorunlu o yüzden 250ms sonra ekliyorum

    scroll_frame = ctk.CTkScrollableFrame(detay_pencere)
    scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

    id, kullanici_id, kullanici_adi, baslik, aciklama, olusturma, bitis, oncelik, durum, atanan_kullanici_adi = gorev

    oncelik_rengi = {
        "yüksek": "#dc2626",
        "orta": "#8b5cf6",
        "düşük": "#6b7280"
    }.get(oncelik.lower(), "#9ca3af")

    durum_rengi = "#3b82f6" if durum.lower() == "tamamlandı" else "#f97316"

    def bilgi_karti(baslik, icerik, renk="white", kutu_yukseklik=40, is_textbox=False):
        frame = ctk.CTkFrame(scroll_frame, fg_color="#1f1f1f", corner_radius=8)
        frame.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(frame, text=baslik, font=("Segoe UI Black", 13), text_color="#e5e5e5", anchor="w").pack(anchor="w", padx=10, pady=(8, 0))
        
        if is_textbox:
            textbox = ctk.CTkTextbox(frame, height=kutu_yukseklik, font=("Segoe UI", 11), wrap="word", fg_color="#2e2e2e", text_color=renk)
            textbox.insert("1.0", icerik)
            textbox.configure(state="disabled")
            textbox.pack(fill="x", expand=True, padx=10, pady=(5, 10))
        else:
            ctk.CTkLabel(frame, text=icerik, font=("Segoe UI", 11), text_color=renk, anchor="w").pack(anchor="w", padx=10, pady=(5, 10))

    # Başlık özel stil
    baslik_kutusu = ctk.CTkFrame(scroll_frame, fg_color="#1f1f1f", corner_radius=8)
    baslik_kutusu.pack(fill="x", padx=10, pady=10)
    ctk.CTkLabel(baslik_kutusu, text="Başlık", font=("Segoe UI Black", 13), text_color="#e5e5e5", anchor="w").pack(anchor="w", padx=10, pady=(8, 0))
    ctk.CTkLabel(baslik_kutusu, text=baslik, font=("Segoe UI Black", 18), text_color="#e11d48", anchor="w").pack(anchor="w", padx=10, pady=(4, 10))

    bilgi_karti("Açıklama", aciklama, is_textbox=True, kutu_yukseklik=130)
    bilgi_karti("Oluşturan", kullanici_adi, "#cfcfcf")
    bilgi_karti("Atanan", atanan_kullanici_adi, "#cfcfcf")
    bilgi_karti("Oluşturma Tarihi", olusturma, "#cfcfcf")
    bilgi_karti("Bitiş Tarihi", bitis, "#cfcfcf")
    bilgi_karti("Öncelik", oncelik.capitalize(), oncelik_rengi)
    bilgi_karti("Durum", durum.capitalize(), durum_rengi)

giris_ekrani()

