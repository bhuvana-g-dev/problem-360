import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import Field from './Field.jsx'

export default function PasswordField({ label = 'Password', ...rest }) {
  const [show, setShow] = useState(false)
  return (
    <div className="relative">
      <Field label={label} type={show ? 'text' : 'password'} {...rest} />
      <button type="button" onClick={() => setShow((s) => !s)} aria-label={show ? 'Hide password' : 'Show password'}
        className="absolute right-3 top-[2.1rem] text-ink/50 hover:text-ink">
        {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  )
}
