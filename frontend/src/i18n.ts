import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

const resources = {
  bs: {
    translation: {
      appName: 'ASCII Motion Studio',
      upload: 'Učitaj datoteku',
      imageToAscii: 'Slika u ASCII',
      videoToAscii: 'Video u ASCII',
      animation: 'Animacija',
      projects: 'Projekti',
      jobs: 'Poslovi',
      settings: 'Postavke',
      width: 'Širina (znakova)',
      mode: 'Režim',
      palette: 'Paleta',
      background: 'Pozadina',
      contrastAdapt: 'Automatska prilagodba kontrasta',
      convert: 'Pretvori',
      processing: 'Obrada u toku...',
      download: 'Preuzmi',
      preview: 'Pregled',
      grayscale: 'Nijanse sive',
      color: 'Boja',
      monochrome: 'Monohromatski',
      black: 'Crna',
      white: 'Bijela',
      transparent: 'Prozirna',
      standard: 'Standard',
      dense: 'Gusta',
      minimal: 'Minimal',
      blocks: 'Blokovi',
      binary: 'Binarna',
      custom: 'Prilagođena',
      fps: 'Kadrova u sekundi',
      duration: 'Maksimalno trajanje (s)',
      outputFormat: 'Izlazni format',
      png: 'PNG',
      gif: 'GIF',
      mp4: 'MP4',
      webm: 'WebM',
      html: 'HTML',
      txt: 'TXT',
      svg: 'SVG',
    }
  }
};

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'bs',
    interpolation: { escapeValue: false },
  });

export default i18n;
