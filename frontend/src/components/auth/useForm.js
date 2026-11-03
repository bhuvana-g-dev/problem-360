import { useState } from 'react'

/** Tiny form helper: values, per-field errors, submit state and a top-level message. */
export default function useForm(initial, validate) {
  const [values, setValues] = useState(initial)
  const [errors, setErrors] = useState({})
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState('')
  const set = (name) => (e) => setValues((v) => ({ ...v, [name]: e.target.value }))
  const submit = (fn) => async (e) => {
    e.preventDefault()
    const errs = validate(values)
    setErrors(errs); setFormError('')
    if (Object.keys(errs).length) return
    setSubmitting(true)
    try { await fn(values) } catch (err) { setFormError(err.message) } finally { setSubmitting(false) }
  }
  const reset = () => { setValues(initial); setErrors({}) }
  return { values, errors, set, submit, submitting, formError, reset }
}

export const isEmail = (s) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s)
export const loginRules = (v) => ({
  ...(isEmail(v.email) ? {} : { email: 'Enter a valid email.' }),
  ...(v.password ? {} : { password: 'Enter your password.' }),
})
