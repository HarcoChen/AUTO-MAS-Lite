export const DEFAULT_CREDENTIAL_ID = '-'

export type CredentialPlatform = 'Skland' | 'Mihoyo' | 'WW'
export type CheckinScriptType = 'MAA' | 'MaaEnd'

export interface CredentialRow {
  id: string
  name: string
  platform: CredentialPlatform
  enabled: boolean
  token: string
  notes: string
  dirty: boolean
}

export interface CheckinUserRow {
  scriptId: string
  scriptName: string
  scriptType: CheckinScriptType
  userId: string
  userName: string
  ifEnabled: boolean
  credentialId: string
  lastCheckinDate: string
  dirty: boolean
  saving: boolean
}

export interface CheckinProvider {
  platform: CredentialPlatform
  displayName: string
  enabled: boolean
  supportedScripts: CheckinScriptType[]
  toUserMapping: (user: any) => Pick<CheckinUserRow, 'ifEnabled' | 'credentialId' | 'lastCheckinDate'>
  buildUpdateInfo: (mapping: Pick<CheckinUserRow, 'ifEnabled' | 'credentialId'>) => Record<string, any>
}
