'use client'

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import pt from '../locales/pt.json';

const LOCALE_LOADERS: Record<string, () => Promise<{ default: any }>> = {
  en: () => import('../locales/en.json'),
  fr: () => import('../locales/fr.json'),
  de: () => import('../locales/de.json'),
  es: () => import('../locales/es.json'),
  ar: () => import('../locales/ar.json'),
  ja: () => import('../locales/ja.json'),
  ru: () => import('../locales/ru.json'),
  zh: () => import('../locales/zh.json'),
  hi: () => import('../locales/hi.json'),
  ko: () => import('../locales/ko.json'),
  it: () => import('../locales/it.json'),
  tr: () => import('../locales/tr.json'),
  vi: () => import('../locales/vi.json'),
  id: () => import('../locales/id.json'),
  pl: () => import('../locales/pl.json'),
  uk: () => import('../locales/uk.json'),
  nl: () => import('../locales/nl.json'),
  th: () => import('../locales/th.json'),
  bn: () => import('../locales/bn.json'),
  fa: () => import('../locales/fa.json'),
  sk: () => import('../locales/sk.json'),
};

// Funeral Academy ships in Brazilian Portuguese: bundle pt, lazy-load the rest.
const resources = {
  pt: { common: pt },
};

async function loadLocale(lng: string) {
  const code = lng.split('-')[0]
  if (code === 'pt' || !LOCALE_LOADERS[code]) return;
  if (i18n.hasResourceBundle(code, 'common')) return;

  try {
    const mod = await LOCALE_LOADERS[code]();
    i18n.addResourceBundle(code, 'common', mod.default, true, true);
  } catch (e) {
    console.warn(`Failed to load locale: ${lng}`, e);
  }
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'pt',
    ns: ['common'],
    defaultNS: 'common',
    interpolation: {
      escapeValue: false, // react already safes from xss
    },
    detection: {
      // 'navigator' is intentionally omitted: the audience is Brazilian, so a
      // foreign browser locale should not override pt — only an explicit
      // in-app switch (persisted to localStorage/cookie) or ?lng= does.
      order: ['localStorage', 'cookie', 'querystring', 'path', 'subdomain'],
      caches: ['localStorage', 'cookie'],
      lookupLocalStorage: 'i18nextLng',
      lookupCookie: 'i18next',
    },
    react: {
      useSuspense: false,
    }
  });

// Load the detected language if it's not English — export the promise
// so I18nProvider can wait for resources before rendering
export const initialLocaleReady = loadLocale(i18n.language.split('-')[0]);

/**
 * Switch language safely — preloads the bundle before switching
 * so the UI never flashes Portuguese as a fallback.
 */
export async function changeLanguage(lng: string) {
  await loadLocale(lng)
  return i18n.changeLanguage(lng)
}

export default i18n;
