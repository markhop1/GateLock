/**
 * Nuki Smart Lock integration via Nuki Web API.
 * Unlock/lock the physical lock when access is accepted from the web app.
 */

import Nuki from 'nuki-web-api'

const NUKI_TOKEN = process.env.NUKI_TOKEN
const NUKI_SMARTLOCK_ID = process.env.NUKI_SMARTLOCK_ID
const NUKI_ACTION = process.env.NUKI_ACTION || 'unlock'

// Action codes: 1=unlock, 2=lock, 3=unlatch, 4=lockngo, 5=lockngo with unlatch
const ACTION_UNLOCK = 1
const ACTION_LOCK = 2
const ACTION_UNLATCH = 3

function isConfigured(): boolean {
  return Boolean(NUKI_TOKEN && NUKI_SMARTLOCK_ID)
}

function getActionCode(): number {
  if (NUKI_ACTION === 'unlatch') {
    return ACTION_UNLATCH
  }
  return ACTION_UNLOCK
}

/**
 * Unlock the Nuki smart lock (or unlatch if NUKI_ACTION=unlatch).
 * No-op if Nuki is not configured.
 * @param options.throwOnError - If true, rethrow on error (for manual API calls)
 */
export async function unlock(options?: { throwOnError?: boolean }): Promise<void> {
  if (!isConfigured()) {
    if (options?.throwOnError) {
      throw new Error('Nuki is not configured')
    }
    return
  }

  const smartlockId = parseInt(NUKI_SMARTLOCK_ID!, 10)
  if (Number.isNaN(smartlockId)) {
    console.error('[Nuki] Invalid NUKI_SMARTLOCK_ID:', NUKI_SMARTLOCK_ID)
    if (options?.throwOnError) {
      throw new Error('Invalid NUKI_SMARTLOCK_ID')
    }
    return
  }

  try {
    const nuki = new Nuki(NUKI_TOKEN!)
    const action = getActionCode()
    await nuki.setAction(smartlockId, action)
    console.log('[Nuki] Lock action executed successfully:', action === ACTION_UNLATCH ? 'unlatch' : 'unlock')
  } catch (error) {
    console.error('[Nuki] Failed to execute lock action:', error)
    if (options?.throwOnError) {
      throw error
    }
  }
}

/**
 * Lock the Nuki smart lock.
 */
export async function lock(): Promise<void> {
  if (!isConfigured()) {
    return
  }

  const smartlockId = parseInt(NUKI_SMARTLOCK_ID!, 10)
  if (Number.isNaN(smartlockId)) {
    console.error('[Nuki] Invalid NUKI_SMARTLOCK_ID:', NUKI_SMARTLOCK_ID)
    return
  }

  try {
    const nuki = new Nuki(NUKI_TOKEN!)
    await nuki.setAction(smartlockId, ACTION_LOCK)
    console.log('[Nuki] Lock action executed successfully: lock')
  } catch (error) {
    console.error('[Nuki] Failed to execute lock action:', error)
    throw error
  }
}

export type LockStatus = 'locked' | 'unlocked' | 'unlatched' | 'unavailable' | 'unknown'

export type LockStatusResult =
  | { configured: false; notConfigured: true }
  | { configured: true; status: LockStatus; name?: string; batteryCritical?: boolean }
  | { configured: true; status: 'unavailable'; error: true }

/**
 * Get the current lock state from Nuki.
 * State mapping (Nuki Web API): 0=uncalibrated, 1=locked, 2=unlocked, 3=unlatch, 4=unlocked lock'n'go, 5=unlatch lock'n'go
 */
export async function getState(): Promise<LockStatusResult> {
  if (!isConfigured()) {
    return { configured: false, notConfigured: true }
  }

  const smartlockId = parseInt(NUKI_SMARTLOCK_ID!, 10)
  if (Number.isNaN(smartlockId)) {
    return { configured: true, status: 'unavailable', error: true }
  }

  try {
    const nuki = new Nuki(NUKI_TOKEN!)
    const lock = (await nuki.getSmartlock(smartlockId)) as Record<string, unknown>
    const stateObj = lock.state
    const state =
      typeof stateObj === 'object' && stateObj !== null && 'state' in stateObj
        ? (stateObj as { state?: number }).state
        : typeof stateObj === 'number'
          ? stateObj
          : lock.stateName ?? (lock.config as { state?: number } | undefined)?.state
    let status: LockStatus = 'unknown'
    if (typeof state === 'number') {
      if (state === 1) status = 'locked'
      else if (state === 2 || state === 4 || state === 5) status = 'unlocked'
      else if (state === 3) status = 'unlatched'
      else if (state === 0) status = 'unavailable'
    }
    return {
      configured: true,
      status,
      name: lock.name as string | undefined,
      batteryCritical: lock.batteryCritical as boolean | undefined,
    }
  } catch (error) {
    console.error('[Nuki] Failed to get lock state:', error)
    return { configured: true, status: 'unavailable', error: true }
  }
}
