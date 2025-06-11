<template>
  <div class="p-6 max-w-screen-md mx-auto">
    <div class="mb-6">
      <h2 class="text-2xl font-bold mb-4">비디오 스크립트 생성</h2>
      <div class="card">
        <div class="field mb-4">
          <label class="block mb-2">URL</label>
          <InputText id="url" v-model="url" class="w-full" placeholder="콘텐츠 URL을 입력하세요" type="url" />
        </div>

        <div class="field mb-4">
          <label class="block mb-2">영상 길이 (초)</label>
          <InputNumber id="duration" v-model="duration" class="w-full" :min="1" :max="60"
            placeholder="영상 길이를 초 단위로 입력하세요" />
        </div>

        <div class="flex justify-end">
          <Button label="스크립트 생성" icon="pi pi-check" :loading="shortsStore.isLoading" :disabled="!isValid"
            @click="generateScript" />
        </div>
      </div>
    </div>

    <div v-if="shortsStore.error" class="mt-4 p-4 bg-red-100 text-red-700 rounded">
      {{ shortsStore.error }}
    </div>
  </div>
</template>

<script setup lang="ts">
const shortsStore = useShortsStore()
const url = ref('')
const duration = ref(30)

const isValid = computed(() => {
  return url.value && duration.value && duration.value > 0 && duration.value <= 60
})

const generateScript = async () => {
  if (!isValid.value) return
  await shortsStore.generateScript(url.value, duration.value)
}
</script>