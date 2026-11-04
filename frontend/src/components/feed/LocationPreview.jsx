import { ExternalLink, MapPin } from 'lucide-react'
import { useT } from '../../i18n/LangContext.jsx'

/** Opens the spot in OpenStreetMap (nothing is sent to OpenStreetMap until someone clicks). */
export const mapLink = ({ lat, lng }) => `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=17/${lat}/${lng}`

const embedSrc = ({ lat, lng }) => {
  const d = 0.003   // about 330 m each way
  const f = (n) => Number(n).toFixed(5)
  return `https://www.openstreetmap.org/export/embed.html?bbox=${f(lng - d)}%2C${f(lat - d)}%2C${f(lng + d)}%2C${f(lat + d)}&layer=mapnik&marker=${f(lat)}%2C${f(lng)}`
}

/** Shows where a report is. `map` adds an embedded OpenStreetMap (loaded from openstreetmap.org when shown). */
export default function LocationPreview({ coords, map = false, accuracy }) {
  const { t } = useT()
  if (!coords) return null
  const weak = accuracy != null && accuracy > 200
  return (
    <div className="space-y-2">
      <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink/70">
        <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" aria-hidden="true" />
          {t('geo.coords')}: {Number(coords.lat).toFixed(5)}, {Number(coords.lng).toFixed(5)}
          {accuracy != null && ` · ${t('geo.accuracy')} ${accuracy} m`}</span>
        <a href={mapLink(coords)} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 font-medium text-brand hover:underline">
          {t('geo.openMap')}<ExternalLink className="h-3 w-3" aria-hidden="true" /></a>
      </p>
      {weak && <p role="status" className="rounded-lg bg-gold/15 p-2 text-xs">{t('geo.weak')}</p>}
      {map && (
        <>
          <iframe title={t('geo.mapTitle')} src={embedSrc(coords)} loading="lazy" referrerPolicy="no-referrer"
            sandbox="allow-scripts allow-same-origin" className="h-56 w-full rounded-xl border border-ink/10" />
          <p className="text-[11px] text-ink/50">{t('geo.mapNote')}</p>
        </>
      )}
    </div>
  )
}
