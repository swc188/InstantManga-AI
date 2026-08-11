<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { request } from '../api/client'

interface ModelConfig {
  capability: string
  provider_type: string
  base_url: string
  api_key_masked: string
  model_name: string
  is_valid: boolean
}

interface FormState {
  provider_type: string
  base_url: string
  api_key: string
  model_name: string
  url_mode: 'base' | 'full'
}

const CAPABILITIES = [
  { key: 'text', label: '文本生成', hint: '用于剧本、分镜拆解等' },
  { key: 'image', label: '图像生成', hint: '用于定妆照、分镜配图' },
  { key: 'tts', label: '语音合成', hint: '用于台词配音' },
  { key: 'video', label: '视频生成', hint: '用于分镜动效、短视频输出' },
]

const PROVIDER_TYPES = [
  { key: 'openai_compatible', label: 'OpenAI 兼容' },
  { key: 'jimeng', label: '即梦' },
  { key: 'keling', label: '可灵' },
]

const saved = ref<Record<string, ModelConfig>>({})
const forms = reactive<Record<string, FormState>>({
  text: { provider_type: 'openai_compatible', base_url: 'https://apihub.agnes-ai.com/v1', api_key: 'sk-Yj9wvxk4hg80ZuILNIUGWf41PrpJMjH8SayMCEjAWSqZ89r2', model_name: 'agnes-2.0-flash', url_mode: 'base' },
  image: { provider_type: 'openai_compatible', base_url: 'https://apihub.agnes-ai.com/v1/images/generations', api_key: 'sk-Yj9wvxk4hg80ZuILNIUGWf41PrpJMjH8SayMCEjAWSqZ89r2', model_name: 'agnes-image-2.0-flash', url_mode: 'full' },
  tts: { provider_type: 'openai_compatible', base_url: 'https://apihub.agnes-ai.com/v1', api_key: 'sk-Yj9wvxk4hg80ZuILNIUGWf41PrpJMjH8SayMCEjAWSqZ89r2', model_name: '', url_mode: 'base' },
  video: { provider_type: 'openai_compatible', base_url: 'https://apihub.agnes-ai.com/v1/videos', api_key: 'sk-Yj9wvxk4hg80ZuILNIUGWf41PrpJMjH8SayMCEjAWSqZ89r2', model_name: 'agnes-video-v2.0', url_mode: 'full' },
})
const saving = ref<Record<string, boolean>>({})
const testing = ref<Record<string, boolean>>({})
const results = ref<Record<string, string>>({})
const errorMsg = ref('')

async function load() {
  const list = await request<ModelConfig[]>('/model-config')
  saved.value = Object.fromEntries(list.map((c) => [c.capability, c]))
}

async function save(capability: string) {
  saving.value[capability] = true
  results.value[capability] = ''
  errorMsg.value = ''
  try {
    const cfg = await request<ModelConfig>(`/model-config/${capability}`, {
      method: 'PUT',
      body: JSON.stringify({
        provider_type: forms[capability].provider_type,
        base_url: forms[capability].base_url,
        api_key: forms[capability].api_key || undefined,
        model_name: forms[capability].model_name,
        url_mode: forms[capability].url_mode,
      }),
    })
    saved.value[capability] = cfg
    results.value[capability] = '已保存'
  } catch (e) {
    errorMsg.value = (e as Error).message
  } finally {
    saving.value[capability] = false
  }
}

async function testSaved(capability: string) {
  testing.value[capability] = true
  results.value[capability] = ''
  try {
    const res = await request<{ ok: boolean }>(`/model-config/${capability}/test`, {
      method: 'POST',
    })
    if (res.ok && saved.value[capability]) {
      saved.value[capability] = { ...saved.value[capability], is_valid: true }
    }
    results.value[capability] = res.ok ? '连通性正常' : '连通性异常'
  } catch (e) {
    results.value[capability] = (e as Error).message
  } finally {
    testing.value[capability] = false
  }
}

onMounted(load)
</script>

<template>
  <section class="model-config">
    <div class="head">
      <h1>模型配置</h1>
      <p>各环节 AI 能力使用统一服务商，API Key 统一配置后保存即可。</p>
    </div>

    <p v-if="errorMsg" class="error">{{ errorMsg }}</p>

    <form class="cards" @submit.prevent>
      <div v-for="cap in CAPABILITIES" :key="cap.key" class="card">
        <div class="card-head">
          <h2>{{ cap.label }}</h2>
          <span v-if="saved[cap.key]" class="badge" :class="saved[cap.key].is_valid ? 'ok' : 'bad'">
            {{ saved[cap.key].is_valid ? '已校验' : '未校验' }}
          </span>
        </div>
        <p class="hint">{{ cap.hint }}</p>

        <label>
          提供商类型
          <select v-model="forms[cap.key].provider_type">
            <option v-for="p in PROVIDER_TYPES" :key="p.key" :value="p.key">{{ p.label }}</option>
          </select>
        </label>

        <label>
          Base URL
          <div class="url-row">
            <div class="url-toggle">
              <button
                :class="{ active: forms[cap.key].url_mode === 'base' }"
                @click="forms[cap.key].url_mode = 'base'"
              >拼接地地</button>
              <button
                :class="{ active: forms[cap.key].url_mode === 'full' }"
                @click="forms[cap.key].url_mode = 'full'"
              >完整地址</button>
            </div>
            <input v-model="forms[cap.key].base_url" :placeholder="forms[cap.key].url_mode === 'base' ? 'https://api.example.com/v1' : 'https://api.example.com/v1/images/generations'" />
          </div>
          <span class="hint">{{ forms[cap.key].url_mode === 'base' ? '将自动拼接路径（如 /images/generations、/v1/videos）' : '直接填写完整端点 URL' }}</span>
        </label>

        <label>
          API Key
          <div class="key-row">
            <input v-model="forms[cap.key].api_key" type="password" :placeholder="saved[cap.key] ? `已配置（${saved[cap.key].api_key_masked}），留空不修改` : '输入 API Key'" />
          </div>
        </label>

        <label>
          模型名
          <input v-model="forms[cap.key].model_name" placeholder="模型名称" />
        </label>

        <div class="actions">
          <button :disabled="saving[cap.key]" @click="save(cap.key)">
            {{ saving[cap.key] ? '保存中…' : '保存' }}
          </button>
          <button
            class="ghost"
            :disabled="testing[cap.key] || !forms[cap.key].api_key"
            @click="testSaved(cap.key)"
          >
            {{ testing[cap.key] ? '测试中…' : '连通性测试' }}
          </button>
        </div>
        <p v-if="results[cap.key]" class="result">{{ results[cap.key] }}</p>
      </div>
    </form>
  </section>
</template>

<style scoped>
.model-config {
  max-width: 1000px;
  margin: 0 auto;
}

.head h1 {
  font-size: 22px;
  margin-bottom: 8px;
}

.head p {
  color: #64748b;
  font-size: 14px;
  margin-bottom: 24px;
}

.error {
  background: #fef2f2;
  color: #b91c1c;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 14px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card h2 {
  font-size: 16px;
}

.hint {
  color: #94a3b8;
  font-size: 12px;
  margin: 4px 0 16px;
}

.badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 999px;
}

.badge.ok {
  background: #dcfce7;
  color: #166534;
}

.badge.bad {
  background: #fef3c7;
  color: #92400e;
}

label {
  display: block;
  font-size: 13px;
  color: #475569;
  margin-bottom: 12px;
}

.url-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.url-toggle {
  display: flex;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  overflow: hidden;
}

.url-toggle button {
  flex: 1;
  padding: 6px 0;
  font-size: 13px;
  background: #f8fafc;
  color: #64748b;
  border: none;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.url-toggle button.active {
  background: #2563eb;
  color: #fff;
}

.url-row input[type="text"] {
  display: block;
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.actions button {
  flex: 1;
  padding: 9px 0;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.actions button.ghost {
  background: #fff;
  color: #2563eb;
  border: 1px solid #2563eb;
}

.actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.result {
  margin-top: 10px;
  font-size: 13px;
  color: #166534;
}
</style>
