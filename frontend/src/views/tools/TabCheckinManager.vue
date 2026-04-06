<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCheckinManager } from '@/composables/useCheckinManager'
import { buildUserEditorPath } from '@/utils/checkinManagerProvider'
import type { CheckinUserRow } from '@/types/checkin'
import {
  UserOutlined,
  KeyOutlined,
  SearchOutlined,
  PlusOutlined,
  SaveOutlined,
  SyncOutlined,
  ExclamationCircleOutlined,
  ArrowRightOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const activeManagerTab = ref('users')
const searchQuery = ref('')

const {
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
  onCredentialChange,
  saveCredential,
  saveCreds,
  onUserCredentialChange,
  onUserEnabledChange,
  userError,
  refreshData,
  scriptTypeLabel,
  statusTag,
} = useCheckinManager()

// 搜索过滤
const filteredUsers = computed(() => {
  if (!searchQuery.value) return checkinUsers.value
  const query = searchQuery.value.toLowerCase()
  return checkinUsers.value.filter(
    user =>
      user.userName.toLowerCase().includes(query) ||
      user.scriptName.toLowerCase().includes(query)
  )
})

const goToUserEditor = (user: CheckinUserRow) => {
  router.push(buildUserEditorPath(user.scriptType, user.scriptId, user.userId))
}

const getBindingCount = (credId: string) => {
  return checkinUsers.value.filter(u => u.ifEnabled && u.credentialId === credId).length
}

void refreshData()
</script>

<template>
  <div class="checkin-container">
    <!-- 顶部状态栏 -->
    <div class="header-section">
      <div class="header-left">
        <h2 class="title">签到统一管理</h2>
        <div class="stats">
          <a-badge status="processing" :text="`用户总数 ${totalUserCount}`" />
          <a-divider type="vertical" />
          <a-badge status="success" :text="`已开启 ${enabledUserCount}`" />
        </div>
      </div>
      <div class="header-right">
        <a-space>
          <a-button @click="refreshData" :loading="loading">
            <template #icon><sync-outlined /></template>
            刷新数据
          </a-button>
          <a-button
            v-if="dirtyCredCount > 0"
            type="primary"
            @click="saveCreds"
            :loading="savingCreds"
          >
            <template #icon><save-outlined /></template>
            保存凭证改动 ({{ dirtyCredCount }})
          </a-button>
        </a-space>
      </div>
    </div>

    <a-alert class="mas-alert" type="info" show-icon>
      <template #message>全局凭证管理说明</template>
      <template #description>
        森空岛等平台的 Token 现已迁移到“全局凭证”库中统一管理。
        您只需在此处配置一次 Token，即可分配给多个脚本用户使用，且支持一键更新。
      </template>
    </a-alert>

    <a-tabs v-model:activeKey="activeManagerTab" class="mas-tabs" type="card">
      <!-- 选项卡 1: 用户签到映射 -->
      <a-tab-pane key="users">
        <template #tab>
          <span><user-outlined />用户映射</span>
        </template>

        <div class="tab-actions">
          <a-input
            v-model:value="searchQuery"
            placeholder="搜索用户名或脚本名..."
            allow-clear
            class="search-input"
          >
            <template #prefix><search-outlined /></template>
          </a-input>
        </div>

        <a-spin :spinning="busy">
          <div v-if="filteredUsers.length === 0" class="empty-state">
            <a-empty description="未找到匹配的用户" />
          </div>

          <div v-else class="user-grid">
            <a-card
              v-for="user in filteredUsers"
              :key="`${user.scriptId}-${user.userId}`"
              class="user-card"
              hoverable
              :body-style="{ padding: '16px' }"
            >
              <div class="user-card-header">
                <div class="user-info">
                  <div class="user-name">{{ user.userName }}</div>
                  <div class="script-info">
                    <a-tag size="small">{{ scriptTypeLabel(user.scriptType) }}</a-tag>
                    {{ user.scriptName }}
                  </div>
                </div>
                <div class="user-status">
                  <a-tag :color="statusTag(user).color">{{ statusTag(user).text }}</a-tag>
                </div>
              </div>

              <div class="user-card-body">
                <div class="control-item">
                  <span class="label">开启自动签到</span>
                  <a-switch
                    v-model:checked="user.ifEnabled"
                    size="small"
                    @change="onUserEnabledChange(user)"
                  />
                </div>

                <div class="control-item column">
                  <span class="label">使用全局凭证</span>
                  <a-select
                    v-model:value="user.credentialId"
                    :disabled="!user.ifEnabled"
                    :options="credOptions"
                    placeholder="选择凭证..."
                    class="cred-select"
                    @change="onUserCredentialChange(user)"
                  >
                    <template #suffixIcon><key-outlined /></template>
                  </a-select>
                  <div v-if="userError(user)" class="error-text">
                    <exclamation-circle-outlined /> {{ userError(user) }}
                  </div>
                </div>
              </div>

              <div class="user-card-footer">
                <div class="last-date">
                  <span class="label">上次签到:</span>
                  <span class="val">{{ user.lastCheckinDate || '从未' }}</span>
                </div>
                <a-button type="link" size="small" @click="goToUserEditor(user)">
                  详情 <arrow-right-outlined />
                </a-button>
              </div>
              
              <div v-if="user.saving" class="saving-overlay">
                <a-spin size="small" />
              </div>
            </a-card>
          </div>
        </a-spin>
      </a-tab-pane>

      <!-- 选项卡 2: 全局凭证库 -->
      <a-tab-pane key="credentials">
        <template #tab>
          <span>
            <key-outlined />全局凭证
            <a-badge v-if="dirtyCredCount > 0" dot class="tab-dot" />
          </span>
        </template>

        <a-spin :spinning="busy">
          <div class="cred-groups">
            <div v-for="group in credentialGroups" :key="group.platform" class="group-section">
              <div class="group-header">
                <div class="group-header-left">
                  <span class="group-title">{{ group.label }} 平台</span>
                  <a-tag size="small">{{ group.creds.length }}</a-tag>
                </div>
                <a-button type="link" size="small" @click="addCred(group.platform)">
                  <template #icon><plus-outlined /></template>
                  新增凭证
                </a-button>
              </div>

              <div v-if="group.creds.length === 0" class="empty-state-compact">
                <a-empty :description="`暂无${group.label}凭证`" :image-style="{ height: '40px' }" />
              </div>

              <div v-else class="cred-grid">
                <a-card
                  v-for="credential in group.creds"
                  :key="credential.id"
                  class="cred-card"
                  :class="{ 'is-dirty': credential.dirty }"
                  size="small"
                >
                  <template #title>
                    <a-input
                      v-model:value="credential.name"
                      placeholder="凭证别名"
                      class="name-input"
                      @change="onCredentialChange(credential)"
                    />
                  </template>
                  <template #extra>
                    <a-tag v-if="credential.dirty" color="warning" size="small">未保存</a-tag>
                    <a-tooltip title="当前绑定用户数">
                      <a-badge :count="getBindingCount(credential.id)" :number-style="{ backgroundColor: '#52c41a' }" />
                    </a-tooltip>
                  </template>

                  <div class="cred-body">
                    <div class="field">
                      <div class="label">Token / 令牌</div>
                      <a-input-password
                        v-model:value="credential.token"
                        placeholder="输入 Token"
                        @change="onCredentialChange(credential)"
                      />
                    </div>
                    <div class="field">
                      <div class="label">备注信息</div>
                      <a-input
                        v-model:value="credential.notes"
                        placeholder="例如：主账号、二号机..."
                        @change="onCredentialChange(credential)"
                      />
                    </div>
                  </div>

                  <template #actions>
                    <a-button
                      v-if="credential.dirty"
                      type="link"
                      size="small"
                      @click="saveCredential(credential)"
                      :loading="savingCreds"
                    >
                      <save-outlined /> 保存
                    </a-button>
                    <a-popconfirm
                      title="确定删除此凭证吗？关联的用户将无法继续签到。"
                      @confirm="removeCred(credential.id)"
                    >
                      <a-button type="link" danger size="small">
                        <delete-outlined /> 删除
                      </a-button>
                    </a-popconfirm>
                  </template>
                </a-card>
              </div>
            </div>
          </div>
        </a-spin>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<style scoped>
.checkin-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 4px;
}

.stats {
  display: flex;
  align-items: center;
  color: var(--ant-color-text-secondary);
}

.mas-alert {
  margin-bottom: 24px;
  border-radius: 8px;
}

.tab-actions {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.search-input {
  max-width: 300px;
}

.tab-dot {
  margin-left: 4px;
}

/* 用户网格布局 */
.user-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.user-card {
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.user-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.user-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.user-name {
  font-size: 16px;
  font-weight: 600;
  line-height: 1.4;
}

.script-info {
  font-size: 12px;
  color: var(--ant-color-text-secondary);
  margin-top: 2px;
}

.user-card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 0;
  border-top: 1px solid var(--ant-color-border-secondary);
}

.control-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-item.column {
  flex-direction: column;
  align-items: flex-start;
}

.control-item .label {
  font-size: 13px;
  color: var(--ant-color-text-secondary);
  margin-bottom: 4px;
}

.cred-select {
  width: 100%;
}

.error-text {
  color: var(--ant-color-error);
  font-size: 11px;
  margin-top: 4px;
}

.user-card-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--ant-color-border-secondary);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.last-date {
  font-size: 11px;
}

.last-date .label {
  color: var(--ant-color-text-secondary);
  margin-right: 4px;
}

.saving-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

/* 凭证库布局 */
.group-section {
  margin-bottom: 24px;
}

.group-header {
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--ant-color-bg-container-secondary);
  padding: 8px 12px;
  border-radius: 8px;
}

.group-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.group-title {
  font-weight: 600;
  font-size: 15px;
}

.cred-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.cred-card {
  border-radius: 12px;
  border: 1px solid var(--ant-color-border-secondary);
}

.cred-card.is-dirty {
  border-color: var(--ant-color-warning-border);
  background-color: var(--ant-color-warning-bg);
}

.name-input {
  font-weight: 600;
  border: none;
  background: transparent;
  padding: 0;
}

.name-input:focus {
  background: var(--ant-color-bg-container);
  padding: 0 4px;
}

.cred-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field .label {
  font-size: 12px;
  color: var(--ant-color-text-secondary);
  margin-bottom: 4px;
}

.empty-state {
  padding: 60px 0;
  background: var(--ant-color-bg-container);
  border-radius: 12px;
}

.empty-state-compact {
  padding: 24px 0;
}

@media (max-width: 600px) {
  .header-section {
    flex-direction: column;
    gap: 12px;
  }
  
  .user-grid, .cred-grid {
    grid-template-columns: 1fr;
  }
}
</style>
