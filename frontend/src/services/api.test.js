import { describe, it, expect } from 'vitest'
import { formatApiError } from './api'

describe('formatApiError', () => {
  it('returns a plain string detail unchanged', () => {
    expect(formatApiError({ response: { data: { detail: 'Not found' } } })).toBe('Not found')
  })

  it('flattens FastAPI 422 validation arrays into a readable string', () => {
    const err = {
      response: {
        data: {
          detail: [
            { loc: ['body', 'occupation'], msg: 'Field required' },
            { loc: ['body', 'state'], msg: 'Invalid value' },
          ],
        },
      },
    }
    expect(formatApiError(err)).toBe('occupation: Field required, state: Invalid value')
  })

  it('handles object details', () => {
    expect(formatApiError({ response: { data: { detail: { msg: 'Bad request' } } } })).toBe('Bad request')
  })

  it('falls back to the error message and then the default', () => {
    expect(formatApiError({ message: 'Network Error' })).toBe('Network Error')
    expect(formatApiError({}, 'Fallback text')).toBe('Fallback text')
  })
})
