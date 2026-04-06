import { computed, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useScriptApi } from '@/composables/useScriptApi'
import { useToolsApi } from '@/composables/useToolsApi'
import { useUserApi } from '@/composables/useUserApi'
import { getTodayInTimezone, isDateEqual } from '@/utils/dateUtils'
import {
  CHECKIN_PROVIDERS,
  getDefaultProvider,
  getScriptTypeLabel,
} from '@/utils/checkinManagerProvider'
import {
  buildGlobalCredentialPayload,
  mapScriptsToCheckinUsers,
  parseGlobalCredentialRows,
} from '@/utils/checkinManagerMapper'
import {
  DEFAULT_CREDENTIAL_ID,
  type CheckinUserRow,
  type CredentialRow,
} from '@/types/checkin'

export function useCheckinManager() {
  const logger = window.electronAPI.getLogger('签到管理')
  const { getScriptsWithUsers, loading: scriptsLoading } = useScriptApi()
  const { loading: toolsLoading, getTools, updateTools } = useToolsApi()
  const { updateUser } = useUserApi()
  const provider = getDefaultProvider()

  const creds = ref<CredentialRow[]>([])
  const checkinUsers = ref<CheckinUserRow[]>([])

  const loading = ref(false)
  const savingCreds = ref(false)

  const totalUserCount = computed(() => checkinUsers.value.length)
  const enabledUserCount = computed(() => checkinUsers.value.filter(item => item.ifEnabled).length)
  const busy = computed(() => loading.value || toolsLoading.value || scriptsLoading.value)

  const credOptions = computed(() =>
    creds.value.filter(item => item.enabled).map(item => ({ label: item.name, value: item.id }))
  )
  const dirtyCredCount = computed(() => creds.value.filter(item => item.dirty).length)
  
  // 核心：始终返回所有已定义的平台组，方便按平台创建
  const credentialGroups = computed(() =>
    CHECKIN_PROVIDERS.map(providerItem => ({
      platform: providerItem.platform,
      label: providerItem.displayName,
      creds: creds.value.filter(credential => credential.platform === providerItem.platform),
    }))
  )
  const platformOptions = computed(() =>
    CHECKIN_PROVIDERS.map(item => ({
      label: item.enabled ? item.displayName : `${item.displayName}(规划中)`,
      value: item.platform,
      disabled: !item.enabled,
    }))
  )

  const todayUTC8 = computed(() => getTodayInTimezone(8))

  // 核心：支持按平台添加
  const addCred = (platform?: CredentialRow['platform']) => {
    const uid = crypto.randomUUID()
    const targetPlatform = platform || provider.platform
    const platformLabel = CHECKIN_PROVIDERS.find(p => p.platform === targetPlatform)?.displayName || '未知'
    
    creds.value.push({
      id: uid,
      name: `${platformLabel}凭证-${creds.value.length + 1}`,
      platform: targetPlatform,
      enabled: true,
      token: '',
      notes: '',
      dirty: true,
    })
  }

  const removeCred = (credId: string) => {
    // 检查是否有用户正在使用
    const boundUsers = checkinUsers.value.filter(u => u.ifEnabled && u.credentialId === credId)
    if (boundUsers.length > 0) {
      const userNames = boundUsers.map(u => u.userName).join('、')
      message.warning(`无法删除：该凭证正被用户 [${userNames}] 使用。`)
      return
    }

    creds.value = creds.value.filter(item => item.id !== credId)

    checkinUsers.value.forEach(user => {
      if (user.credentialId === credId) {
        user.credentialId = DEFAULT_CREDENTIAL_ID
        user.dirty = true
      }
    })
  }

  const markCredDirty = (credential: CredentialRow) => {
    credential.dirty = true
  }

  const saveCredential = async (credential: CredentialRow) => {
    savingCreds.value = true
    try {
      const payload = buildGlobalCredentialPayload(creds.value)
      logger.debug(`保存单个凭证载荷: ${JSON.stringify(payload)}`)
      await updateTools({ GlobalCredentials: payload } as any)
      credential.dirty = false
      message.success(`已保存凭证：${credential.name}`)
      // 保存后刷新以确保注入状态
      void refreshData()
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error)
      logger.error(`保存凭证失败: ${errorMsg}`)
      message.error(`保存凭证失败：${credential.name}`)
    } finally {
      savingCreds.value = false
    }
  }

  const saveCreds = async () => {
    savingCreds.value = true
    try {
      const payload = buildGlobalCredentialPayload(creds.value)
      logger.debug(`保存全局凭证载荷: ${JSON.stringify(payload)}`)
      await updateTools({ GlobalCredentials: payload } as any)
      creds.value.forEach(item => {
        item.dirty = false
      })
      message.success('全局凭证已保存')
      // 保存后刷新
      void refreshData()
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error)
      logger.error(`保存全局凭证失败: ${errorMsg}`)
      message.error('保存全局凭证失败')
    } finally {
      savingCreds.value = false
    }
  }

  const scriptTypeLabel = getScriptTypeLabel
  const providerLabel = provider.displayName

  const statusTag = (user: CheckinUserRow) => {
    if (!user.ifEnabled) {
      return { text: '禁用', color: 'default' }
    }

    if (isDateEqual(user.lastCheckinDate, todayUTC8.value, 8)) {
      return { text: '已签到', color: 'green' }
    }

    return { text: '未签到', color: 'orange' }
  }

  const userError = (user: CheckinUserRow): string | null => {
    if (user.ifEnabled && user.credentialId === DEFAULT_CREDENTIAL_ID) {
      return '启用签到后必须绑定全局凭证'
    }
    return null
  }

  const markUserDirty = (user: CheckinUserRow) => {
    user.dirty = true
  }

  const onCredentialChange = (credential: CredentialRow) => {
    markCredDirty(credential)
  }

  const onUserEnabledChange = (user: CheckinUserRow) => {
    markUserDirty(user)
    void saveUserMapping(user)
  }

  const onUserCredentialChange = (user: CheckinUserRow) => {
    markUserDirty(user)
    void saveUserMapping(user)
  }

  const saveUserMapping = async (user: CheckinUserRow) => {
    if (user.saving) {
      return
    }

    const validationError = userError(user)
    if (validationError) {
      message.warning(`${user.userName}: ${validationError}`)
      return
    }

    user.saving = true
    try {
      const infoPayload = provider.buildUpdateInfo({
        ifEnabled: user.ifEnabled,
        credentialId: user.credentialId,
      })
      const ok = await updateUser(user.scriptId, user.userId, { Info: infoPayload })

      if (!ok) {
        throw new Error('保存失败')
      }

      user.dirty = false
      message.success(`已保存 ${user.userName} 的签到映射`)
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error)
      logger.error(`保存用户签到映射失败: ${errorMsg}`)
      message.error(`保存 ${user.userName} 失败`)
    } finally {
      user.saving = false
    }
  }

  const refreshData = async () => {
    loading.value = true
    try {
      const [toolsData, scriptsData] = await Promise.all([getTools(), getScriptsWithUsers()])

      const globalCredentials = (toolsData as any).GlobalCredentials
      logger.debug(`读取到的全局凭证原始数据: ${JSON.stringify(globalCredentials)}`)
      if (globalCredentials) {
        try {
          creds.value = parseGlobalCredentialRows(globalCredentials)
          logger.debug(`解析后的全局凭证数量: ${creds.value.length}`)
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error)
          logger.error(`解析凭证数据失败: ${errorMsg}`)
          creds.value = []
        }
      } else {
        creds.value = []
      }
      checkinUsers.value = mapScriptsToCheckinUsers(scriptsData as any, provider)
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error)
      logger.error(`加载签到管理数据失败: ${errorMsg}`)
      message.error('加载签到管理数据失败')
    } finally {
      loading.value = false
    }
  }

  return {
    creds,
    checkinUsers,
    totalUserCount,
    enabledUserCount,
    dirtyCredCount,
    credOptions,
    credentialGroups,
    platformOptions,
    providerLabel,
    busy,
    loading,
    savingCreds,
    addCred,
    removeCred,
    markCredDirty,
    onCredentialChange,
    saveCredential,
    saveCreds,
    markUserDirty,
    onUserCredentialChange,
    onUserEnabledChange,
    userError,
    saveUserMapping,
    refreshData,
    scriptTypeLabel,
    statusTag,
  }
}
