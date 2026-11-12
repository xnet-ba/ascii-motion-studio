<!-- xnet-ba-matrix-header-v1 -->
<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=00FF41&height=140&section=header&text=ascii-motion-studio&fontColor=000000&fontSize=32&fontAlignY=32&desc=ASCII%20Motion%20Studio%20-%20Professional%20ASCII%20Image%2C%20Video%20and%20An&descAlignY=55" width="100%" alt="ascii-motion-studio"/>

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=16&duration=2800&pause=800&color=00FF41&center=true&vCenter=true&width=700&lines=xnet-ba+%3A%3A+open-source+AI+iz+BiH;citaj+README+pa+pokreni;PR+dobrodosli)](https://github.com/xnet-ba/ascii-motion-studio)

[![Stars](https://img.shields.io/github/stars/xnet-ba/ascii-motion-studio?style=flat-square&color=00FF41&labelColor=000000)](https://github.com/xnet-ba/ascii-motion-studio/stargazers)
[![License](https://img.shields.io/github/license/xnet-ba/ascii-motion-studio?style=flat-square&color=00FF41&labelColor=000000)](LICENSE)
[![Top lang](https://img.shields.io/github/languages/top/xnet-ba/ascii-motion-studio?style=flat-square&color=00FF41&labelColor=000000)](https://github.com/xnet-ba/ascii-motion-studio)
[![Last commit](https://img.shields.io/github/last-commit/xnet-ba/ascii-motion-studio?style=flat-square&color=00FF41&labelColor=000000)](https://github.com/xnet-ba/ascii-motion-studio/commits)
[![matrix](https://img.shields.io/badge/MATRIX-xnet--ba-00FF41?style=flat-square&labelColor=000000)](https://github.com/xnet-ba)

</div>

---
# ASCII Motion Studio

Professional ASCII Image, Video and Animation Generator.

- **GitHub:** https://github.com/xnet-ba/ascii-motion-studio
- **Demo:** https://go.kolektiv.pro

> Jezik korisničkog interfejsa: bosanski (ijekavica). Arhitektura podržava buduće višejezične interfejse putem `react-i18next`.

## Funkcije

- Pretvaranje slika (PNG, JPG, WebP, BMP, GIF, SVG) u ASCII grafiku.
- Pretvaranje videozapisa (MP4, MOV, WebM, AVI) i GIF animacija u ASCII animacije.
- Izlazni formati: PNG, GIF, SVG, TXT, HTML, MP4, WebM.
- Samostalna HTML/Canvas animacija bez server-side renderovanja.
- Više režima: grayscale, color, monochrome.
- Prilagođene ASCII palete i vlastiti skupovi znakova.
- Podešavanje kontrasta, svjetline, gama-korekcije, zasićenja, oštrenja.
- Contrast-aware rendering za logotipe.
- Project management (SQLite).
- Background job queue (SQLite + worker).
- REST API sa OpenAPI dokumentacijom.
- Autentifikacija putem Bearer tokena.
- Systemd servisi sa automatskim restartom.

## Arhitektura

```
ascii-motion-studio/
├── frontend/          React + TypeScript + Vite + Tailwind CSS
├── backend/           FastAPI + Pillow + NumPy + FFmpeg
│   ├── api/           REST endpointi
│   ├── core/          Config i sigurnost
│   ├── engines/       Image, video, ASCII, GIF, export
│   ├── workers/       Background worker
│   └── storage/       SQLite + filesystem
├── deployment/        Systemd unit fajlovi
└── docs/              Dodata dokumentacija
```

## Zahtjevi

- Ubuntu 22.04/24.04
- Python 3.11+
- Node.js 20+
- FFmpeg + FFprobe
- ImageMagick
- HestiaCP + Nginx (za deployment na K.PRO serveru)

## Brza instalacija

```bash
git clone https://github.com/xnet-ba/ascii-motion-studio.git /opt/ascii-motion-studio
cd /opt/ascii-motion-studio/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd /opt/ascii-motion-studio/frontend
npm install
npm run build

# Direktoriji za podatke
sudo mkdir -p /var/lib/ascii-motion-studio/{uploads,exports} \
             /var/log/ascii-motion-studio \
             /var/tmp/ascii-motion-studio/jobs
sudo chown -R $USER:$USER /var/lib/ascii-motion-studio \
                          /var/log/ascii-motion-studio \
                          /var/tmp/ascii-motion-studio

# Systemd
sudo cp deployment/ascii-motion-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ascii-motion-api ascii-motion-worker
```

## Konfiguracija

Kopiraj `backend/.env.example` u `backend/.env` i prilagodi:

```env
APP_URL=https://go.kolektiv.pro
API_TOKEN=tvoj-jaki-token
SECRET_KEY=tvoj-jaki-secret
MAX_UPLOAD_SIZE_MB=50
MAX_VIDEO_DURATION_SECONDS=20
CONCURRENT_JOBS=2
```

## API dokumentacija

Nakon pokretanja backend-a dostupna je na:

- OpenAPI JSON: `/api/v1/openapi.json`
- Swagger UI: `/docs`
- Redoc: `/redoc`

### Primjer poziva

```bash
curl -X POST https://go.kolektiv.pro/api/v1/upload \
  -H "Authorization: Bearer $API_TOKEN" \
  -F "file=@slika.png"

curl -X POST https://go.kolektiv.pro/api/v1/image/convert \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"input_path":"/var/lib/ascii-motion-studio/uploads/.../slika.png",
       "width":120,"mode":"color","background":"black","output_format":"png"}'

curl https://go.kolektiv.pro/api/v1/jobs/1 \
  -H "Authorization: Bearer $API_TOKEN"
```

## HestiaCP deployment

1. Kreiraj domenu `go.kolektiv.pro` u HestiaCP.
2. Postavi nginx proxy template `ascii-motion`.
3. Omogući SSL (Let's Encrypt).
4. Build-ani frontend kopiraj u `/home/admin/web/go.kolektiv.pro/public_html`.
5. `/api/` i `/exports/` se automatski proslijeđuju na backend port 8001.

## Sigurnost

- API je zaštićen Bearer tokenom.
- Upload-ovane datoteke se provjeravaju magic-byte-ovima.
- Ograničena veličina datoteka, trajanje videa, dimenzije i broj kadrova.
- FFmpeg se pokreće kao neprivilegovani korisnik.
- Privremeni fajlovi se čuvaju u `/var/tmp/ascii-motion-studio`.
- Path-traversal zaštita na imenima datoteka.

## Backup i restore

Baza i korisnički fajlovi:

```bash
sudo tar czf /var/backups/ascii-motion-$(date +%Y%m%d).tar.gz \
  /var/lib/ascii-motion-studio /opt/ascii-motion-studio/backend/.env
```

Restore:

```bash
sudo tar xzf /var/backups/ascii-motion-YYYYMMDD.tar.gz -C /
sudo systemctl restart ascii-motion-api ascii-motion-worker
```

## License

MIT License. Tehnička inspiracija: [Ghostty](https://ghostty.org/) / [ghostty-org/website](https://github.com/ghostty-org/website).

---

<div align="center">
<img src="https://raw.githubusercontent.com/xnet-ba/xnet-ba/main/assets/divider.svg" width="100%" alt=""/>
<sup>part of <a href="https://github.com/xnet-ba">xnet-ba matrix</a> — open-source AI iz BiH</sup>
</div>
