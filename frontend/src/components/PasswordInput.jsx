/**
 * PasswordInput — labelled password field with an accessible visibility toggle.
 *
 * The toggle is a real button (keyboard reachable) and exposes its state via
 * `aria-pressed`. The label stays associated with the input through `htmlFor`.
 */

import { useId, useState } from 'react'
import Icon from './Icon'

export default function PasswordInput({
  id,
  label,
  name,
  value,
  onChange,
  placeholder = '••••••••',
  autoComplete = 'current-password',
  required = true,
  hint,
}) {
  const generatedId = useId()
  const inputId = id || generatedId
  const [visible, setVisible] = useState(false)

  return (
    <div>
      <label htmlFor={inputId} className="label">{label}</label>
      <div className="password-wrap">
        <input
          id={inputId}
          name={name}
          type={visible ? 'text' : 'password'}
          className="input"
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          required={required}
          aria-describedby={hint ? `${inputId}-hint` : undefined}
        />
        <button
          type="button"
          className="password-toggle"
          onClick={() => setVisible((current) => !current)}
          aria-label={visible ? 'Hide password' : 'Show password'}
          aria-pressed={visible}
          aria-controls={inputId}
        >
          <Icon name={visible ? 'eyeOff' : 'eye'} size={17} />
        </button>
      </div>
      {hint && (
        <p id={`${inputId}-hint`} className="field-hint">{hint}</p>
      )}
    </div>
  )
}
