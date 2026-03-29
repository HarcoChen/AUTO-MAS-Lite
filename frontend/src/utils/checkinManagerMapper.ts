import { isCredentialPlatform } from '@/utils/checkinManagerProvider'
import {
  type CheckinProvider,
  type CheckinUserRow,
  type CredentialPlatform,
  type CredentialRow,
} from '@/types/checkin'

type RawGlobalCredentialPayload = {
  instances: Array<{ uid: string }>
  [key: string]: any
}

type RawScriptUser = {
  id: string
  name: string
  Info: Record<string, any>
  Data: Record<string, any>
}

type RawScript = {
  uid: string
  type: string
  name: string
  users: RawScriptUser[]
}

export const parseGlobalCredentialRows = (raw: RawGlobalCredentialPayload): CredentialRow[] => {
  return raw.instances.map(item => {
    const detail = raw[item.uid]
    const platform = resolvePlatform(detail.Info.Platform)
    return {
      id: item.uid,
      name: detail.Info.Name,
      platform,
      enabled: detail.Info.Enabled,
      token: detail.Data.Token,
      notes: detail.Data.Notes,
      dirty: false,
    }
  })
}

export const buildGlobalCredentialPayload = (rows: CredentialRow[]) => {
  const payload: Record<string, any> = { instances: [] as Array<{ uid: string; type: string }> }

  for (const credential of rows) {
    payload.instances.push({ uid: credential.id, type: 'GlobalCredential' })
    payload[credential.id] = {
      Info: {
        Name: credential.name,
        Platform: credential.platform,
        Enabled: credential.enabled,
      },
      Data: {
        Token: credential.token,
        Notes: credential.notes,
      },
    }
  }

  return payload
}

export const mapScriptsToCheckinUsers = (
  scripts: RawScript[],
  provider: CheckinProvider
): CheckinUserRow[] => {
  return scripts
    .filter(script => provider.supportedScripts.includes(script.type as CheckinUserRow['scriptType']))
    .flatMap(script => {
      const scriptType = script.type as CheckinUserRow['scriptType']
      const users = script.users

      return users.map(user => {
        const mapping = provider.toUserMapping(user)
        return {
          scriptId: script.uid,
          scriptName: script.name,
          scriptType,
          userId: user.id,
          userName: user.Info.Name,
          ifEnabled: mapping.ifEnabled,
          credentialId: mapping.credentialId,
          lastCheckinDate: mapping.lastCheckinDate,
          dirty: false,
          saving: false,
        }
      })
    })
    .sort((a, b) => {
      const typeCompare = a.scriptType.localeCompare(b.scriptType)
      if (typeCompare !== 0) return typeCompare

      const scriptCompare = a.scriptName.localeCompare(b.scriptName, 'zh-CN')
      if (scriptCompare !== 0) return scriptCompare

      return a.userName.localeCompare(b.userName, 'zh-CN')
    })
}

const resolvePlatform = (platform: unknown): CredentialPlatform => {
  if (!isCredentialPlatform(platform)) {
    throw new Error(`未知凭证平台: ${String(platform)}`)
  }
  return platform
}
