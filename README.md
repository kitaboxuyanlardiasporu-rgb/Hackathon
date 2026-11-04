# Qiymətləndirmə portalı

Bu portalda müsabiqə komandalarını jürilər qiymətləndirir. Portal iki rolla işləyir: admin və jüri.
Texniki baza: **FastAPI** (backend), **PostgreSQL** (verilənlər bazası) və asılılığı olmayan veb interfeys.

## Nə hazırdır

- **Operatorlar:** admin **Operatorlar** bölməsində operator yaradır və ona icazələr verir: müsabiqə yaratmaq və ayarlamaq, jüri əlavə etmək, komandaları müəyyənləşdirmək, meyarları müəyyənləşdirmək, qiymətləndirməni açıb-bağlamaq, müsabiqə məlumatlarını sıfırlamaq. Operator özünün yaratdığı müsabiqələri və admin tərəfindən **giriş verilmiş** müsabiqələri görür. Admin hər operatora istənilən müsabiqəyə **yalnız baxış** (dəyişiklik olmadan) və ya **idarə** (operatorun icazələri daxilində) girişi verə bilər; bu, Operatorlar bölməsindəki "Müsabiqələrə giriş" düyməsi ilə edilir. Müsabiqəni silmək, balları redaktə etmək, nəticələr, tarixçə və operatorların idarəsi yalnız admindədir. İcazələr hər sorğuda serverdə yoxlanılır.
- **Sıfırlama:** müsabiqənin bütün balları silinir (istəyə görə jürilər, komandalar və meyarlar da), struktur kilidi açılır. Adı yazmaqla təsdiqlənir, silinən ballar tarixçədə qalır.
- **Jüri ekranı:** hər komanda kartında komandanın altında meyarlar, hər meyar üçün açılan siyahı.
- **Bir neçə müsabiqə:** admin **Müsabiqələr** bölməsində yeni müsabiqə yaradır, yan menyudakı seçici ilə müsabiqələr arasında keçir və köhnə müsabiqəni həmişəlik silir. Silmədən əvvəl müsabiqənin adı yazılaraq təsdiqlənir və nəticələri CSV kimi yükləmək təklif olunur. Sonuncu müsabiqəni də silmək olar; o zaman admin yeni müsabiqə yaradır.
- **Qiymətləndirməni açmaq və bağlamaq:** hər müsabiqə üçün ayrıca idarə olunur və bir neçə müsabiqə eyni vaxtda açıq ola bilər. Bağlı müsabiqədə jüri yeni bal təsdiqləyə bilmir, amma təsdiqlənmiş balları saxlanılır. Yeni müsabiqə bağlı vəziyyətdə yaradılır.
- **Jürilər:** hər müsabiqənin öz jüri hesabları var. İstifadəçi adı bütün portal üzrə unikaldır. Müsabiqə silinəndə onun jüri hesabları da silinir. Təsdiqlənmiş balı olan jürini də silmək olar: istifadəçi adını yazıb təsdiqləyəndə hesab balları ilə birlikdə silinir, silinən ballar isə tarixçədə saxlanılır.

- **Giriş:** admin və jüri eyni səhifədən daxil olur. Sessiya HttpOnly cookie ilə saxlanılır. Parollar scrypt ilə, duzlanmış heş kimi saxlanılır. Uğursuz giriş cəhdləri limitlənir.
- **Qiymətləndirmə tipləri:**
  - Unikal bal (1–N, təkrarsız). Bu qayda verilənlər bazasında unikal indekslə də qorunur.
  - Şkala (1–5).
  - Fərdi şkala (1–n, burada n = 2–100).
- **Admin paneli:** İcmal, Müsabiqə ayarları, Komandalar, Meyarlar, Jürilər, Qiymətləndirmələr (redaktə və kilid açma), Nəticələr (CSV ixracı ilə), Tarixçə və parol dəyişmə.
- **Jüri paneli:** komanda kartları, tipə uyğun bal seçimi, təsdiq pəncərəsi, kilidləmə və irəliləyiş göstəricisi.
- **Paralel sorğular:** bütün yazma əməliyyatları serverdə ardıcıllaşdırılır. Admin redaktələrində versiya yoxlaması aparılır.
- **İlk dəfə işə düşəndə:** 10 nümunə komanda (Komanda 01–10) və 5 meyar yaradılır. Əvvəlki məlumatlar heç vaxt silinmir.

## 1-ci variant: Render-də yayım (ən asan yol, kod tələb etmir)

1. github.com saytında yeni **private** repo yaradın və bu qovluğun bütün fayllarını ora yükləyin ("Add file → Upload files").
2. render.com saytına daxil olun və **New → Blueprint** seçin. Sonra həmin reponu seçin.
3. Render `render.yaml` faylını oxuyub veb xidməti və PostgreSQL bazasını özü yaradacaq. O, iki dəyər soruşacaq:
   - `ADMIN_USERNAME` — admin istifadəçi adı (məsələn, `admin`);
   - `ADMIN_PASSWORD` — güclü parol (ən azı 8 simvol, tövsiyə: 14+).
4. Yayım bitdikdən sonra Render sizə `https://qiymetlendirme-portali-xxxx.onrender.com` kimi bir link verəcək. Bu, portalın giriş linkidir.
5. İlk girişdən sonra Render-də `ADMIN_PASSWORD` dəyərini silə bilərsiniz. Admin artıq bazada saxlanılır, bu dəyişənlər bir daha istifadə olunmur.

> Planı (pulsuz və ya ödənişli) Render yaradılış zamanı göstərəcək. Real müsabiqə üçün bazanı ödənişli planda saxlamaq tövsiyə olunur, çünki pulsuz bazalar müvəqqətidir.

## 2-ci variant: öz serverinizdə (Docker)

```bash
cp .env.example .env        # sonra .env faylındakı parolları dəyişin
docker compose up -d --build
```

Portal `http://SERVER:8000` ünvanında açılacaq. İnternetə açarkən onu **HTTPS** arxasında yerləşdirin. Ən sadə yol Caddy-dir; `Caddyfile` faylının nümunəsi:

```
qiymetlendirme.sizin-domen.az {
    reverse_proxy 127.0.0.1:8000
}
```

## İlkin admin hesabı

Admin hesabını yalnız sayt sahibi yarada bilər. Portalda admin qeydiyyatı üçün heç bir səhifə yoxdur. İki yol var:

- **Mühit dəyişənləri:** `ADMIN_USERNAME` və `ADMIN_PASSWORD`. Bu dəyərlər yalnız bazada **heç bir admin olmadıqda** istifadə olunur.
- **Serverdə əmr:**
  ```bash
  docker compose exec web python -m app.cli create-admin --username admin
  docker compose exec web python -m app.cli reset-admin-password --username admin   # unudulmuş parol
  ```

Jüri hesablarını yalnız admin yaradır: **Jürilər** bölməsindən.

## Ehtiyat nüsxə

```bash
docker compose exec db pg_dump -U portal portal > ehtiyat-$(date +%F).sql
```

Render-də isə: **Database → Backups**.

## Yeniləmə

Yeniləmədən əvvəl həmişə nəticələri CSV kimi yükləyin; Render-in ödənişli planındasınızsa, bazanın ehtiyat nüsxəsini də çıxarın.

Kodu yeniləyib yenidən yayımlamaq kifayətdir (`docker compose up -d --build` və ya Render-də avtomatik yayım). Yeni sütunlar avtomatik əlavə olunur. Mövcud hesablar, ballar və ayarlar saxlanılır. Qiymətləndirmə tipi qeyd olunmamış köhnə müsabiqələr "Unikal bal" kimi qəbul edilir. Tək müsabiqəli köhnə versiyadan keçəndə bütün komanda, meyar, jüri və ballar birinci müsabiqəyə bağlanır və o müsabiqə açıq qalır.

> GitHub-a brauzerdən yükləyəndə qovluqlar itə və bütün fayllar reponun kökünə düşə bilər. Dockerfile bunu nəzərə alır: `app/` qovluğu yoxdursa, quruluşu yayım zamanı özü bərpa edir.

## Testlər (tərtibatçılar üçün)

```bash
pip install -r requirements-dev.txt
DATABASE_URL=postgresql://USER:PASS@localhost/portal_test pytest -q
```

49 avtomatik test aşağıdakıları yoxlayır: hər üç tipin qaydaları, kilidlər, rollar, nəticələrin hesablanması, bərabər balların sıralanması, CSV ixracı, paralel sorğular, miqrasiya, müsabiqələrin bir-birindən ayrılığı, qiymətləndirmənin açılıb-bağlanması və müsabiqənin silinməsi, operator icazələri, müsabiqəyə giriş və sıfırlama.

## Mühit dəyişənləri

| Dəyişən | Təyinat | Standart |
|---|---|---|
| `DATABASE_URL` | PostgreSQL ünvanı | — |
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | İlkin admin (yalnız admin yoxdursa) | boş |
| `COOKIE_SECURE` | `auto` / `1` / `0` | `auto` |
| `SESSION_HOURS` | Sessiyanın müddəti (aktivlikdə uzanır) | `12` |
| `SEED_DEFAULTS` | Boş bazada nümunə komanda və meyarlar | `1` |
