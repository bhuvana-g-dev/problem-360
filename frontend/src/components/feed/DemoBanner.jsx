import { DEMO } from '../../services/posts.js'
import Alert from '../ui/Alert.jsx'

export default function DemoBanner() {
  return DEMO ? <Alert tone="warning" title="Demo data">These posts are placeholders for previewing the interface. They are not real reports.</Alert> : null
}
