<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCheckinManager } from '@/composables/useCheckinManager'
import { buildUserEditorPath } from '@/utils/checkinManagerProvider'
import type { CheckinUserRow } from '@/types/checkin'

const router = useRouter()
const activeManagerTab = ref('users')
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

const goToUserEditor = (user: CheckinUserRow) => {
  router.push(buildUserEditorPath(user.scriptType, user.scriptId, user.userId))
}

void refreshData()
</script>

<template>
  <div class="checkin-tab-content">
    <div class="checkin-toolbar">
      <a-space>
        <a-tag color="processing">用户总数: {{ totalUserCount }}</a-tag>
        <a-tag color="success">已启用: {{ enabledUserCount }}</a-tag>
      </a-space>
      <a-space>
        <a-button :loading="loading" @click="refreshData">刷新</a-button>
      </a-space>
    </div>

    <a-alert
      type="info"
      show-icon
      message="全局凭证由工具页统一管理"
      description="现在您的Token迁移到工具页进行统一管理,仍会在用户执行脚本时自动签到。"
      style="margin-bottom: 16px"
    />

    <a-tabs v-model:activeKey="activeManagerTab" class="manager-tabs">
      <a-tab-pane key="users" tab="用户映射">
        <a-spin :spinning="busy">
          <a-empty v-if="checkinUsers.length === 0" description="未找到可管理的 MAA/MaaEnd 用户" />

          <div v-else class="checkin-list">
            <a-card v-for="user in checkinUsers" :key="`${user.scriptId}-${user.userId}`" class="checkin-card" size="small">
              <div class="checkin-card-header">
                <div class="checkin-card-title-wrap">
                  <div class="checkin-card-title">{{ user.userName }}</div>
                  <div class="checkin-card-subtitle">{{ user.scriptName }} · {{ scriptTypeLabel(user.scriptType) }}</div>
                </div>
                <div class="checkin-card-tags">
                  <a-tag color="processing">{{ providerLabel }}</a-tag>
                  <a-tag :color="statusTag(user).color">{{ statusTag(user).text }}</a-tag>
                  <a-tag v-if="userError(user)" color="error">配置错误</a-tag>
                </div>
              </div>

              <a-row :gutter="12" style="margin-top: 8px">
                <a-col :xs="24" :md="5">
                  <div class="checkin-label">启用签到</div>
                  <a-switch
                    v-model:checked="user.ifEnabled"
                    @change="onUserEnabledChange(user)"
                  />
                </a-col>
                <a-col :xs="24" :md="13">
                  <div class="checkin-label">全局凭证</div>
                  <a-select
                    v-model:value="user.credentialId"
                    :disabled="!user.ifEnabled"
                    :options="credOptions"
                    placeholder="请选择全局凭证"
                    style="width: 100%"
                    @change="onUserCredentialChange(user)"
                  />
                </a-col>
                <a-col :xs="24" :md="6">
                  <div class="checkin-label">最近签到日期(UTC+8)</div>
                  <div class="checkin-date">{{ user.lastCheckinDate }}</div>
                </a-col>
              </a-row>

              <div class="checkin-card-actions">
                <a-button size="small" @click="goToUserEditor(user)">打开用户页</a-button>
                <a-tag v-if="user.saving" color="processing">保存中</a-tag>
              </div>
            </a-card>
          </div>
        </a-spin>
      </a-tab-pane>

      <a-tab-pane key="credentials" tab="全局凭证">
        <a-card title="全局凭证库" size="small" class="credential-card">
          <template #extra>
            <a-space>
              <a-button size="small" @click="addCred">新增凭证</a-button>
              <a-button
                v-if="dirtyCredCount > 0"
                type="primary"
                size="small"
                :loading="savingCreds"
                @click="saveCreds"
              >
                保存全部改动
              </a-button>
            </a-space>
          </template>

          <a-empty v-if="creds.length === 0" description="暂无全局凭证" />
          <div v-else class="credential-list">
            <div v-for="group in credentialGroups" :key="group.platform" class="credential-group">
              <div class="credential-group-header">
                <a-tag color="processing">{{ group.label }}</a-tag>
                <span class="credential-group-count">{{ group.creds.length }} 项</span>
              </div>
              <a-card v-for="credential in group.creds" :key="credential.id" size="small" class="credential-item">
                <a-row :gutter="12">
                  <a-col :xs="24" :md="6">
                    <div class="checkin-label">名称</div>
                    <a-input v-model:value="credential.name" @change="onCredentialChange(credential)" />
                  </a-col>
                  <a-col :xs="24" :md="8">
                    <div class="checkin-label">Token</div>
                    <a-input-password
                      v-model:value="credential.token"
                      placeholder="请输入全局Token"
                      allow-clear
                      @change="onCredentialChange(credential)"
                    />
                  </a-col>
                  <a-col :xs="24" :md="4">
                    <div class="checkin-label">平台</div>
                    <a-select
                      v-model:value="credential.platform"
                      :options="platformOptions"
                      style="width: 100%"
                      @change="onCredentialChange(credential)"
                    />
                  </a-col>
                  <a-col :xs="24" :md="6" class="credential-delete-col">
                    <a-space direction="vertical" size="small" style="align-items: flex-end">
                      <a-button
                        v-if="credential.dirty"
                        type="primary"
                        size="small"
                        :loading="savingCreds"
                        @click="saveCredential(credential)"
                      >
                        保存
                      </a-button>
                      <a-button danger size="small" @click="removeCred(credential.id)">删除</a-button>
                    </a-space>
                  </a-col>
                </a-row>
                <a-row :gutter="12" style="margin-top: 8px">
                  <a-col :span="24">
                    <div class="checkin-label">备注</div>
                    <a-input v-model:value="credential.notes" @change="onCredentialChange(credential)" />
                  </a-col>
                </a-row>
              </a-card>
            </div>
          </div>
        </a-card>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<style scoped>
.checkin-tab-content {
  padding: 12px;
}

.checkin-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.credential-card {
  margin-bottom: 16px;
}

.credential-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.credential-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.credential-group-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.credential-group-count {
  color: var(--ant-color-text-secondary);
  font-size: 12px;
}

.credential-item {
  border-radius: 10px;
}

.credential-delete-col {
  display: flex;
  align-items: end;
  justify-content: flex-end;
}

.checkin-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.checkin-card {
  border-radius: 10px;
}

.checkin-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.checkin-card-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--ant-color-text);
}

.checkin-card-subtitle {
  margin-top: 2px;
  font-size: 12px;
  color: var(--ant-color-text-secondary);
}

.checkin-card-tags {
  display: flex;
  align-items: center;
  gap: 6px;
}

.checkin-label {
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--ant-color-text-secondary);
}

.checkin-date {
  height: 32px;
  display: flex;
  align-items: center;
  padding: 0 11px;
  border: 1px solid var(--ant-color-border);
  border-radius: 6px;
  background: var(--ant-color-bg-container-disabled);
  color: var(--ant-color-text);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
}

.checkin-card-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 900px) {
  .checkin-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .credential-delete-col {
    justify-content: flex-start;
    margin-top: 6px;
  }
}
</style>
