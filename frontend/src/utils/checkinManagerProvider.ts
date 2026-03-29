import {
  DEFAULT_CREDENTIAL_ID,
  type CheckinProvider,
  type CheckinScriptType,
  type CredentialPlatform,
} from '@/types/checkin'

interface ScriptTarget {
  scriptType: CheckinScriptType
  label: string
  editMode: 'maa' | 'maaend'
}

const SCRIPT_TARGETS: ScriptTarget[] = [
  { scriptType: 'MAA', label: 'Arknights', editMode: 'maa' },
  { scriptType: 'MaaEnd', label: 'Endfield', editMode: 'maaend' },
]

const SCRIPT_TARGET_MAP = new Map(SCRIPT_TARGETS.map(item => [item.scriptType, item]))

const PROVIDERS: CheckinProvider[] = [
  {
    platform: 'Skland',
    displayName: 'Skland',
    enabled: true,
    supportedScripts: ['MAA', 'MaaEnd'],
    toUserMapping: user => ({
      ifEnabled: user.Info.IfSkland,
      credentialId: user.Info.SklandCredentialId,
      lastCheckinDate: user.Data.LastSklandDate,
    }),
    buildUpdateInfo: mapping => ({
      IfSkland: mapping.ifEnabled,
      SklandCredentialId: mapping.ifEnabled ? mapping.credentialId : DEFAULT_CREDENTIAL_ID,
    }),
  },
]

const PROVIDER_MAP = new Map(PROVIDERS.map(item => [item.platform, item]))
const DEFAULT_PROVIDER = PROVIDERS[0]

if (!DEFAULT_PROVIDER) {
  throw new Error('签到平台配置不能为空')
}

export const CHECKIN_PROVIDERS = PROVIDERS

export const getProvider = (platform: CredentialPlatform) => PROVIDER_MAP.get(platform)

export const isCredentialPlatform = (platform: unknown): platform is CredentialPlatform =>
  typeof platform === 'string' && PROVIDER_MAP.has(platform as CredentialPlatform)

export const getEnabledProviders = () => CHECKIN_PROVIDERS.filter(item => item.enabled)
export const getDefaultProvider = () => DEFAULT_PROVIDER

export const isCheckinScriptType = (scriptType: string): scriptType is CheckinScriptType =>
  SCRIPT_TARGET_MAP.has(scriptType as CheckinScriptType)

export const getScriptTypeLabel = (scriptType: CheckinScriptType) =>
  SCRIPT_TARGET_MAP.get(scriptType)!.label

export const buildUserEditorPath = (
  scriptType: CheckinScriptType,
  scriptId: string,
  userId: string
) => {
  const target = SCRIPT_TARGET_MAP.get(scriptType)!
  return `/scripts/${scriptId}/users/${userId}/edit/${target.editMode}`
}
