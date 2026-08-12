import { ref, watch } from 'vue'
import en from './locales/en.json'
import it from './locales/it.json'
import es from './locales/es.json'
import de from './locales/de.json'
import fr from './locales/fr.json'

const translations: Record<string, any> = {
  en,
  it,
  es,
  de,
  fr
}

const getBrowserLocale = () => {
  const lang = navigator.language.split('-')[0]
  if (['en', 'it', 'es', 'de', 'fr'].includes(lang)) {
    return lang
  }
  return 'en'
}

const initialLocale = localStorage.getItem('language') || getBrowserLocale()
export const currentLocale = ref(initialLocale)

watch(currentLocale, (newLocale) => {
  localStorage.setItem('language', newLocale)
})

export const setLanguage = (lang: string) => {
  if (['en', 'it', 'es', 'de', 'fr'].includes(lang)) {
    currentLocale.value = lang
  }
}

export const t = (key: string): string => {
  // We access currentLocale.value to make this function reactive
  // when used inside Vue templates.
  const locale = currentLocale.value
  const keys = key.split('.')
  
  let value: any = translations[locale]
  for (const k of keys) {
    if (value && typeof value === 'object') {
      value = value[k]
    } else {
      value = undefined
      break
    }
  }
  
  if (value === undefined) {
    // Fallback to english if not found
    let fallbackValue: any = translations['en']
    for (const k of keys) {
      if (fallbackValue && typeof fallbackValue === 'object') {
        fallbackValue = fallbackValue[k]
      } else {
        fallbackValue = undefined
        break
      }
    }
    return fallbackValue !== undefined ? fallbackValue : key
  }
  
  return value
}
