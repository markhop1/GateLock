declare module 'nuki-web-api' {
  interface NukiOptions {
    url?: string
  }

  interface NukiSmartlockState {
    state?: number
    stateName?: string
    batteryCritical?: boolean
    name?: string
  }

  interface NukiClient {
    setAction(smartlockId: number, action: number): Promise<void>
    getSmartlock(smartlockId: number): Promise<NukiSmartlockState>
  }

  declare class Nuki {
    constructor(token: string, options?: NukiOptions)
    setAction(smartlockId: number, action: number): Promise<void>
    getSmartlock(smartlockId: number): Promise<NukiSmartlockState>
  }

  export default Nuki
}
